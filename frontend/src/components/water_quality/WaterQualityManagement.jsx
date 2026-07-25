import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  compareWaterQualityPonds,
  createWaterQualityReading,
  getPonds,
  getWaterQualityDashboard,
  getWaterQualityGraph,
  getWaterQualityHistory,
  getWaterQualityReadings,
} from '../../lib/api';
import './WaterQualityManagement.css';

const TABS = [
  'Dashboard',
  'Add Reading',
  'History',
  'Comparison',
  'AI Advisor',
];

const PERIODS = ['daily', 'weekly', 'monthly', 'yearly'];
const STATUS_OPTIONS = ['', 'Good', 'Warning', 'Danger'];

const PARAMETERS = [
  { key: 'temperature', label: 'Temperature', unit: '°C' },
  { key: 'ph', label: 'pH', unit: '' },
  { key: 'dissolved_oxygen', label: 'DO', unit: 'mg/L' },
  { key: 'ammonia', label: 'Ammonia', unit: 'mg/L' },
  { key: 'nitrite', label: 'Nitrite', unit: 'mg/L' },
  { key: 'nitrate', label: 'Nitrate', unit: 'mg/L' },
  { key: 'turbidity', label: 'Turbidity', unit: 'NTU' },
  { key: 'salinity', label: 'Salinity', unit: 'ppt' },
  { key: 'water_level', label: 'Water Level', unit: 'ft' },
];

const EMPTY_READING = {
  temperature: '',
  ph: '',
  dissolved_oxygen: '',
  ammonia: '',
  nitrite: '',
  nitrate: '',
  turbidity: '',
  salinity: '',
  water_level: '',
};

