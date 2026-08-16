import React, { useCallback, useEffect, useMemo, useState } from 'react';

import {
  createHealthRecord,
  createTreatmentPlan,
  addTreatmentTrackingEntry,
  getDiseaseLibrary,
  getFishHealthAlerts,
  getFishHealthDashboard,
  getFishHealthRecommendation,
  getHealthRecords,
  getPondStocks,
  getPonds,
  getTreatmentPlans,
  markFishHealthAlertsRead,
} from '../../lib/api';
import './FishHealthManagement.css';

const TABS = [
  'Dashboard',
  'Diagnosis Form',
  'Health Records',
  'Disease Library',
  'Treatments',
  'AI Recommendation',
  'Alerts',
];

const SYMPTOMS = [
  'gasping at surface',
  'rapid gill movement',
  'red gills',
  'white spots',
  'rubbing body',
  'frayed fins',
  'cotton like patches',
  'skin ulcers',
  'lethargy',
  'reduced feeding',
  'erratic swimming',
  'sudden death',
  'morning mortality',
  'visible worms',
  'clamped fins',
  'pale gills',
];

const EMPTY_RECORD = {
  fish_stock: '',
  observed_at: '',
  species: '',
  symptoms: [],
  symptom_notes: '',
  abnormal_behavior: '',
  affected_count: '',
  mortality_count: '',
};

const EMPTY_TREATMENT = {
  fish_stock: '',
  health_record: '',
  disease: '',
  medicine_name: '',
  dosage: '',
  start_date: '',
  end_date: '',
  cost: '',
  instructions: '',
  status: 'Planned',
  outcome_notes: '',
};

function formatDate(value) {
  if (!value) return 'No date';

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function formatShortDate(value) {
  if (!value) return 'Open';

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
  }).format(new Date(value));
}

function statusClass(value) {
  return String(value || 'empty').toLowerCase();
}

function PanelState({ type = 'empty', children }) {
  return <div className={`fhm-state fhm-state-${type}`}>{children}</div>;
}

function StatusPill({ value }) {
  return <span className={`fhm-pill fhm-pill-${statusClass(value)}`}>{value || 'No Data'}</span>;
}

function DashboardView({ dashboard, loading, error }) {
  if (loading) return <PanelState>Loading fish health dashboard...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;
  if (!dashboard) return <PanelState>No fish health data yet.</PanelState>;

  const summary = dashboard.summary || {};

  return (
    <div className="fhm-stack">
      <div className="fhm-overview">
        <Metric label="Health Records" value={summary.total_records || 0} />
        <Metric label="Active Cases" value={summary.active_cases || 0} />
        <Metric label="Critical Cases" value={summary.critical_cases || 0} tone="danger" />
        <Metric label="Active Treatments" value={summary.active_treatments || 0} />
        <Metric label="Disease Library" value={summary.disease_library_count || 0} />
        <Metric label="Unread Alerts" value={summary.unread_health_alerts || 0} tone="warning" />
      </div>

      <div className="fhm-grid-two">
        <ContextPanel title="Water Quality Context" context={dashboard.water_quality} />
        <ContextPanel title="Weather Context" context={dashboard.weather} />
      </div>

      <section className="fhm-panel">
        <div className="fhm-panel-header">
          <div>
            <span>Recent Cases</span>
            <h2>Latest Health Records</h2>
          </div>
        </div>
        <RecordList records={dashboard.latest_records || []} compact />
      </section>
    </div>
  );
}

