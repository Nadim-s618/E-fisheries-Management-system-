import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { getPonds, getWeatherDashboard } from '../../lib/api';
import './WeatherManagement.css';

const RISK_LABELS = {
  Low: 'Low',
  Moderate: 'Moderate',
  High: 'High',
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
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}${unit ? ` ${unit}` : ''}`;
}

function riskClass(value) {
  return String(value || 'Low').toLowerCase();
}

function weatherIcon(code) {
  if ([0, 1].includes(code)) return 'Sun';
  if ([2, 3].includes(code)) return 'Cloud';
  if ([45, 48].includes(code)) return 'Mist';
  if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(code)) return 'Rain';
  if ([95, 96, 99].includes(code)) return 'Storm';
  return 'Weather';
}

function PanelState({ type = 'empty', children }) {
  return <div className={`wm-state wm-state-${type}`}>{children}</div>;
}

function MetricCard({ label, value, unit, tone = 'neutral' }) {
  return (
    <article className={`wm-metric wm-metric-${tone}`}>
      <span>{label}</span>
      <strong>{formatValue(value, unit)}</strong>
    </article>
  );
}

function RiskBadge({ value }) {
  return (
    <span className={`wm-risk wm-risk-${riskClass(value)}`}>
      {RISK_LABELS[value] || value || 'Low'}
    </span>
  );
}

function RecommendationList({ items }) {
  return (
    <ul className="wm-recommendations">
      {(items || []).map(item => (
        <li key={item.text} className={`wm-rec wm-rec-${item.status}`}>
          <span aria-hidden="true">{item.status === 'ok' ? '✓' : '!'}</span>
          {item.text}
        </li>
      ))}
    </ul>
  );
}

function Alerts({ alerts }) {
  return (
    <div className="wm-alert-list">
      {(alerts || []).map(alert => (
        <div key={alert.text} className={`wm-alert wm-alert-${alert.level}`}>
          <span>{alert.level === 'ok' ? 'OK' : '!'}</span>
          <p>{alert.text}</p>
        </div>
      ))}
    </div>
  );
}

function ForecastStrip({ forecast }) {
  if (!forecast?.length) return null;

  return (
    <div className="wm-forecast-strip" aria-label="Future weather prediction">
      {forecast.map(item => (
        <article key={item.time} className="wm-forecast-item">
          <span>{new Intl.DateTimeFormat(undefined, { hour: 'numeric' }).format(new Date(item.time))}</span>
          <strong>{formatValue(item.air_temperature, '°C')}</strong>
          <small>{formatValue(item.rainfall_probability, '% rain')}</small>
        </article>
      ))}
    </div>
  );
}

function WeatherDashboard({ data, stale, sourceError }) {
  const report = data?.report;
  if (!report) return null;

  return (
    <div className="wm-dashboard">
      {(stale || sourceError) && (
        <PanelState type="warning">
          Showing last saved report. {sourceError}
        </PanelState>
      )}

      <section className="wm-hero" aria-label="Today's weather">
        <div>
          <span className="wm-kicker">Today's Weather</span>
          <h2>{report.pond_name}</h2>
          <p>{report.resolved_location}</p>
        </div>
        <div className="wm-hero-reading">
          <span>{weatherIcon(report.weather_code)}</span>
          <strong>{formatValue(report.air_temperature, '°C')}</strong>
        </div>
      </section>

      <div className="wm-metrics">
        <MetricCard label="Humidity" value={report.humidity} unit="%" tone="blue" />
        <MetricCard label="Rainfall" value={report.rainfall_probability} unit="%" tone="rain" />
        <MetricCard label="Wind Speed" value={report.wind_speed} unit="km/h" tone="wind" />
        <MetricCard label="UV Index" value={report.uv_index} tone="sun" />
        <MetricCard label="Cloud Cover" value={report.cloud_cover} unit="%" tone="cloud" />
        <MetricCard label="Pressure" value={report.atmospheric_pressure} unit="hPa" tone="pressure" />
      </div>

      <div className="wm-grid">
        <section className="wm-panel wm-panel-risk">
          <div className="wm-panel-title">
            <span>Fish Weather Risk</span>
            <RiskBadge value={report.fish_weather_risk} />
          </div>
          <p>{report.pond_impact?.summary}</p>
        </section>

        <section className="wm-panel">
          <div className="wm-panel-title">
            <span>Feeding Recommendation</span>
          </div>
          <RecommendationList items={report.feeding_recommendation} />
        </section>

        <section className="wm-panel">
          <div className="wm-panel-title">
            <span>DO Prediction</span>
          </div>
          <div className="wm-do-grid">
            <div>
              <span>Morning</span>
              <strong>{formatValue(report.do_prediction?.morning, report.do_prediction?.unit)}</strong>
            </div>
            <div>
              <span>Night</span>
              <strong>{formatValue(report.do_prediction?.night, report.do_prediction?.unit)}</strong>
            </div>
          </div>
          <p className="wm-action">{report.do_prediction?.action}</p>
        </section>

        <section className="wm-panel">
          <div className="wm-panel-title">
            <span>Disease Risk</span>
            <RiskBadge value={report.disease_risk} />
          </div>
          <p>
            Humidity, cloud cover and rainfall are being tracked for fungal and bacterial pressure.
          </p>
        </section>

        <section className="wm-panel">
          <div className="wm-panel-title">
            <span>Rain Impact</span>
          </div>
          <dl className="wm-impact-list">
            <div><dt>pH</dt><dd>{report.rain_impact?.ph}</dd></div>
            <div><dt>Turbidity</dt><dd>{report.rain_impact?.turbidity}</dd></div>
            <div><dt>Overflow</dt><dd>{report.rain_impact?.overflow}</dd></div>
          </dl>
        </section>

        <section className="wm-panel">
          <div className="wm-panel-title">
            <span>Alerts</span>
          </div>
          <Alerts alerts={report.alerts} />
        </section>
      </div>

      <section className="wm-panel">
        <div className="wm-panel-title">
          <span>Future Prediction</span>
          <small>Updated {formatDate(report.updated_at)}</small>
        </div>
        <ForecastStrip forecast={report.forecast} />
      </section>

      <p className="wm-source">
        Weather data by <a href={report.source_url} target="_blank" rel="noreferrer">{report.source}</a>
      </p>
    </div>
  );
}

export default function WeatherManagement() {
  const [ponds, setPonds] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [loadingPonds, setLoadingPonds] = useState(true);
  const [loadingWeather, setLoadingWeather] = useState(false);
  const [error, setError] = useState('');

  const selectedPond = useMemo(
    () => ponds.find(pond => String(pond.id) === String(selectedPondId)),
    [ponds, selectedPondId],
  );

  useEffect(() => {
    let active = true;

    async function loadPonds() {
      setLoadingPonds(true);
      setError('');

      try {
        const data = await getPonds();
        if (!active) return;
        setPonds(data || []);
        setSelectedPondId(data?.[0]?.id ? String(data[0].id) : '');
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoadingPonds(false);
      }
    }

    loadPonds();

    return () => {
      active = false;
    };
  }, []);

  const loadWeather = useCallback(async (refresh = false) => {
    if (!selectedPondId) return;
    setLoadingWeather(true);
    setError('');

    try {
      const data = await getWeatherDashboard(selectedPondId, { refresh });
      setWeatherData(data);
    } catch (err) {
      setWeatherData(null);
      setError(err.message);
    } finally {
      setLoadingWeather(false);
    }
  }, [selectedPondId]);

  useEffect(() => {
    if (!selectedPondId) return undefined;

    let active = true;

    async function loadSelectedWeather() {
      setLoadingWeather(true);
      setError('');

      try {
        const data = await getWeatherDashboard(selectedPondId);
        if (active) setWeatherData(data);
      } catch (err) {
        if (active) {
          setWeatherData(null);
          setError(err.message);
        }
      } finally {
        if (active) setLoadingWeather(false);
      }
    }

    loadSelectedWeather();

    return () => {
      active = false;
    };
  }, [selectedPondId]);

  return (
    <section className="dp-management wm-root dp-weather-management" aria-labelledby="weather-title">
      <div className="dp-management-header wm-header dp-fade-in">
        <div>
          <span className="wm-kicker">Weather</span>
          <h1 id="weather-title">Pond Weather Dashboard</h1>
        </div>
        <div className="wm-controls">
          <label className="wm-field">
            <span>Pond</span>
            <select value={selectedPondId} onChange={event => setSelectedPondId(event.target.value)}>
              {ponds.length === 0 ? <option value="">No ponds</option> : ponds.map(pond => (
                <option key={pond.id} value={pond.id}>{pond.name}</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="wm-btn wm-btn-primary dp-btn-primary dp-btn-animated"
            onClick={() => loadWeather(true)}
            disabled={!selectedPondId || loadingWeather}
          >
            {loadingWeather ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {selectedPond && (
        <p className="wm-pond-note">
          Weather is matched from this pond location: <strong>{selectedPond.location}</strong>
        </p>
      )}

      {loadingPonds ? (
        <PanelState>Loading ponds...</PanelState>
      ) : !ponds.length ? (
        <PanelState>Add a pond before viewing weather reports.</PanelState>
      ) : loadingWeather && !weatherData ? (
        <PanelState>Loading pond weather...</PanelState>
      ) : error ? (
        <PanelState type="error">{error}</PanelState>
      ) : (
        <WeatherDashboard
          data={weatherData}
          stale={weatherData?.stale}
          sourceError={weatherData?.source_error}
        />
      )}
    </section>
  );
}
