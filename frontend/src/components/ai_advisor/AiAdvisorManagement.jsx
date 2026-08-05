import { useCallback, useEffect, useState } from 'react';

import { getAiAdvisor, getPonds } from '../../lib/api';
import './AiAdvisorManagement.css';

function PanelState({ type = 'empty', children }) {
  return <div className={`aim-state aim-state-${type}`}>{children}</div>;
}

function AdviceList({ title, items }) {
  if (!items?.length) return null;

  return (
    <section className="aim-panel">
      <div className="aim-panel-header">
        <span>{title}</span>
      </div>
      <ul className="aim-list">
        {items.map(item => <li key={item}>{item}</li>)}
      </ul>
    </section>
  );
}

export default function AiAdvisorManagement() {
  const [ponds, setPonds] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [advice, setAdvice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadPonds() {
      try {
        const data = await getPonds();
        if (!active) return;
        setPonds(data || []);
        setSelectedPondId(data?.[0]?.id ? String(data[0].id) : '');
      } catch (err) {
        if (active) setError(err.message);
      }
    }

    loadPonds();

    return () => {
      active = false;
    };
  }, []);

  const loadAdvice = useCallback(async (pondId = selectedPondId) => {
    if (!pondId) return;
    setLoading(true);
    setError('');

    try {
      const data = await getAiAdvisor(pondId);
      setAdvice(data);
    } catch (err) {
      setAdvice(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedPondId]);

  useEffect(() => {
    if (!selectedPondId) return undefined;
    const timer = window.setTimeout(() => loadAdvice(selectedPondId), 0);
    return () => window.clearTimeout(timer);
  }, [loadAdvice, selectedPondId]);

  return (
    <section className="aim-root" aria-labelledby="ai-advisor-title">
      <div className="aim-header">
        <div>
          <span>AI Advisor</span>
          <h1 id="ai-advisor-title">General Pond Recommendation</h1>
        </div>
        <label className="aim-field">
          <span>Pond</span>
          <select value={selectedPondId} onChange={event => setSelectedPondId(event.target.value)}>
            {ponds.length === 0 ? <option value="">No ponds</option> : ponds.map(pond => (
              <option key={pond.id} value={pond.id}>{pond.name}</option>
            ))}
          </select>
        </label>
      </div>

      {!ponds.length ? (
        <PanelState>Add a pond before generating AI recommendations.</PanelState>
      ) : loading ? (
        <PanelState>Loading AI recommendation...</PanelState>
      ) : error ? (
        <PanelState type="error">{error}</PanelState>
      ) : advice ? (
        <div className="aim-stack">
          <section className="aim-summary">
            <div>
              <span>{advice.ai_enabled ? 'Gemini AI' : 'Fallback Advisor'}</span>
              <h2>{advice.priority || 'Normal'}</h2>
            </div>
            <p>{advice.summary}</p>
          </section>
          <AdviceList title="Recommendations" items={advice.recommendations} />
          <AdviceList title="Risks" items={advice.risks} />
          <AdviceList title="Next Actions" items={advice.next_actions} />
        </div>
      ) : (
        <PanelState>Select a pond to generate advice.</PanelState>
      )}
    </section>
  );
}