function formatDate(value) {
  if (!value) return 'No update';

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function formatValue(value, unit = '') {
  if (value === null || value === undefined || value === '') return '—';
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}${unit ? ` ${unit}` : ''}`;
}

function statusClass(status) {
  return String(status || 'empty').toLowerCase();
}

function getRiskCards(dashboard) {
  return (dashboard?.parameter_cards || []).filter(card => card.status !== 'Good');
}

export function TrendArrow({ value }) {
  return <span className={`wqm-trend wqm-trend-${value === '↑' ? 'up' : value === '↓' ? 'down' : 'flat'}`}>{value || '→'}</span>;
}

function StatusPill({ status }) {
  return <span className={`wqm-status wqm-status-${statusClass(status)}`}>{status || 'No Data'}</span>;
}

function PanelState({ type = 'empty', children }) {
  return <div className={`wqm-state wqm-state-${type}`}>{children}</div>;
}

export function DashboardCards({ dashboard, loading, error }) {
  if (loading) return <PanelState>Loading water quality dashboard...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;
  if (!dashboard?.parameter_cards?.length) return <PanelState>No water quality readings yet.</PanelState>;

  return (
    <>
      <div className="wqm-overview">
        <div>
          <span>Overall Status</span>
          <strong>{dashboard.overall_status}</strong>
        </div>
        <div>
          <span>Good</span>
          <strong>{dashboard.good_count}</strong>
        </div>
        <div>
          <span>Warning</span>
          <strong>{dashboard.warning_count}</strong>
        </div>
        <div>
          <span>Danger</span>
          <strong>{dashboard.danger_count}</strong>
        </div>
      </div>

      <div className="wqm-card-grid">
        {dashboard.parameter_cards.map(card => (
          <article key={card.parameter} className={`wqm-card wqm-card-${statusClass(card.status)}`}>
            <div className="wqm-card-top">
              <span>{labelFor(card.parameter)}</span>
              <StatusPill status={card.status} />
            </div>
            <strong>{formatValue(card.current_value, unitFor(card.parameter))}</strong>
            <dl>
              <div>
                <dt>Normal range</dt>
                <dd>{card.normal_range}</dd>
              </div>
              <div>
                <dt>Trend</dt>
                <dd><TrendArrow value={card.trend} /></dd>
              </div>
              <div>
                <dt>Last updated</dt>
                <dd>{formatDate(card.last_updated)}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </>
  );
}

export function WaterQualityForm({ ponds, selectedPondId, onSaved }) {
  const [formData, setFormData] = useState(EMPTY_READING);
  const [pondId, setPondId] = useState(selectedPondId || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');

    try {
      const payload = {
        pond: Number(pondId),
        ...Object.fromEntries(
          Object.entries(formData).map(([key, value]) => [
            key,
            key === 'salinity' && value === '' ? null : Number(value),
          ]),
        ),
      };

      await createWaterQualityReading(payload);
      setFormData(EMPTY_READING);
      onSaved?.(String(pondId));
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="wqm-form" onSubmit={handleSubmit}>
      <label className="wqm-field">
        <span>Pond</span>
        <select value={pondId} onChange={event => setPondId(event.target.value)} required>
          <option value="">Select pond</option>
          {ponds.map(pond => <option key={pond.id} value={pond.id}>{pond.name}</option>)}
        </select>
      </label>

      <div className="wqm-form-grid">
        {PARAMETERS.map(parameter => (
          <label key={parameter.key} className="wqm-field">
            <span>{parameter.label}{parameter.unit ? ` (${parameter.unit})` : ''}</span>
            <input
              name={parameter.key}
              type="number"
              step="0.01"
              min="0"
              max={parameter.key === 'ph' ? '14' : undefined}
              value={formData[parameter.key]}
              onChange={handleChange}
              required={parameter.key !== 'salinity'}
            />
          </label>
        ))}
      </div>

      {error && <PanelState type="error">{error}</PanelState>}

      <div className="wqm-actions">
        <button type="button" className="wqm-btn wqm-btn-secondary" onClick={() => setFormData(EMPTY_READING)}>
          Clear
        </button>
        <button type="submit" className="wqm-btn wqm-btn-primary" disabled={saving || !pondId}>
          {saving ? 'Saving...' : 'Save Reading'}
        </button>
      </div>
    </form>
  );
}

export function HistoricalGraph({ data, parameterKey, onParameterChange, loading, error }) {
  const parameter = PARAMETERS.find(item => item.key === parameterKey) || PARAMETERS[0];
  const chart = useMemo(() => buildChart(data, parameterKey), [data, parameterKey]);

  if (loading) return <PanelState>Loading graph...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;
  if (!data.length) return <PanelState>No graph data for the selected filters.</PanelState>;

  return (
    <section className="wqm-panel">
      <div className="wqm-panel-header">
        <div>
          <span>Chart</span>
          <h2>{parameter.label}</h2>
        </div>
        <select value={parameterKey} onChange={event => onParameterChange(event.target.value)}>
          {PARAMETERS.map(item => <option key={item.key} value={item.key}>{item.label}</option>)}
        </select>
      </div>
      <svg className="wqm-chart" viewBox="0 0 640 240" role="img" aria-label={`${parameter.label} historical chart`}>
        <line x1="34" y1="206" x2="606" y2="206" />
        <line x1="34" y1="28" x2="34" y2="206" />
        <polyline points={chart.points} />
        {chart.pointList.map(point => <circle key={`${point.x}-${point.y}`} cx={point.x} cy={point.y} r="4" />)}
      </svg>
      <div className="wqm-chart-meta">
        <span>Min {formatValue(chart.min, parameter.unit)}</span>
        <span>Max {formatValue(chart.max, parameter.unit)}</span>
        <span>{data.length} periods</span>
      </div>
    </section>
  );
}

export function HistoryTable({ readings, loading, error }) {
  if (loading) return <PanelState>Loading reading history...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;
  if (!readings.length) return <PanelState>No readings match the selected filters.</PanelState>;

  return (
    <div className="wqm-table-wrap">
      <table className="wqm-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Pond</th>
            {PARAMETERS.map(parameter => <th key={parameter.key}>{parameter.label}</th>)}
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {readings.map(reading => (
            <tr key={reading.id}>
              <td>{formatDate(reading.created_at)}</td>
              <td>{reading.pond_name}</td>
              {PARAMETERS.map(parameter => (
                <td key={parameter.key}>{formatValue(reading[parameter.key], parameter.unit)}</td>
              ))}
              <td><StatusPill status={reading.overall_status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PondComparison({ ponds, selectedIds, onSelectionChange, comparison, onCompare, loading, error }) {
  function togglePond(pondId) {
    const id = String(pondId);
    onSelectionChange(
      selectedIds.includes(id)
        ? selectedIds.filter(item => item !== id)
        : [...selectedIds, id],
    );
  }

  return (
    <section className="wqm-panel">
      <div className="wqm-panel-header">
        <div>
          <span>Compare</span>
          <h2>Pond Comparison</h2>
        </div>
        <button type="button" className="wqm-btn wqm-btn-primary" onClick={onCompare} disabled={selectedIds.length < 2 || loading}>
          {loading ? 'Comparing...' : 'Compare Ponds'}
        </button>
      </div>

      <div className="wqm-checkbox-grid">
        {ponds.map(pond => (
          <label key={pond.id} className="wqm-checkbox">
            <input type="checkbox" checked={selectedIds.includes(String(pond.id))} onChange={() => togglePond(pond.id)} />
            <span>{pond.name}</span>
          </label>
        ))}
      </div>

      {error && <PanelState type="error">{error}</PanelState>}

      {!comparison?.ponds?.length ? (
        <PanelState>Select at least two ponds to compare.</PanelState>
      ) : (
        <div className="wqm-comparison-grid">
          {comparison.ponds.map(item => (
            <article key={item.pond.id} className="wqm-compare-card">
              <div className="wqm-card-top">
                <span>Rank #{item.rank}</span>
                <StatusPill status={item.overall_status} />
              </div>
              <h3>{item.pond.name}</h3>
              <p>{item.danger_count} danger · {item.warning_count} warning · {item.good_count} good</p>
              <dl>
                <div><dt>Avg Temp</dt><dd>{formatValue(item.average_values.temperature, '°C')}</dd></div>
                <div><dt>Avg pH</dt><dd>{formatValue(item.average_values.ph)}</dd></div>
                <div><dt>Avg DO</dt><dd>{formatValue(item.average_values.dissolved_oxygen, 'mg/L')}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export function AIAdvicePanel({ dashboard }) {
  const risks = getRiskCards(dashboard);

  if (!dashboard) return <PanelState>Select a pond with readings to view recommendations.</PanelState>;
  if (!risks.length) {
    return (
      <section className="wqm-panel">
        <div className="wqm-panel-header"><div><span>AI Advisor</span><h2>Recommendations</h2></div></div>
        <PanelState type="success">All latest parameters are Good. Continue routine monitoring and record readings consistently.</PanelState>
      </section>
    );
  }

  return (
    <section className="wqm-advice-grid">
      {risks.map(card => (
        <article key={card.parameter} className={`wqm-advice-card wqm-card-${statusClass(card.status)}`}>
          <div className="wqm-card-top">
            <span>{labelFor(card.parameter)}</span>
            <StatusPill status={card.status} />
          </div>
          <p>{labelFor(card.parameter)} is {card.status.toLowerCase()} at {formatValue(card.current_value, unitFor(card.parameter))}. Normal range is {card.normal_range}.</p>
          <ul>
            <li>Retest this parameter before making major changes.</li>
            <li>Reduce feeding pressure and improve aeration when fish show stress.</li>
            {card.status === 'Danger' && <li>Prepare immediate corrective action and monitor fish behavior closely.</li>}
          </ul>
        </article>
      ))}
    </section>
  );
}

export default function WaterQualityManagement() {
  const [ponds, setPonds] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState('');
  const [period, setPeriod] = useState('daily');
  const [historyRows, setHistoryRows] = useState([]);
  const [graphRows, setGraphRows] = useState([]);
  const [readings, setReadings] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [tableFilters, setTableFilters] = useState({ date: '', status: '' });
  const [chartParameter, setChartParameter] = useState('temperature');
  const [compareIds, setCompareIds] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadPonds() {
      try {
        const data = await getPonds();
        if (!active) return;
        setPonds(data || []);
        const firstPondId = data?.[0]?.id ? String(data[0].id) : '';
        setSelectedPondId(firstPondId);
        setCompareIds((data || []).slice(0, 2).map(pond => String(pond.id)));
      } catch {
        if (active) setPonds([]);
      }
    }

    loadPonds();

    return () => {
      active = false;
    };
  }, []);

  const loadDashboard = useCallback(async (pondId = selectedPondId) => {
    if (!pondId) return;
    setDashboardLoading(true);
    setDashboardError('');

    try {
      const data = await getWaterQualityDashboard(pondId);
      setDashboard(data);
    } catch (err) {
      setDashboard(null);
      setDashboardError(err.message);
    } finally {
      setDashboardLoading(false);
    }
  }, [selectedPondId]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError('');

    try {
      const [history, graph, readingList] = await Promise.all([
        getWaterQualityHistory({ pond: selectedPondId, period }),
        getWaterQualityGraph({ pond: selectedPondId, period }),
        getWaterQualityReadings({
          pond: selectedPondId,
          date: tableFilters.date,
          status: tableFilters.status,
        }),
      ]);
      setHistoryRows(history.results || []);
      setGraphRows(graph.results || []);
      setReadings(readingList || []);
    } catch (err) {
      setHistoryRows([]);
      setGraphRows([]);
      setReadings([]);
      setHistoryError(err.message);
    } finally {
      setHistoryLoading(false);
    }
  }, [period, selectedPondId, tableFilters.date, tableFilters.status]);

  useEffect(() => {
    if (selectedPondId) loadDashboard(selectedPondId);
  }, [selectedPondId, loadDashboard]);

  useEffect(() => {
    if (activeTab === 'History' && selectedPondId) loadHistory();
  }, [activeTab, selectedPondId, loadHistory]);

  async function loadComparison() {
    setCompareLoading(true);
    setCompareError('');

    try {
      const data = await compareWaterQualityPonds(compareIds);
      setComparison(data);
    } catch (err) {
      setComparison(null);
      setCompareError(err.message);
    } finally {
      setCompareLoading(false);
    }
  }

  function handleSaved(pondId) {
    setSelectedPondId(pondId);
    setActiveTab('Dashboard');
    loadDashboard(pondId);
  }

  return (
    <section className="wqm-root" aria-labelledby="water-quality-title">
      <div className="wqm-header">
        <div>
          <span>Water Quality</span>
          <h1 id="water-quality-title">Water Quality Management</h1>
        </div>
        <label className="wqm-field wqm-pond-picker">
          <span>Pond</span>
          <select value={selectedPondId} onChange={event => setSelectedPondId(event.target.value)}>
            {ponds.length === 0 ? <option value="">No ponds</option> : ponds.map(pond => (
              <option key={pond.id} value={pond.id}>{pond.name}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="wqm-tabs" role="tablist" aria-label="Water quality views">
        {TABS.map(tab => (
          <button key={tab} type="button" className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {!ponds.length ? (
        <PanelState>Add a pond before recording water quality readings.</PanelState>
      ) : (
        <>
          {activeTab === 'Dashboard' && (
            <DashboardCards dashboard={dashboard} loading={dashboardLoading} error={dashboardError} />
          )}

          {activeTab === 'Add Reading' && (
            <WaterQualityForm key={selectedPondId} ponds={ponds} selectedPondId={selectedPondId} onSaved={handleSaved} />
          )}

          {activeTab === 'History' && (
            <div className="wqm-stack">
              <div className="wqm-filter-row">
                <label className="wqm-field">
                  <span>Period</span>
                  <select value={period} onChange={event => setPeriod(event.target.value)}>
                    {PERIODS.map(item => <option key={item} value={item}>{item}</option>)}
                  </select>
                </label>
                <label className="wqm-field">
                  <span>Date</span>
                  <input type="date" value={tableFilters.date} onChange={event => setTableFilters(current => ({ ...current, date: event.target.value }))} />
                </label>
                <label className="wqm-field">
                  <span>Status</span>
                  <select value={tableFilters.status} onChange={event => setTableFilters(current => ({ ...current, status: event.target.value }))}>
                    {STATUS_OPTIONS.map(item => <option key={item || 'all'} value={item}>{item || 'All'}</option>)}
                  </select>
                </label>
              </div>
              <HistoricalGraph data={graphRows.length ? graphRows : historyRows} parameterKey={chartParameter} onParameterChange={setChartParameter} loading={historyLoading} error={historyError} />
              <HistoryTable readings={readings} loading={historyLoading} error={historyError} />
            </div>
          )}

          {activeTab === 'Comparison' && (
            <PondComparison
              ponds={ponds}
              selectedIds={compareIds}
              onSelectionChange={setCompareIds}
              comparison={comparison}
              onCompare={loadComparison}
              loading={compareLoading}
              error={compareError}
            />
          )}

          {activeTab === 'AI Advisor' && <AIAdvicePanel dashboard={dashboard} />}
        </>
      )}
    </section>
  );
}

function labelFor(key) {
  return PARAMETERS.find(parameter => parameter.key === key)?.label || key;
}

function unitFor(key) {
  return PARAMETERS.find(parameter => parameter.key === key)?.unit || '';
}

function buildChart(rows, key) {
  const values = rows
    .map((row, index) => ({ index, value: row[key] }))
    .filter(point => point.value !== null && point.value !== undefined);

  if (!values.length) {
    return { points: '', pointList: [], min: null, max: null };
  }

  const min = Math.min(...values.map(point => Number(point.value)));
  const max = Math.max(...values.map(point => Number(point.value)));
  const spread = max - min || 1;
  const width = 640;
  const height = 240;
  const pad = 34;
  const step = values.length > 1 ? (width - pad * 2) / (values.length - 1) : 0;
  const pointList = values.map((point, index) => {
    const x = values.length > 1 ? pad + step * index : width / 2;
    const y = height - pad - ((Number(point.value) - min) / spread) * (height - pad * 2);
    return { x, y };
  });

  return {
    points: pointList.map(point => `${point.x},${point.y}`).join(' '),
    pointList,
    min,
    max,
  };
}
