import React, { useEffect, useMemo, useState } from 'react';

import {
  createGrowthRecord,
  createStock,
  deleteGrowthRecord,
  deleteStock,
  getPondStocks,
  getPonds,
  updateGrowthRecord,
  updateStock,
} from '../../lib/api';

import './StockGrowthManagement.css';

const STOCK_STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'partial_harvest', label: 'Partial harvest' },
  { value: 'harvested', label: 'Harvested' },
];

function today() {
  return new Date().toISOString().slice(0, 10);
}

function emptyStockForm() {
  return {
    species: '',
    batch_name: '',
    stocking_date: today(),
    initial_quantity: '',
    current_quantity: '',
    initial_average_weight_g: '',
    status: 'active',
    notes: '',
  };
}

function emptyGrowthForm() {
  return {
    recorded_date: today(),
    sample_count: '',
    average_weight_g: '',
    average_length_cm: '',
    mortality_count: '0',
    feed_used_kg: '',
    notes: '',
  };
}

function formatNumber(value, suffix = '') {
  if (value === null || value === undefined || value === '') {
    return '-';
  }

  return `${Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })}${suffix}`;
}

function formatDate(value) {
  if (!value) {
    return '-';
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function getGrowthStatus(analysis) {
  if (!analysis || analysis.growth_records_count === 0) {
    return 'No growth records yet';
  }

  if (analysis.daily_growth_rate_g === null) {
    return 'First growth record added';
  }

  if (analysis.daily_growth_rate_g > 0) {
    return `${formatNumber(analysis.daily_growth_rate_g, ' g/day')}`;
  }

  return 'Growth needs attention';
}

function getDateValue(value) {
  return new Date(`${value}T00:00:00`).getTime();
}

function buildGrowthEntries(stock) {
  const entries = [
    {
      date: stock.stocking_date,
      label: 'Initial',
      weight: Number(stock.initial_average_weight_g || 0),
    },
    ...(stock.growth_records || []).map(record => ({
      date: record.recorded_date,
      label: formatDate(record.recorded_date),
      weight: Number(record.average_weight_g || 0),
    })),
  ];

  return entries
    .filter(entry => entry.date && entry.weight > 0)
    .sort((a, b) => getDateValue(a.date) - getDateValue(b.date));
}

function GrowthTrendChart({ stock }) {
  const entries = buildGrowthEntries(stock);
  const latestEntry = entries.at(-1);
  const firstEntry = entries[0];
  const hasGrowthRecords = (stock.growth_records || []).length > 0;

  if (entries.length === 0) {
    return (
      <div className="dp-growth-chart dp-growth-chart-empty dp-fade-in">
        <div className="dp-growth-chart-copy">
          <span>Weight trend</span>
          <strong>No weight data yet</strong>
        </div>
      </div>
    );
  }

  const chart = {
    width: 460,
    height: 210,
    left: 48,
    right: 18,
    top: 22,
    bottom: 44,
  };
  const plotWidth = chart.width - chart.left - chart.right;
  const plotHeight = chart.height - chart.top - chart.bottom;
  const weights = entries.map(entry => entry.weight);
  const minWeight = Math.min(...weights);
  const maxWeight = Math.max(...weights);
  const weightRange = Math.max(maxWeight - minWeight, 1);
  const yMin = Math.max(0, minWeight - Math.max(weightRange * 0.18, 1));
  const yMax = maxWeight + Math.max(weightRange * 0.18, 1);
  const minTime = Math.min(...entries.map(entry => getDateValue(entry.date)));
  const maxTime = Math.max(...entries.map(entry => getDateValue(entry.date)));
  const timeRange = Math.max(maxTime - minTime, 1);

  function xFor(entry) {
    if (entries.length === 1) {
      return chart.left + plotWidth / 2;
    }

    return chart.left + ((getDateValue(entry.date) - minTime) / timeRange) * plotWidth;
  }

  function yFor(entry) {
    return chart.top + ((yMax - entry.weight) / (yMax - yMin)) * plotHeight;
  }

  const points = entries.map(entry => `${xFor(entry)},${yFor(entry)}`).join(' ');
  const areaPoints = `${chart.left},${chart.top + plotHeight} ${points} ${chart.left + plotWidth},${chart.top + plotHeight}`;
  const startWeight = Number(firstEntry?.weight || 0);
  const latestWeight = Number(latestEntry?.weight || 0);
  const gain = latestWeight - startWeight;

  return (
    <div className="dp-growth-chart dp-fade-in">
      <div className="dp-growth-chart-copy">
        <span>Weight trend</span>
        <strong>{formatNumber(startWeight, ' g')} to {formatNumber(latestWeight, ' g')}</strong>
        <small>{hasGrowthRecords ? `${formatNumber(gain, ' g')} total gain` : 'Add growth records to extend the trend'}</small>
      </div>

      <svg
        className="dp-growth-chart-svg"
        viewBox={`0 0 ${chart.width} ${chart.height}`}
        role="img"
        aria-label={`${stock.batch_name} average weight growth trend`}
      >
        <line x1={chart.left} y1={chart.top} x2={chart.left} y2={chart.top + plotHeight} />
        <line x1={chart.left} y1={chart.top + plotHeight} x2={chart.left + plotWidth} y2={chart.top + plotHeight} />
        <line className="dp-chart-grid" x1={chart.left} y1={chart.top + plotHeight / 2} x2={chart.left + plotWidth} y2={chart.top + plotHeight / 2} />
        <text x={chart.left - 10} y={chart.top + 4} textAnchor="end">{formatNumber(yMax, 'g')}</text>
        <text x={chart.left - 10} y={chart.top + plotHeight + 4} textAnchor="end">{formatNumber(yMin, 'g')}</text>
        <text x={chart.left} y={chart.height - 12}>{formatDate(firstEntry.date)}</text>
        <text x={chart.left + plotWidth} y={chart.height - 12} textAnchor="end">{formatDate(latestEntry.date)}</text>
        {entries.length > 1 && <polygon className="dp-chart-area" points={areaPoints} />}
        {entries.length > 1 && <polyline className="dp-chart-line dp-chart-line-animated" points={points} />}
        {entries.map((entry, index) => (
          <g key={`${entry.date}-${index}`}>
            <circle
              className={index === entries.length - 1 ? 'dp-chart-point dp-chart-point-latest' : 'dp-chart-point'}
              cx={xFor(entry)}
              cy={yFor(entry)}
              r={index === entries.length - 1 ? 5 : 4}
              style={{ animationDelay: `${index * 60}ms` }}
            />
            <title>{entry.label}: {formatNumber(entry.weight, ' g')}</title>
          </g>
        ))}
      </svg>
    </div>
  );
}

export function StockGrowthManagement() {
  const [ponds, setPonds] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState(null);
  const [stocks, setStocks] = useState([]);
  const [stockForm, setStockForm] = useState(emptyStockForm);
  const [growthForm, setGrowthForm] = useState(emptyGrowthForm);
  const [editingStockId, setEditingStockId] = useState(null);
  const [editingGrowthId, setEditingGrowthId] = useState(null);
  const [growthFormStockId, setGrowthFormStockId] = useState(null);
  const [isStockFormOpen, setIsStockFormOpen] = useState(false);
  const [isLoadingPonds, setIsLoadingPonds] = useState(true);
  const [isLoadingStocks, setIsLoadingStocks] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');

  const selectedPond = useMemo(
    () => ponds.find(pond => pond.id === selectedPondId) || null,
    [ponds, selectedPondId],
  );

  const stockSummary = useMemo(() => {
    return stocks.reduce(
      (summary, stock) => ({
        batches: summary.batches + 1,
        fish: summary.fish + Number(stock.current_quantity || 0),
        biomass: summary.biomass + Number(stock.growth_analysis?.estimated_biomass_kg || 0),
      }),
      { batches: 0, fish: 0, biomass: 0 },
    );
  }, [stocks]);

  useEffect(() => {
    let isMounted = true;

    async function loadPonds() {
      setIsLoadingPonds(true);
      setError('');

      try {
        const data = await getPonds();
        if (isMounted) {
          setPonds(data || []);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message);
        }
      } finally {
        if (isMounted) {
          setIsLoadingPonds(false);
        }
      }
    }

    loadPonds();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedPondId) {
      return;
    }

    let isMounted = true;

    async function loadStocks() {
      setIsLoadingStocks(true);
      setError('');

      try {
        const data = await getPondStocks(selectedPondId);
        if (isMounted) {
          setStocks(data || []);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message);
        }
      } finally {
        if (isMounted) {
          setIsLoadingStocks(false);
        }
      }
    }

    loadStocks();

    return () => {
      isMounted = false;
    };
  }, [selectedPondId]);

  async function reloadStocks() {
    if (!selectedPondId) {
      return;
    }

    const data = await getPondStocks(selectedPondId);
    setStocks(data || []);
  }

  function selectPond(pondId) {
    setSelectedPondId(pondId);
    closeStockForm();
    closeGrowthForm();
  }

  function openCreateStockForm() {
    setEditingStockId(null);
    setStockForm(emptyStockForm());
    setFormError('');
    setIsStockFormOpen(true);
  }

  function openEditStockForm(stock) {
    setEditingStockId(stock.id);
    setStockForm({
      species: stock.species || '',
      batch_name: stock.batch_name || '',
      stocking_date: stock.stocking_date || today(),
      initial_quantity: stock.initial_quantity || '',
      current_quantity: stock.current_quantity || '',
      initial_average_weight_g: stock.initial_average_weight_g || '',
      status: stock.status || 'active',
      notes: stock.notes || '',
    });
    setFormError('');
    setIsStockFormOpen(true);
  }

  function closeStockForm() {
    setEditingStockId(null);
    setStockForm(emptyStockForm());
    setFormError('');
    setIsStockFormOpen(false);
  }

  function openCreateGrowthForm(stockId) {
    setEditingGrowthId(null);
    setGrowthFormStockId(stockId);
    setGrowthForm(emptyGrowthForm());
    setFormError('');
  }

  function openEditGrowthForm(stockId, record) {
    setEditingGrowthId(record.id);
    setGrowthFormStockId(stockId);
    setGrowthForm({
      recorded_date: record.recorded_date || today(),
      sample_count: record.sample_count || '',
      average_weight_g: record.average_weight_g || '',
      average_length_cm: record.average_length_cm || '',
      mortality_count: record.mortality_count ?? '0',
      feed_used_kg: record.feed_used_kg || '',
      notes: record.notes || '',
    });
    setFormError('');
  }

  function closeGrowthForm() {
    setEditingGrowthId(null);
    setGrowthFormStockId(null);
    setGrowthForm(emptyGrowthForm());
    setFormError('');
  }

  function handleStockChange(event) {
    const { name, value } = event.target;
    setStockForm(current => ({
      ...current,
      [name]: value,
    }));
  }

  function handleGrowthChange(event) {
    const { name, value } = event.target;
    setGrowthForm(current => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleStockSubmit(event) {
    event.preventDefault();
    if (!selectedPondId) {
      return;
    }

    setIsSaving(true);
    setFormError('');

    try {
      const payload = {
        ...stockForm,
        initial_quantity: Number(stockForm.initial_quantity),
        current_quantity: Number(stockForm.current_quantity),
        initial_average_weight_g: stockForm.initial_average_weight_g,
      };

      if (editingStockId) {
        await updateStock(editingStockId, payload);
      } else {
        await createStock(selectedPondId, payload);
      }

      await reloadStocks();
      closeStockForm();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleGrowthSubmit(event) {
    event.preventDefault();
    if (!growthFormStockId) {
      return;
    }

    setIsSaving(true);
    setFormError('');

    try {
      const payload = {
        ...growthForm,
        sample_count: Number(growthForm.sample_count),
        average_length_cm: growthForm.average_length_cm || null,
        mortality_count: Number(growthForm.mortality_count || 0),
        feed_used_kg: growthForm.feed_used_kg || null,
      };

      if (editingGrowthId) {
        await updateGrowthRecord(editingGrowthId, payload);
      } else {
        await createGrowthRecord(growthFormStockId, payload);
      }

      await reloadStocks();
      closeGrowthForm();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteStock(stock) {
    const shouldDelete = window.confirm(`Delete stock batch ${stock.batch_name}?`);
    if (!shouldDelete) {
      return;
    }

    try {
      await deleteStock(stock.id);
      await reloadStocks();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteGrowth(record) {
    const shouldDelete = window.confirm(`Delete growth record from ${formatDate(record.recorded_date)}?`);
    if (!shouldDelete) {
      return;
    }

    try {
      await deleteGrowthRecord(record.id);
      await reloadStocks();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="dp-management dp-stock-growth" aria-labelledby="stock-growth-title">
      <div className="dp-management-header dp-fade-in">
        <div>
          <p className="dp-section-kicker">Stock & Growth</p>
          <h1 id="stock-growth-title">Stock and Growth Analysis</h1>
        </div>
        {selectedPond && (
          <button
            type="button"
            className="dp-btn-primary dp-btn-animated"
            onClick={isStockFormOpen ? closeStockForm : openCreateStockForm}
          >
            {isStockFormOpen ? 'Close form' : 'Add stock'}
          </button>
        )}
      </div>

      {error && <div className="dp-inline-error dp-shake">{error}</div>}

      <div className="dp-pond-picker" aria-label="Select pond for stock and growth">
        {isLoadingPonds ? (
          <div className="dp-table-state dp-pulse">Loading ponds...</div>
        ) : ponds.length === 0 ? (
          <div className="dp-table-state">No ponds recorded yet.</div>
        ) : (
          ponds.map((pond, index) => (
            <button
              key={pond.id}
              type="button"
              className={`dp-pond-option dp-btn-animated dp-pop-in ${selectedPondId === pond.id ? 'active' : ''}`}
              style={{ animationDelay: `${index * 45}ms` }}
              onClick={() => selectPond(pond.id)}
            >
              <strong>{pond.name}</strong>
              <span>{pond.location}</span>
              <small>{formatNumber(pond.stocking_capacity)} capacity</small>
            </button>
          ))
        )}
      </div>

      {!selectedPond ? (
        <div className="dp-empty-panel dp-fade-in">Select a pond to view its stock batches and growth records.</div>
      ) : (
        <>
          <div className="dp-metric-row dp-fade-in-up" aria-label="Stock summary">
            <div className="dp-metric">
              <span>Selected pond</span>
              <strong>{selectedPond.name}</strong>
            </div>
            <div className="dp-metric">
              <span>Stock batches</span>
              <strong>{stockSummary.batches}</strong>
            </div>
            <div className="dp-metric">
              <span>Current fish</span>
              <strong>{formatNumber(stockSummary.fish)}</strong>
            </div>
          </div>

          <div className="dp-metric-row dp-metric-row-secondary dp-fade-in-up" aria-label="Growth summary">
            <div className="dp-metric">
              <span>Estimated biomass</span>
              <strong>{formatNumber(stockSummary.biomass, ' kg')}</strong>
            </div>
            <div className="dp-metric">
              <span>Pond capacity</span>
              <strong>{formatNumber(selectedPond.stocking_capacity)}</strong>
            </div>
            <div className="dp-metric">
              <span>Available capacity</span>
              <strong>{formatNumber(Number(selectedPond.stocking_capacity || 0) - stockSummary.fish)}</strong>
            </div>
          </div>

          <div className={`dp-collapsible ${isStockFormOpen ? 'dp-collapsible-open' : ''}`}>
            <form className="dp-pond-form" onSubmit={handleStockSubmit}>
              <div className="dp-form-grid">
                <label>
                  <span>Fish species</span>
                  <input
                    name="species"
                    value={stockForm.species}
                    onChange={handleStockChange}
                    placeholder="Rohu"
                    required
                  />
                </label>

                <label>
                  <span>Batch name</span>
                  <input
                    name="batch_name"
                    value={stockForm.batch_name}
                    onChange={handleStockChange}
                    placeholder="Rohu batch A"
                    required
                  />
                </label>

                <label>
                  <span>Stocking date</span>
                  <input
                    name="stocking_date"
                    type="date"
                    value={stockForm.stocking_date}
                    onChange={handleStockChange}
                    required
                  />
                </label>

                <label>
                  <span>Initial quantity</span>
                  <input
                    name="initial_quantity"
                    type="number"
                    min="1"
                    step="1"
                    value={stockForm.initial_quantity}
                    onChange={handleStockChange}
                    required
                  />
                </label>

                <label>
                  <span>Current quantity</span>
                  <input
                    name="current_quantity"
                    type="number"
                    min="0"
                    step="1"
                    value={stockForm.current_quantity}
                    onChange={handleStockChange}
                    required
                  />
                </label>

                <label>
                  <span>Initial avg weight (g)</span>
                  <input
                    name="initial_average_weight_g"
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={stockForm.initial_average_weight_g}
                    onChange={handleStockChange}
                    required
                  />
                </label>

                <label>
                  <span>Status</span>
                  <select name="status" value={stockForm.status} onChange={handleStockChange}>
                    {STOCK_STATUS_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>

                <label className="dp-form-notes">
                  <span>Notes</span>
                  <textarea
                    name="notes"
                    value={stockForm.notes}
                    onChange={handleStockChange}
                    rows="3"
                    placeholder="Optional stock details"
                  />
                </label>
              </div>

              {formError && <div className="dp-inline-error dp-shake">{formError}</div>}

              <div className="dp-form-actions">
                <button type="button" className="dp-btn-secondary dp-btn-animated" onClick={closeStockForm}>
                  Cancel
                </button>
                <button type="submit" className="dp-btn-primary dp-btn-animated" disabled={isSaving}>
                  {isSaving ? 'Saving...' : editingStockId ? 'Update stock' : 'Save stock'}
                </button>
              </div>
            </form>
          </div>

          {isLoadingStocks ? (
            <div className="dp-table-state dp-pulse">Loading stock batches...</div>
          ) : stocks.length === 0 ? (
            <div className="dp-empty-panel dp-fade-in">No stock batches recorded for this pond yet.</div>
          ) : (
            <div className="dp-stock-list">
              {stocks.map((stock, index) => (
                <article
                  className="dp-stock-card dp-fade-in-up"
                  key={stock.id}
                  style={{ animationDelay: `${index * 70}ms` }}
                >
                  <div className="dp-stock-card-header">
                    <div>
                      <p className="dp-section-kicker">{stock.species}</p>
                      <h2>{stock.batch_name}</h2>
                      <span>{formatDate(stock.stocking_date)} stocking date</span>
                    </div>
                    <div className="dp-stock-actions">
                      <button
                        type="button"
                        className="dp-table-action dp-btn-animated"
                        onClick={() => openEditStockForm(stock)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="dp-table-action dp-table-action-danger dp-btn-animated"
                        onClick={() => handleDeleteStock(stock)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="dp-growth-insights">
                    <div>
                      <span>Current fish</span>
                      <strong>{formatNumber(stock.current_quantity)}</strong>
                    </div>
                    <div>
                      <span>Latest avg weight</span>
                      <strong>{formatNumber(stock.growth_analysis?.latest_average_weight_g, ' g')}</strong>
                    </div>
                    <div>
                      <span>Daily growth</span>
                      <strong>{getGrowthStatus(stock.growth_analysis)}</strong>
                    </div>
                    <div>
                      <span>Survival</span>
                      <strong>{formatNumber(stock.growth_analysis?.survival_rate_percent, '%')}</strong>
                    </div>
                    <div>
                      <span>FCR</span>
                      <strong>{formatNumber(stock.growth_analysis?.feed_conversion_ratio)}</strong>
                    </div>
                  </div>

                  <GrowthTrendChart stock={stock} />

                  {stock.notes && <p className="dp-stock-note">{stock.notes}</p>}

                  <div className="dp-growth-toolbar">
                    <h3>Growth records</h3>
                    <button
                      type="button"
                      className="dp-btn-secondary dp-btn-animated"
                      onClick={() => openCreateGrowthForm(stock.id)}
                    >
                      Add growth
                    </button>
                  </div>

                  <div className={`dp-collapsible ${growthFormStockId === stock.id ? 'dp-collapsible-open' : ''}`}>
                    <form className="dp-growth-form" onSubmit={handleGrowthSubmit}>
                      <div className="dp-form-grid">
                        <label>
                          <span>Record date</span>
                          <input
                            name="recorded_date"
                            type="date"
                            value={growthForm.recorded_date}
                            onChange={handleGrowthChange}
                            required
                          />
                        </label>

                        <label>
                          <span>Sample count</span>
                          <input
                            name="sample_count"
                            type="number"
                            min="1"
                            step="1"
                            value={growthForm.sample_count}
                            onChange={handleGrowthChange}
                            required
                          />
                        </label>

                        <label>
                          <span>Avg weight (g)</span>
                          <input
                            name="average_weight_g"
                            type="number"
                            min="0.01"
                            step="0.01"
                            value={growthForm.average_weight_g}
                            onChange={handleGrowthChange}
                            required
                          />
                        </label>

                        <label>
                          <span>Avg length (cm)</span>
                          <input
                            name="average_length_cm"
                            type="number"
                            min="0.01"
                            step="0.01"
                            value={growthForm.average_length_cm}
                            onChange={handleGrowthChange}
                          />
                        </label>

                        <label>
                          <span>Mortality count</span>
                          <input
                            name="mortality_count"
                            type="number"
                            min="0"
                            step="1"
                            value={growthForm.mortality_count}
                            onChange={handleGrowthChange}
                          />
                        </label>

                        <label>
                          <span>Feed used (kg)</span>
                          <input
                            name="feed_used_kg"
                            type="number"
                            min="0.01"
                            step="0.01"
                            value={growthForm.feed_used_kg}
                            onChange={handleGrowthChange}
                          />
                        </label>

                        <label className="dp-form-notes">
                          <span>Notes</span>
                          <textarea
                            name="notes"
                            value={growthForm.notes}
                            onChange={handleGrowthChange}
                            rows="3"
                            placeholder="Optional growth notes"
                          />
                        </label>
                      </div>

                      {formError && <div className="dp-inline-error dp-shake">{formError}</div>}

                      <div className="dp-form-actions">
                        <button type="button" className="dp-btn-secondary dp-btn-animated" onClick={closeGrowthForm}>
                          Cancel
                        </button>
                        <button type="submit" className="dp-btn-primary dp-btn-animated" disabled={isSaving}>
                          {isSaving ? 'Saving...' : editingGrowthId ? 'Update growth' : 'Save growth'}
                        </button>
                      </div>
                    </form>
                  </div>

                  <div className="dp-table-wrap dp-growth-table-wrap">
                    {stock.growth_records.length === 0 ? (
                      <div className="dp-table-state">No growth records for this stock yet.</div>
                    ) : (
                      <table className="dp-data-table dp-growth-table">
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Sample</th>
                            <th>Weight</th>
                            <th>Length</th>
                            <th>Mortality</th>
                            <th>Feed</th>
                            <th aria-label="Actions" />
                          </tr>
                        </thead>
                        <tbody>
                          {stock.growth_records.map(record => (
                            <tr key={record.id} className="dp-row-fade-in">
                              <td>
                                <strong>{formatDate(record.recorded_date)}</strong>
                                {record.notes && <span>{record.notes}</span>}
                              </td>
                              <td>{formatNumber(record.sample_count)}</td>
                              <td>{formatNumber(record.average_weight_g, ' g')}</td>
                              <td>{formatNumber(record.average_length_cm, ' cm')}</td>
                              <td>{formatNumber(record.mortality_count)}</td>
                              <td>{formatNumber(record.feed_used_kg, ' kg')}</td>
                              <td>
                                <button
                                  type="button"
                                  className="dp-table-action dp-btn-animated"
                                  onClick={() => openEditGrowthForm(stock.id, record)}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="dp-table-action dp-table-action-danger dp-btn-animated"
                                  onClick={() => handleDeleteGrowth(record)}
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
