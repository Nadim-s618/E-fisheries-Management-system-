import { useCallback, useEffect, useMemo, useState } from 'react';

import { getMarketAnalysisDashboard } from '../../lib/api';
import './MarketAnalysis.css';

function formatPrice(value) {
  if (value === null || value === undefined) return 'BDT --';
  return `BDT ${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function formatPercent(value) {
  const number = Number(value || 0);
  return `${Math.abs(number).toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
}

function formatDate(value, options = { month: 'short', day: 'numeric' }) {
  if (!value) return '--';
  return new Intl.DateTimeFormat(undefined, options).format(new Date(`${value}T00:00:00`));
}

function directionLabel(direction) {
  if (direction === 'up') return 'Increase';
  if (direction === 'down') return 'Decrease';
  return 'No change';
}

function DirectionArrow({ direction }) {
  const symbol = direction === 'up' ? '\u2191' : direction === 'down' ? '\u2193' : '\u2192';

  return (
    <span className={`ma-arrow ma-arrow-${direction}`} aria-label={directionLabel(direction)}>
      <span aria-hidden="true">{symbol}</span>
    </span>
  );
}

function DemandBadge({ value }) {
  return <span className={`ma-demand ma-demand-${String(value).toLowerCase()}`}>{value}</span>;
}

function SummaryCard({ label, value, tone = 'green' }) {
  return (
    <article className={`ma-summary-card ma-summary-card-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function PanelState({ type = 'empty', children }) {
  return <div className={`ma-state ma-state-${type}`}>{children}</div>;
}

function SeriesPanel({ title, items, valueKey }) {
  return (
    <section className="ma-panel">
      <div className="ma-panel-title">
        <span>{title}</span>
      </div>
      <div className="ma-series">
        {(items || []).map(item => (
          <article key={item.date} className="ma-series-item">
            <span>{formatDate(item.date)}</span>
            <strong>{formatPrice(item[valueKey])}</strong>
            {item.demand_level && <small>{item.demand_level}</small>}
          </article>
        ))}
      </div>
    </section>
  );
}

function MarketTable({ records, selectedKey, onSelect }) {
  return (
    <div className="ma-table-wrap">
      <table className="ma-table">
        <thead>
          <tr>
            <th>Fish</th>
            <th>Division</th>
            <th>Today</th>
            <th>Yesterday</th>
            <th>Change</th>
            <th>Demand</th>
          </tr>
        </thead>
        <tbody>
          {records.map(record => {
            const key = `${record.fish_name}-${record.division}`;
            return (
              <tr
                key={key}
                className={selectedKey === key ? 'selected' : ''}
                onClick={() => onSelect(key)}
              >
                <td>
                  <button type="button" className="ma-row-button" onClick={() => onSelect(key)}>
                    {record.fish_name}
                  </button>
                </td>
                <td>{record.division}</td>
                <td>{formatPrice(record.today_price)}</td>
                <td>{formatPrice(record.yesterday_price)}</td>
                <td>
                  <span className="ma-change">
                    <DirectionArrow direction={record.direction} />
                    <span>{formatPrice(Math.abs(Number(record.change_amount || 0)))}</span>
                    <small>{formatPercent(record.change_percent)}</small>
                  </span>
                </td>
                <td><DemandBadge value={record.demand_level} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function MarketAnalysis() {
  const [dashboard, setDashboard] = useState(null);
  const [divisionFilter, setDivisionFilter] = useState('All');
  const [fishFilter, setFishFilter] = useState('All');
  const [selectedKey, setSelectedKey] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const loadDashboard = useCallback(async (refresh = false) => {
    if (refresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError('');

    try {
      const data = await getMarketAnalysisDashboard({ refresh });
      setDashboard(data);
      setSelectedKey(currentKey => {
        const hasCurrentRecord = data?.records?.some(record => (
          `${record.fish_name}-${record.division}` === currentKey
        ));
        if (hasCurrentRecord) return currentKey;

        const firstRecord = data?.records?.[0];
        return firstRecord ? `${firstRecord.fish_name}-${firstRecord.division}` : '';
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    queueMicrotask(() => {
      loadDashboard();
    });
  }, [loadDashboard]);

  const records = useMemo(() => {
    const allRecords = dashboard?.records || [];
    return allRecords.filter(record => (
      (divisionFilter === 'All' || record.division === divisionFilter)
      && (fishFilter === 'All' || record.fish_name === fishFilter)
    ));
  }, [dashboard, divisionFilter, fishFilter]);

  const selectedRecord = useMemo(() => (
    records.find(record => `${record.fish_name}-${record.division}` === selectedKey)
    || records[0]
    || null
  ), [records, selectedKey]);
  const effectiveSelectedKey = selectedRecord ? `${selectedRecord.fish_name}-${selectedRecord.division}` : '';
  const mover = dashboard?.summary?.biggest_mover;

  return (
    <section className="ma-root" aria-labelledby="market-analysis-title">
      <div className="ma-header">
        <div>
          <span className="ma-kicker">Market Analysis</span>
          <h1 id="market-analysis-title">Bangladesh Fish Price Dashboard</h1>
          {dashboard?.as_of_date && <p>Updated for {formatDate(dashboard.as_of_date, { dateStyle: 'medium' })}</p>}
          {dashboard?.price_source && <p className="ma-source">Source: {dashboard.price_source}</p>}
        </div>
        <div className="ma-controls">
          <button
            type="button"
            className="ma-refresh-button"
            onClick={() => loadDashboard(true)}
            disabled={loading || refreshing}
          >
            <span aria-hidden="true">{'\u21bb'}</span>
            {refreshing ? 'Refreshing...' : 'Refresh prices'}
          </button>
          <label className="ma-field">
            <span>Division</span>
            <select value={divisionFilter} onChange={event => setDivisionFilter(event.target.value)}>
              <option value="All">All divisions</option>
              {(dashboard?.divisions || []).map(division => (
                <option key={division} value={division}>{division}</option>
              ))}
            </select>
          </label>
          <label className="ma-field">
            <span>Fish</span>
            <select value={fishFilter} onChange={event => setFishFilter(event.target.value)}>
              <option value="All">All fish</option>
              {(dashboard?.fish || []).map(fish => (
                <option key={fish} value={fish}>{fish}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {loading ? (
        <PanelState>Loading market prices...</PanelState>
      ) : error ? (
        <PanelState type="error">{error}</PanelState>
      ) : !dashboard ? (
        <PanelState>No market analysis data found.</PanelState>
      ) : (
        <div className="ma-dashboard">
          <div className="ma-summary">
            <SummaryCard label="Market Points" value={dashboard.summary.market_points} />
            <SummaryCard label="Average Today" value={formatPrice(dashboard.summary.average_price_today)} tone="blue" />
            <SummaryCard label="High Demand" value={dashboard.summary.high_demand_count} tone="amber" />
            <SummaryCard
              label="Biggest Move"
              value={mover ? `${mover.fish_name}, ${mover.division} ${formatPercent(mover.change_percent)}` : '--'}
              tone={mover?.direction === 'down' ? 'red' : 'green'}
            />
          </div>

          {records.length ? (
            <>
              <MarketTable records={records} selectedKey={effectiveSelectedKey} onSelect={setSelectedKey} />

              {selectedRecord && (
                <div className="ma-detail">
                  <section className="ma-panel ma-selected">
                    <div>
                      <span className="ma-kicker">Selected Market</span>
                      <h2>{selectedRecord.fish_name} in {selectedRecord.division}</h2>
                    </div>
                    <div className="ma-selected-price">
                      <strong>{formatPrice(selectedRecord.today_price)}</strong>
                      <span>
                        <DirectionArrow direction={selectedRecord.direction} />
                        {formatPercent(selectedRecord.change_percent)} from yesterday
                      </span>
                    </div>
                  </section>

                  <SeriesPanel title="Last 7 Days Price" items={selectedRecord.last_7_days} valueKey="price" />
                  <SeriesPanel title="Future 7 Days Price Prediction" items={selectedRecord.next_7_days} valueKey="predicted_price" />
                </div>
              )}
            </>
          ) : (
            <PanelState>No prices match these filters.</PanelState>
          )}
        </div>
      )}
    </section>
  );
}