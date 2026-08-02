import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  acceptFeedingRecommendation,
  completeFeedingSession,
  editFeedingRecommendation,
  getFeedingDashboard,
  getPonds,
} from '../../lib/api';
import './FeedingManagement.css';

const TABS = ['Recommendation', 'Tracker', 'History'];

function formatCurrency(value) {
  return `RM${Number(value || 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatNumber(value, suffix = '') {
  if (value === null || value === undefined || value === '') return '-';
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}${suffix}`;
}

function formatDate(value) {
  if (!value) return '-';
  return new Intl.DateTimeFormat(undefined, { day: '2-digit', month: 'short' }).format(new Date(`${value}T00:00:00`));
}

function formatDateTime(value) {
  if (!value) return '-';
  return new Intl.DateTimeFormat(undefined, {
    day: '2-digit',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value));
}

function emptyEditForm(recommendation) {
  return {
    recommended_feed_kg: recommendation?.recommended_feed_kg || '',
    feed_type: recommendation?.feed_type || 'Floating Feed 32%',
    price_per_kg: recommendation?.price_per_kg || '4.50',
    meals: recommendation?.meals || 2,
    meal_times: (recommendation?.schedule || []).map(item => item.time),
  };
}

function PanelState({ type = 'empty', children }) {
  return <div className={`ff-state ff-state-${type}`}>{children}</div>;
}

function RecommendationCard({ recommendation, onAccept, onEdit, saving }) {
  if (!recommendation) return <PanelState>No feeding recommendation available.</PanelState>;
  const isDraft = recommendation.status === 'draft';

  return (
    <section className="ff-recommendation" aria-label="Today's feeding recommendation">
      <div className="ff-rec-header">
        <span>Today's Feeding Recommendation</span>
        <strong>{recommendation.pond_name}</strong>
      </div>

      <div className="ff-rec-grid">
        <div>
          <span>Recommended Feed</span>
          <strong>{formatNumber(recommendation.recommended_feed_kg, ' kg')}</strong>
        </div>
        <div>
          <span>Feed Type</span>
          <strong>{recommendation.feed_type}</strong>
        </div>
        <div>
          <span>Price</span>
          <strong>{formatCurrency(recommendation.price_per_kg)}/kg</strong>
        </div>
        <div>
          <span>Estimated Cost</span>
          <strong>{formatCurrency(recommendation.estimated_cost)}</strong>
        </div>
        <div>
          <span>Meals</span>
          <strong>{recommendation.meals}</strong>
        </div>
      </div>

      <div className="ff-schedule">
        {(recommendation.schedule || []).map(item => (
          <div key={item.meal_number}>
            <span>{item.label}</span>
            <em aria-hidden="true">-&gt;</em>
            <strong>{formatNumber(item.feed_kg, ' kg')}</strong>
          </div>
        ))}
      </div>

      <div className="ff-reasons">
        <span>Reason</span>
        {(recommendation.reasons || []).map(reason => (
          <p key={reason}><span aria-hidden="true">{'\u2713'}</span>{reason}</p>
        ))}
      </div>

      <div className="ff-actions">
        <button type="button" className="ff-btn ff-btn-primary" onClick={onAccept} disabled={saving || !isDraft}>
          {saving ? 'Accepting...' : isDraft ? 'Accept' : 'Tracking'}
        </button>
        <button type="button" className="ff-btn ff-btn-secondary" onClick={onEdit} disabled={saving || !isDraft}>
          Edit
        </button>
      </div>
    </section>
  );
}