function Metric({ label, value, tone = 'default' }) {
  return (
    <article className={`fhm-metric fhm-metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ContextPanel({ title, context }) {
  const snapshot = context?.snapshot || {};
  const notes = context?.risk_notes || [];

  return (
    <section className="fhm-panel">
      <div className="fhm-panel-header">
        <div>
          <span>Integrated Data</span>
          <h2>{title}</h2>
        </div>
      </div>
      {!Object.keys(snapshot).length ? (
        <PanelState>No latest data available for this pond.</PanelState>
      ) : (
        <>
          <div className="fhm-context-grid">
            {Object.entries(snapshot)
              .filter(([key]) => !['id', 'alerts'].includes(key))
              .slice(0, 8)
              .map(([key, value]) => (
                <div key={key}>
                  <span>{key.replaceAll('_', ' ')}</span>
                  <strong>{String(value)}</strong>
                </div>
              ))}
          </div>
          {notes.length ? (
            <ul className="fhm-note-list">
              {notes.map(note => <li key={note}>{note}</li>)}
            </ul>
          ) : (
            <PanelState type="success">No major risk signal from the latest context.</PanelState>
          )}
        </>
      )}
    </section>
  );
}

function DiagnosisForm({ ponds, stocks, selectedPondId, onSaved }) {
  const [formData, setFormData] = useState(EMPTY_RECORD);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({ ...current, [name]: value }));
  }

  function toggleSymptom(symptom) {
    setFormData(current => ({
      ...current,
      symptoms: current.symptoms.includes(symptom)
        ? current.symptoms.filter(item => item !== symptom)
        : [...current.symptoms, symptom],
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');

    try {
      const selectedStock = stocks.find(stock => String(stock.id) === String(formData.fish_stock));
      const payload = {
        pond: Number(selectedPondId),
        fish_stock: formData.fish_stock ? Number(formData.fish_stock) : null,
        observed_at: formData.observed_at ? new Date(formData.observed_at).toISOString() : new Date().toISOString(),
        species: formData.species || selectedStock?.species || '',
        symptoms: formData.symptoms,
        symptom_notes: formData.symptom_notes,
        abnormal_behavior: formData.abnormal_behavior,
        affected_count: Number(formData.affected_count || 0),
        mortality_count: Number(formData.mortality_count || 0),
      };

      const saved = await createHealthRecord(payload);
      setResult(saved);
      setFormData(EMPTY_RECORD);
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (!ponds.length) {
    return <PanelState>Add a pond before creating health records.</PanelState>;
  }

  return (
    <div className="fhm-grid-two fhm-align-start">
      <form className="fhm-panel fhm-form" onSubmit={handleSubmit}>
        <div className="fhm-panel-header">
          <div>
            <span>Symptom Input</span>
            <h2>Diagnose Possible Disease</h2>
          </div>
        </div>

        <div className="fhm-form-grid">
          <label className="fhm-field">
            <span>Fish Stock</span>
            <select name="fish_stock" value={formData.fish_stock} onChange={handleChange}>
              <option value="">Not linked</option>
              {stocks.map(stock => (
                <option key={stock.id} value={stock.id}>{stock.batch_name} - {stock.species}</option>
              ))}
            </select>
          </label>
          <label className="fhm-field">
            <span>Observed At</span>
            <input name="observed_at" type="datetime-local" value={formData.observed_at} onChange={handleChange} />
          </label>
          <label className="fhm-field">
            <span>Species</span>
            <input name="species" value={formData.species} onChange={handleChange} placeholder="Any fish species" />
          </label>
          <label className="fhm-field">
            <span>Affected Count</span>
            <input name="affected_count" type="number" min="0" value={formData.affected_count} onChange={handleChange} />
          </label>
          <label className="fhm-field">
            <span>Mortality Count</span>
            <input name="mortality_count" type="number" min="0" value={formData.mortality_count} onChange={handleChange} />
          </label>
        </div>

        <div className="fhm-checks" aria-label="Symptoms">
          {SYMPTOMS.map(symptom => (
            <label key={symptom} className="fhm-check">
              <input type="checkbox" checked={formData.symptoms.includes(symptom)} onChange={() => toggleSymptom(symptom)} />
              <span>{symptom}</span>
            </label>
          ))}
        </div>

        <label className="fhm-field">
          <span>Symptom Notes</span>
          <textarea name="symptom_notes" rows="4" value={formData.symptom_notes} onChange={handleChange} placeholder="Describe color, movement, appetite, visible wounds, or mortality pattern." />
        </label>

        <label className="fhm-field">
          <span>Abnormal Behavior</span>
          <textarea name="abnormal_behavior" rows="3" value={formData.abnormal_behavior} onChange={handleChange} />
        </label>

        {error && <PanelState type="error">{error}</PanelState>}

        <div className="fhm-actions">
          <button type="button" className="fhm-btn fhm-btn-secondary" onClick={() => setFormData(EMPTY_RECORD)}>Clear</button>
          <button type="submit" className="fhm-btn fhm-btn-primary" disabled={saving || !selectedPondId}>
            {saving ? 'Diagnosing...' : 'Save and Diagnose'}
          </button>
        </div>
      </form>

      <DiagnosisResult record={result} />
    </div>
  );
}

function DiagnosisResult({ record }) {
  if (!record) {
    return (
      <section className="fhm-panel">
        <div className="fhm-panel-header">
          <div>
            <span>Output</span>
            <h2>Possible Diseases</h2>
          </div>
        </div>
        <PanelState>Submit symptoms to generate possible disease matches.</PanelState>
      </section>
    );
  }

  return (
    <section className="fhm-panel">
      <div className="fhm-panel-header">
        <div>
          <span>Output</span>
          <h2>Possible Diseases</h2>
        </div>
        <StatusPill value={record.severity} />
      </div>

      {!record.possible_diseases?.length ? (
        <PanelState>No strong disease match found.</PanelState>
      ) : (
        <div className="fhm-disease-match-list">
          {record.possible_diseases.map(disease => (
            <article key={disease.name} className="fhm-match-card">
              <div className="fhm-card-top">
                <h3>{disease.name}</h3>
                <strong>{disease.confidence}%</strong>
              </div>
              <StatusPill value={disease.risk_level} />
              <p>{disease.description}</p>
              <small>Matched: {disease.matched_symptoms?.join(', ') || 'environment context'}</small>
              <TreatmentGuide protocols={disease.treatment_protocols || []} maintenance={disease.maintenance_actions || []} />
            </article>
          ))}
        </div>
      )}

      <div className="fhm-recommendation">
        <span>AI Health Recommendation</span>
        <p>{record.ai_recommendation}</p>
      </div>
    </section>
  );
}

function RecordList({ records, compact = false }) {
  if (!records.length) return <PanelState>No health records found.</PanelState>;

  return (
    <div className="fhm-table-wrap">
      <table className="fhm-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Pond</th>
            <th>Stock</th>
            <th>Symptoms</th>
            <th>Severity</th>
            <th>Status</th>
            {!compact && <th>Recommendation</th>}
          </tr>
        </thead>
        <tbody>
          {records.map(record => (
            <tr key={record.id}>
              <td>{formatDate(record.observed_at)}</td>
              <td>{record.pond_name}</td>
              <td>{record.fish_stock_name || 'Not linked'}</td>
              <td>{record.symptoms?.slice(0, 3).join(', ') || 'Notes only'}</td>
              <td><StatusPill value={record.severity} /></td>
              <td><StatusPill value={record.status} /></td>
              {!compact && <td>{record.ai_recommendation || 'No recommendation'}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DiseaseLibrary({ diseases, loading, error }) {
  if (loading) return <PanelState>Loading disease library...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;
  if (!diseases.length) return <PanelState>No disease library entries found.</PanelState>;

  return (
    <div className="fhm-library-grid">
      {diseases.map(disease => (
        <article key={disease.id} className="fhm-panel fhm-library-card">
          <div className="fhm-card-top">
            <h2>{disease.name}</h2>
            <StatusPill value={disease.risk_level} />
          </div>
          <p>{disease.description}</p>
          <dl>
            <div>
              <dt>Symptoms</dt>
              <dd>{disease.symptoms.join(', ')}</dd>
            </div>
            <div>
              <dt>Treatment</dt>
              <dd>{disease.recommended_treatments.slice(0, 2).join(' ')}</dd>
            </div>
            <div>
              <dt>Medicine and Dosage</dt>
              <dd>
                <TreatmentGuide protocols={disease.treatment_protocols || []} maintenance={disease.maintenance_actions || []} compact />
              </dd>
            </div>
            <div>
              <dt>Prevention</dt>
              <dd>{disease.prevention.slice(0, 2).join(' ')}</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}

function TreatmentGuide({ protocols, maintenance, compact = false }) {
  if (!protocols.length && !maintenance.length) {
    return <span className="fhm-muted-text">No structured treatment guide added.</span>;
  }

  return (
    <div className={`fhm-treatment-guide ${compact ? 'fhm-treatment-guide-compact' : ''}`}>
      {protocols.slice(0, compact ? 1 : 2).map(protocol => (
        <article key={`${protocol.medicine}-${protocol.dosage}`} className="fhm-protocol-card">
          <div>
            <span>Medicine</span>
            <strong>{protocol.medicine}</strong>
          </div>
          <div>
            <span>Dosage</span>
            <p>{protocol.dosage}</p>
          </div>
          {!compact && (
            <>
              <div>
                <span>Duration</span>
                <p>{protocol.duration}</p>
              </div>
              <div>
                <span>Estimated Cost</span>
                <p>{protocol.estimated_cost}</p>
              </div>
              <div>
                <span>Maintenance</span>
                <p>{protocol.maintenance}</p>
              </div>
            </>
          )}
        </article>
      ))}
      {!compact && maintenance.length > 0 && (
        <ul className="fhm-maintenance-list">
          {maintenance.slice(0, 3).map(action => <li key={action}>{action}</li>)}
        </ul>
      )}
    </div>
  );
}

function TreatmentManager({ stocks, records, diseases, treatments, selectedPondId, onSaved }) {
  const [formData, setFormData] = useState(EMPTY_TREATMENT);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [trackingFor, setTrackingFor] = useState(null);
  const [trackingForm, setTrackingForm] = useState({
    status: 'Active',
    administered_dosage: '',
    quantity_used: '',
    notes: '',
    follow_up_date: '',
    follow_up_notes: '',
  });
  const [trackingSaving, setTrackingSaving] = useState(false);
  const [trackingError, setTrackingError] = useState('');

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');

    try {
      await createTreatmentPlan({
        pond: Number(selectedPondId),
        fish_stock: formData.fish_stock ? Number(formData.fish_stock) : null,
        health_record: formData.health_record ? Number(formData.health_record) : null,
        disease: formData.disease ? Number(formData.disease) : null,
        medicine_name: formData.medicine_name,
        dosage: formData.dosage,
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        cost: Number(formData.cost || 0),
        instructions: formData.instructions,
        status: formData.status,
        outcome_notes: formData.outcome_notes,
      });
      setFormData(EMPTY_TREATMENT);
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function openTracking(treatment) {
    setTrackingFor(treatment.id);
    setTrackingError('');
    setTrackingForm({
      status: treatment.status === 'Planned' ? 'Active' : treatment.status,
      administered_dosage: treatment.dosage || '',
      quantity_used: '',
      notes: '',
      follow_up_date: '',
      follow_up_notes: '',
    });
  }

  function handleTrackingChange(event) {
    const { name, value } = event.target;
    setTrackingForm(current => ({ ...current, [name]: value }));
  }

  async function handleTrackingSubmit(event, treatmentId) {
    event.preventDefault();
    setTrackingSaving(true);
    setTrackingError('');

    try {
      await addTreatmentTrackingEntry(treatmentId, {
        ...trackingForm,
        quantity_used: trackingForm.quantity_used ? Number(trackingForm.quantity_used) : null,
        follow_up_date: trackingForm.follow_up_date || null,
      });
      setTrackingFor(null);
      onSaved?.();
    } catch (err) {
      setTrackingError(err.message);
    } finally {
      setTrackingSaving(false);
    }
  }

  return (
    <div className="fhm-grid-two fhm-align-start">
      <form className="fhm-panel fhm-form" onSubmit={handleSubmit}>
        <div className="fhm-panel-header">
          <div>
            <span>Treatment</span>
            <h2>Plan Treatment</h2>
          </div>
        </div>
        <div className="fhm-form-grid">
          <label className="fhm-field">
            <span>Fish Stock</span>
            <select name="fish_stock" value={formData.fish_stock} onChange={handleChange}>
              <option value="">Not linked</option>
              {stocks.map(stock => <option key={stock.id} value={stock.id}>{stock.batch_name} - {stock.species}</option>)}
            </select>
          </label>
          <label className="fhm-field">
            <span>Health Record</span>
            <select name="health_record" value={formData.health_record} onChange={handleChange}>
              <option value="">Not linked</option>
              {records.map(record => <option key={record.id} value={record.id}>{formatDate(record.observed_at)} - {record.severity}</option>)}
            </select>
          </label>
          <label className="fhm-field">
            <span>Disease</span>
            <select name="disease" value={formData.disease} onChange={handleChange}>
              <option value="">Unknown</option>
              {diseases.map(disease => <option key={disease.id} value={disease.id}>{disease.name}</option>)}
            </select>
          </label>
          <label className="fhm-field">
            <span>Medicine</span>
            <input name="medicine_name" value={formData.medicine_name} onChange={handleChange} required />
          </label>
          <label className="fhm-field">
            <span>Dosage</span>
            <input name="dosage" value={formData.dosage} onChange={handleChange} required />
          </label>
          <label className="fhm-field">
            <span>Cost</span>
            <input name="cost" type="number" min="0" step="0.01" value={formData.cost} onChange={handleChange} />
          </label>
          <label className="fhm-field">
            <span>Start Date</span>
            <input name="start_date" type="date" value={formData.start_date} onChange={handleChange} required />
          </label>
          <label className="fhm-field">
            <span>End Date</span>
            <input name="end_date" type="date" value={formData.end_date} onChange={handleChange} />
          </label>
          <label className="fhm-field">
            <span>Status</span>
            <select name="status" value={formData.status} onChange={handleChange}>
              {['Planned', 'Active', 'Completed', 'Cancelled'].map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
        </div>
        <label className="fhm-field">
          <span>Instructions</span>
          <textarea name="instructions" rows="3" value={formData.instructions} onChange={handleChange} />
        </label>
        <label className="fhm-field">
          <span>Outcome Notes</span>
          <textarea name="outcome_notes" rows="3" value={formData.outcome_notes} onChange={handleChange} />
        </label>
        {error && <PanelState type="error">{error}</PanelState>}
        <div className="fhm-actions">
          <button type="submit" className="fhm-btn fhm-btn-primary" disabled={saving || !selectedPondId}>
            {saving ? 'Saving...' : 'Save Treatment'}
          </button>
        </div>
      </form>

      <section className="fhm-panel">
        <div className="fhm-panel-header">
          <div>
            <span>Treatment History</span>
            <h2>Plans</h2>
          </div>
        </div>
        {!treatments.length ? (
          <PanelState>No treatment plans yet.</PanelState>
        ) : (
          <div className="fhm-treatment-list">
            {treatments.map(treatment => (
              <article key={treatment.id} className="fhm-treatment-card">
                <div className="fhm-card-top">
                  <h3>{treatment.medicine_name}</h3>
                  <StatusPill value={treatment.status} />
                </div>
                <p>{treatment.dosage}</p>
                <small>{formatShortDate(treatment.start_date)} to {formatShortDate(treatment.end_date)} · Cost {treatment.cost}</small>
                <div className="fhm-treatment-tracking">
                  <div className="fhm-card-top">
                    <strong>Tracking history</strong>
                    <button type="button" className="fhm-btn fhm-btn-secondary" onClick={() => openTracking(treatment)}>
                      Add update
                    </button>
                  </div>
                  {(treatment.tracking || []).map(entry => (
                    <div key={entry.id} className="fhm-tracking-entry">
                      <div><StatusPill value={entry.status} /><small>{formatDate(entry.created_at)}</small></div>
                      {entry.administered_dosage && <span>Dosage: {entry.administered_dosage}</span>}
                      {entry.quantity_used && <span>Used: {entry.quantity_used}</span>}
                      {entry.notes && <span>{entry.notes}</span>}
                      {entry.follow_up_date && <span>Follow-up: {formatShortDate(entry.follow_up_date)}</span>}
                      {entry.follow_up_notes && <span>{entry.follow_up_notes}</span>}
                    </div>
                  ))}
                  {trackingFor === treatment.id && (
                    <form className="fhm-tracking-form" onSubmit={event => handleTrackingSubmit(event, treatment.id)}>
                      <label className="fhm-field"><span>Status</span><select name="status" value={trackingForm.status} onChange={handleTrackingChange}>{['Planned', 'Active', 'Completed', 'Cancelled'].map(item => <option key={item} value={item}>{item}</option>)}</select></label>
                      <label className="fhm-field"><span>Actual dosage</span><input name="administered_dosage" value={trackingForm.administered_dosage} onChange={handleTrackingChange} /></label>
                      <label className="fhm-field"><span>Quantity used</span><input name="quantity_used" type="number" min="0" step="0.01" value={trackingForm.quantity_used} onChange={handleTrackingChange} /></label>
                      <label className="fhm-field"><span>Follow-up date</span><input name="follow_up_date" type="date" value={trackingForm.follow_up_date} onChange={handleTrackingChange} /></label>
                      <label className="fhm-field"><span>Notes</span><textarea name="notes" rows="2" value={trackingForm.notes} onChange={handleTrackingChange} /></label>
                      <label className="fhm-field"><span>Follow-up notes</span><textarea name="follow_up_notes" rows="2" value={trackingForm.follow_up_notes} onChange={handleTrackingChange} /></label>
                      {trackingError && <PanelState type="error">{trackingError}</PanelState>}
                      <div className="fhm-actions"><button type="button" className="fhm-btn fhm-btn-secondary" onClick={() => setTrackingFor(null)}>Cancel</button><button type="submit" className="fhm-btn fhm-btn-primary" disabled={trackingSaving}>{trackingSaving ? 'Saving...' : 'Save update'}</button></div>
                    </form>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function RecommendationPanel({ recommendation, loading, error }) {
  if (loading) return <PanelState>Loading AI recommendation...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;

  return (
    <section className="fhm-panel">
      <div className="fhm-panel-header">
        <div>
          <span>AI Health Recommendation</span>
          <h2>Latest Guidance</h2>
        </div>
      </div>
      <div className="fhm-recommendation fhm-recommendation-large">
        <p>{recommendation?.recommendation || 'Create a health record to generate recommendations.'}</p>
      </div>
      {recommendation?.record && (
        <DiagnosisResult record={recommendation.record} />
      )}
    </section>
  );
}

function AlertsPanel({ alerts, loading, error, onMarkRead }) {
  if (loading) return <PanelState>Loading health alerts...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;

  return (
    <section className="fhm-panel">
      <div className="fhm-panel-header">
        <div>
          <span>In App Notifications</span>
          <h2>Health Alerts</h2>
        </div>
        <button type="button" className="fhm-btn fhm-btn-secondary" onClick={onMarkRead} disabled={!alerts.length}>
          Mark all read
        </button>
      </div>
      {!alerts.length ? (
        <PanelState>No fish health alerts.</PanelState>
      ) : (
        <div className="fhm-alert-list">
          {alerts.map(alert => (
            <article key={alert.id} className={`fhm-alert fhm-alert-${alert.is_read ? 'read' : 'unread'}`}>
              <div>
                <strong>{alert.pond_name}</strong>
                <p>{alert.reason}</p>
                <small>{formatDate(alert.created_at)}</small>
              </div>
              <StatusPill value={alert.priority} />
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default function FishHealthManagement() {
  const [ponds, setPonds] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [records, setRecords] = useState([]);
  const [diseases, setDiseases] = useState([]);
  const [treatments, setTreatments] = useState([]);
  const [recommendation, setRecommendation] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const selectedPond = useMemo(
    () => ponds.find(pond => String(pond.id) === String(selectedPondId)),
    [ponds, selectedPondId],
  );

  const loadPonds = useCallback(async () => {
    try {
      const data = await getPonds();
      setPonds(data || []);
      if (data?.[0]?.id) {
        setSelectedPondId(current => current || String(data[0].id));
      }
    } catch {
      setPonds([]);
    }
  }, []);

  const loadCoreData = useCallback(async (pondId = selectedPondId) => {
    if (!pondId) return;
    setLoading(true);
    setError('');

    try {
      const [dashboardData, recordData, diseaseData, treatmentData, recommendationData, alertData, stockData] = await Promise.all([
        getFishHealthDashboard(pondId),
        getHealthRecords({ pond: pondId }),
        getDiseaseLibrary(),
        getTreatmentPlans({ pond: pondId }),
        getFishHealthRecommendation(pondId),
        getFishHealthAlerts(pondId),
        getPondStocks(pondId),
      ]);

      setDashboard(dashboardData);
      setRecords(recordData || []);
      setDiseases(diseaseData || []);
      setTreatments(treatmentData || []);
      setRecommendation(recommendationData);
      setAlerts(alertData || []);
      setStocks(stockData || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedPondId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadPonds();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [loadPonds]);

  useEffect(() => {
    if (!selectedPondId) return undefined;

    const timer = window.setTimeout(() => {
      loadCoreData(selectedPondId);
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedPondId, loadCoreData]);

  async function handleSaved() {
    await loadCoreData(selectedPondId);
  }

  async function handleMarkAlertsRead() {
    await markFishHealthAlertsRead('all');
    await loadCoreData(selectedPondId);
  }

  return (
    <section className="fhm-root" aria-labelledby="fish-health-title">
      <div className="fhm-header">
        <div>
          <span>Fish Health</span>
          <h1 id="fish-health-title">Fish Health Management</h1>
        </div>
        <label className="fhm-field fhm-pond-picker">
          <span>Pond</span>
          <select value={selectedPondId} onChange={event => setSelectedPondId(event.target.value)}>
            {ponds.length === 0 ? <option value="">No ponds</option> : ponds.map(pond => (
              <option key={pond.id} value={pond.id}>{pond.name}</option>
            ))}
          </select>
        </label>
      </div>

      {selectedPond && (
        <div className="fhm-selected-pond">
          <strong>{selectedPond.name}</strong>
          <span>{selectedPond.location}</span>
        </div>
      )}

      <div className="fhm-tabs" role="tablist" aria-label="Fish health views">
        {TABS.map(tab => (
          <button key={tab} type="button" className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {!ponds.length ? (
        <PanelState>Add a pond before using fish health management.</PanelState>
      ) : error && activeTab === 'Dashboard' ? (
        <PanelState type="error">{error}</PanelState>
      ) : (
        <>
          {activeTab === 'Dashboard' && <DashboardView dashboard={dashboard} loading={loading} error={error} />}
          {activeTab === 'Diagnosis Form' && (
            <DiagnosisForm
              ponds={ponds}
              stocks={stocks}
              selectedPondId={selectedPondId}
              onSaved={handleSaved}
            />
          )}
          {activeTab === 'Health Records' && (
            <section className="fhm-panel">
              <div className="fhm-panel-header">
                <div>
                  <span>Records</span>
                  <h2>Health Records</h2>
                </div>
              </div>
              {loading ? <PanelState>Loading health records...</PanelState> : <RecordList records={records} />}
            </section>
          )}
          {activeTab === 'Disease Library' && <DiseaseLibrary diseases={diseases} loading={loading} error={error} />}
          {activeTab === 'Treatments' && (
            <TreatmentManager
              stocks={stocks}
              records={records}
              diseases={diseases}
              treatments={treatments}
              selectedPondId={selectedPondId}
              onSaved={handleSaved}
            />
          )}
          {activeTab === 'AI Recommendation' && <RecommendationPanel recommendation={recommendation} loading={loading} error={error} />}
          {activeTab === 'Alerts' && <AlertsPanel alerts={alerts} loading={loading} error={error} onMarkRead={handleMarkAlertsRead} />}
        </>
      )}
    </section>
  );
}