function EditPanel({ recommendation, onCancel, onSave, saving }) {
  const [form, setForm] = useState(() => emptyEditForm(recommendation));

  function handleChange(event) {
    const { name, value } = event.target;
    setForm(current => ({ ...current, [name]: value }));
  }

  function handleMealTimeChange(index, value) {
    setForm(current => {
      const mealTimes = [...current.meal_times];
      mealTimes[index] = value;
      return { ...current, meal_times: mealTimes };
    });
  }

  function handleMealsChange(event) {
    const meals = Number(event.target.value);
    setForm(current => {
      const mealTimes = [...current.meal_times];
      while (mealTimes.length < meals) mealTimes.push('16:30');
      return { ...current, meals, meal_times: mealTimes.slice(0, meals) };
    });
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSave({
      ...form,
      recommended_feed_kg: Number(form.recommended_feed_kg),
      price_per_kg: Number(form.price_per_kg),
      meals: Number(form.meals),
      meal_times: form.meal_times,
    });
  }

  return (
    <form className="ff-edit-panel" onSubmit={handleSubmit}>
      <div className="ff-form-grid">
        <label>
          <span>Recommended Feed (kg)</span>
          <input name="recommended_feed_kg" type="number" min="0.01" step="0.01" value={form.recommended_feed_kg} onChange={handleChange} required />
        </label>
        <label>
          <span>Feed Type</span>
          <input name="feed_type" value={form.feed_type} onChange={handleChange} required />
        </label>
        <label>
          <span>Price (RM/kg)</span>
          <input name="price_per_kg" type="number" min="0" step="0.01" value={form.price_per_kg} onChange={handleChange} required />
        </label>
        <label>
          <span>Meals</span>
          <input name="meals" type="number" min="1" max="4" step="1" value={form.meals} onChange={handleMealsChange} required />
        </label>
      </div>

      <div className="ff-time-grid">
        {form.meal_times.map((mealTime, index) => (
          <label key={`${index}-${form.meals}`}>
            <span>Meal {index + 1}</span>
            <input type="time" value={mealTime} onChange={event => handleMealTimeChange(index, event.target.value)} required />
          </label>
        ))}
      </div>

      <div className="ff-actions">
        <button type="button" className="ff-btn ff-btn-secondary" onClick={onCancel}>Cancel</button>
        <button type="submit" className="ff-btn ff-btn-primary" disabled={saving}>
          {saving ? 'Saving...' : 'Save & Track'}
        </button>
      </div>
    </form>
  );
}

function FeedingTracker({ plan, pendingSessions, completeValues, onValueChange, onComplete, savingSessionId }) {
  const sessions = plan?.sessions || pendingSessions || [];
  const pending = sessions.filter(session => session.status === 'pending');
  const completed = sessions.filter(session => session.status === 'completed');

  if (!plan && pending.length === 0) {
    return <PanelState>Accept or edit a recommendation to start tracking feed.</PanelState>;
  }

  return (
    <section className="ff-tracker">
      <div className="ff-tracker-summary">
        <div>
          <span>Active Feed</span>
          <strong>{formatNumber(plan?.recommended_feed_kg, ' kg')}</strong>
        </div>
        <div>
          <span>Completed</span>
          <strong>{completed.length}</strong>
        </div>
        <div>
          <span>Pending</span>
          <strong>{pending.length}</strong>
        </div>
      </div>

      <div className="ff-session-list">
        {sessions.map(session => (
          <article key={session.id} className={`ff-session ff-session-${session.status}`}>
            <div>
              <span>Meal {session.meal_number}</span>
              <strong>{formatDateTime(session.scheduled_at)}</strong>
              <small>{formatNumber(session.planned_feed_kg, ' kg')} planned</small>
            </div>
            {session.status === 'completed' ? (
              <div className="ff-session-done">
                <span>Completed</span>
                <strong>{formatNumber(session.actual_feed_kg, ' kg')}</strong>
              </div>
            ) : (
              <div className="ff-complete-form">
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={completeValues[session.id] ?? session.planned_feed_kg}
                  onChange={event => onValueChange(session.id, event.target.value)}
                  aria-label={`Actual feed for meal ${session.meal_number}`}
                />
                <button
                  type="button"
                  className="ff-btn ff-btn-primary"
                  onClick={() => onComplete(session)}
                  disabled={savingSessionId === session.id}
                >
                  {savingSessionId === session.id ? 'Saving...' : 'Complete'}
                </button>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function HistoryTable({ rows }) {
  if (!rows.length) return <PanelState>No feeding history yet.</PanelState>;

  return (
    <div className="ff-table-wrap">
      <table className="ff-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Pond</th>
            <th>Feed (kg)</th>
            <th>Cost</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.id}>
              <td>{formatDate(row.recommendation_date)}</td>
              <td>{row.pond_name}</td>
              <td>{formatNumber(row.recommended_feed_kg, ' kg')}</td>
              <td>{formatCurrency(row.estimated_cost)}</td>
              <td><span className={`ff-status ff-status-${String(row.computed_status || row.status).toLowerCase().replace(/\s+/g, '-')}`}>{row.computed_status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function FeedingManagement({ onNotificationChange }) {
  const [ponds, setPonds] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [activeTab, setActiveTab] = useState('Recommendation');
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingSessionId, setSavingSessionId] = useState(null);
  const [error, setError] = useState('');
  const [editOpen, setEditOpen] = useState(false);
  const [completeValues, setCompleteValues] = useState({});
  const [notice, setNotice] = useState('');

  const selectedPond = useMemo(
    () => ponds.find(pond => String(pond.id) === String(selectedPondId)),
    [ponds, selectedPondId],
  );

  const loadDashboard = useCallback(async (pondId = selectedPondId) => {
    if (!pondId) return;
    setLoading(true);
    setError('');

    try {
      const data = await getFeedingDashboard(pondId);
      setDashboard(data);
    } catch (err) {
      setDashboard(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedPondId]);

  useEffect(() => {
    let active = true;

    async function loadPonds() {
      setLoading(true);
      try {
        const data = await getPonds();
        if (!active) return;
        setPonds(data || []);
        setSelectedPondId(data?.[0]?.id ? String(data[0].id) : '');
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadPonds();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedPondId) return undefined;
    const timer = window.setTimeout(() => loadDashboard(selectedPondId), 0);
    return () => window.clearTimeout(timer);
  }, [loadDashboard, selectedPondId]);

  async function handleAccept() {
    if (!dashboard?.recommendation?.id) return;
    setSaving(true);
    setError('');
    setNotice('');

    try {
      await acceptFeedingRecommendation(dashboard.recommendation.id);
      await loadDashboard();
      setActiveTab('Tracker');
      onNotificationChange?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(payload) {
    if (!dashboard?.recommendation?.id) return;
    setSaving(true);
    setError('');
    setNotice('');

    try {
      await editFeedingRecommendation(dashboard.recommendation.id, payload);
      setEditOpen(false);
      await loadDashboard();
      setActiveTab('Tracker');
      onNotificationChange?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function handleCompleteValue(sessionId, value) {
    setCompleteValues(current => ({ ...current, [sessionId]: value }));
  }

  async function handleComplete(session) {
    setSavingSessionId(session.id);
    setError('');
    setNotice('');

    try {
      const result = await completeFeedingSession(session.id, {
        actual_feed_kg: Number(completeValues[session.id] ?? session.planned_feed_kg),
      });
      await loadDashboard();
      onNotificationChange?.();

      if (result.next_recommendation) {
        setNotice('All feeding sessions completed. A new recommendation is ready.');
        setActiveTab('Recommendation');
      } else if (result.next_session) {
        setNotice(`Next session: ${formatNumber(result.next_session.planned_feed_kg, ' kg')} at ${formatDateTime(result.next_session.scheduled_at)}.`);
        setActiveTab('Tracker');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingSessionId(null);
    }
  }

  return (
    <section className="ff-root" aria-labelledby="feeding-title">
      <div className="ff-header">
        <div>
          <span>Fish Feeding</span>
          <h1 id="feeding-title">Automatic Feeding Recommendation</h1>
        </div>
        <label className="ff-field ff-pond-picker">
          <span>Pond</span>
          <select value={selectedPondId} onChange={event => setSelectedPondId(event.target.value)}>
            {ponds.length === 0 ? <option value="">No ponds</option> : ponds.map(pond => (
              <option key={pond.id} value={pond.id}>{pond.name}</option>
            ))}
          </select>
        </label>
      </div>

      {selectedPond && (
        <div className="ff-context">
          <span>{selectedPond.location}</span>
          <strong>{formatNumber(selectedPond.stocking_capacity)} fish capacity</strong>
        </div>
      )}

      <div className="ff-tabs" role="tablist" aria-label="Feeding views">
        {TABS.map(tab => (
          <button key={tab} type="button" className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {error && <PanelState type="error">{error}</PanelState>}
      {notice && <PanelState type="success">{notice}</PanelState>}

      {loading ? (
        <PanelState>Loading feeding data...</PanelState>
      ) : !ponds.length ? (
        <PanelState>Add a pond before generating feeding recommendations.</PanelState>
      ) : activeTab === 'Recommendation' ? (
        <div className="ff-stack">
          <RecommendationCard
            recommendation={dashboard?.recommendation}
            onAccept={handleAccept}
            onEdit={() => setEditOpen(true)}
            saving={saving}
          />
          {editOpen && (
            <EditPanel
              recommendation={dashboard?.recommendation}
              onCancel={() => setEditOpen(false)}
              onSave={handleEditSave}
              saving={saving}
            />
          )}
        </div>
      ) : activeTab === 'Tracker' ? (
        <FeedingTracker
          plan={dashboard?.active_plan}
          pendingSessions={dashboard?.pending_sessions || []}
          completeValues={completeValues}
          onValueChange={handleCompleteValue}
          onComplete={handleComplete}
          savingSessionId={savingSessionId}
        />
      ) : (
        <HistoryTable rows={dashboard?.history || []} />
      )}
    </section>
  );
}
