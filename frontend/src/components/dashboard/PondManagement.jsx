import React, { useEffect, useMemo, useState } from 'react';

import { createPond, deletePond, getPonds, updatePond } from '../../lib/api';
import './PondManagement.css';

const WATER_SOURCE_OPTIONS = [
  { value: 'mixed', label: 'Mixed' },
  { value: 'rainwater', label: 'Rainwater' },
  { value: 'river', label: 'River' },
  { value: 'deep_tubewell', label: 'Deep tubewell' },
  { value: 'canal', label: 'Canal' },
];

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'inactive', label: 'Inactive' },
];

const EMPTY_FORM = {
  name: '',
  location: '',
  area_decimal: '',
  average_depth_ft: '',
  water_source: 'mixed',
  stocking_capacity: '',
  status: 'active',
  notes: '',
};

function formatNumber(value, suffix = '') {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  return `${Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })}${suffix}`;
}

function GaugeWave() {
  return (
    <svg className="pw-gauge-wave" viewBox="0 0 200 46" preserveAspectRatio="none" aria-hidden="true">
      <path
        d="M0 30 C 25 10, 50 10, 75 25 S 125 40, 150 22 S 190 8, 200 18 V46 H0 Z"
        fill="var(--pw-aqua-soft)"
      />
    </svg>
  );
}

export function PondManagement({ openOnMount = false }) {
  const [ponds, setPonds] = useState([]);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [editingPondId, setEditingPondId] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(openOnMount);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');

  const totalCapacity = useMemo(
    () => ponds.reduce((sum, pond) => sum + Number(pond.stocking_capacity || 0), 0),
    [ponds],
  );

  const maxCapacity = useMemo(
    () => ponds.reduce((max, pond) => Math.max(max, Number(pond.stocking_capacity || 0)), 0),
    [ponds],
  );

  useEffect(() => {
    let isMounted = true;

    async function loadPonds() {
      setIsLoading(true);
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
          setIsLoading(false);
        }
      }
    }

    loadPonds();

    return () => {
      isMounted = false;
    };
  }, []);

  function openCreateForm() {
    setEditingPondId(null);
    setFormData(EMPTY_FORM);
    setFormError('');
    setIsFormOpen(true);
  }

  function openEditForm(pond) {
    setEditingPondId(pond.id);
    setFormData({
      name: pond.name || '',
      location: pond.location || '',
      area_decimal: pond.area_decimal || '',
      average_depth_ft: pond.average_depth_ft || '',
      water_source: pond.water_source || 'mixed',
      stocking_capacity: pond.stocking_capacity || '',
      status: pond.status || 'active',
      notes: pond.notes || '',
    });
    setFormError('');
    setIsFormOpen(true);
  }

  function closeForm() {
    setEditingPondId(null);
    setFormData(EMPTY_FORM);
    setFormError('');
    setIsFormOpen(false);
  }

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setFormError('');

    try {
      const payload = {
        ...formData,
        area_decimal: formData.area_decimal,
        average_depth_ft: formData.average_depth_ft,
        stocking_capacity: Number(formData.stocking_capacity),
      };
      const pond = editingPondId
        ? await updatePond(editingPondId, payload)
        : await createPond(payload);

      setPonds(current => {
        const next = editingPondId
          ? current.map(item => (item.id === pond.id ? pond : item))
          : [...current, pond];

        return next.sort((a, b) => a.name.localeCompare(b.name));
      });
      closeForm();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(pond) {
    const shouldDelete = window.confirm(`Delete ${pond.name}?`);
    if (!shouldDelete) {
      return;
    }

    try {
      await deletePond(pond.id);
      setPonds(current => current.filter(item => item.id !== pond.id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="pw-module" aria-labelledby="pond-management-title">
      <div className="pw-header">
        <div>
          <p className="pw-kicker">Pond module</p>
          <h1 id="pond-management-title">Pond Management</h1>
        </div>
        <button
          type="button"
          className="pw-btn pw-btn-primary"
          onClick={isFormOpen ? closeForm : openCreateForm}
        >
          {isFormOpen ? 'Close form' : '+ Add pond'}
        </button>
      </div>

      <div className="pw-gauges" aria-label="Pond summary">
        <div className="pw-gauge">
          <GaugeWave />
          <p className="pw-gauge-label">Total ponds</p>
          <strong className="pw-gauge-value">{ponds.length}</strong>
        </div>
        <div className="pw-gauge">
          <GaugeWave />
          <p className="pw-gauge-label">Active ponds</p>
          <strong className="pw-gauge-value">
            {ponds.filter(pond => pond.status === 'active').length}
          </strong>
        </div>
        <div className="pw-gauge">
          <GaugeWave />
          <p className="pw-gauge-label">Stocking capacity</p>
          <strong className="pw-gauge-value">{totalCapacity.toLocaleString()}</strong>
        </div>
      </div>

      {error && <div className="pw-alert">{error}</div>}

      {isFormOpen && (
        <form className="pw-form-panel" onSubmit={handleSubmit}>
          <div className="pw-form-panel-header">
            {editingPondId ? 'Edit pond record' : 'New pond record'}
          </div>

          <div className="pw-form-grid">
            <label className="pw-field">
              <span>Pond name</span>
              <input
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Purba Madhnagar"
                required
              />
            </label>

            <label className="pw-field">
              <span>Location</span>
              <input
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="Natore"
                required
              />
            </label>

            <label className="pw-field">
              <span>Area (decimal)</span>
              <input
                name="area_decimal"
                type="number"
                min="0.01"
                step="0.01"
                value={formData.area_decimal}
                onChange={handleChange}
                required
              />
            </label>

            <label className="pw-field">
              <span>Avg depth (ft)</span>
              <input
                name="average_depth_ft"
                type="number"
                min="0.01"
                step="0.01"
                value={formData.average_depth_ft}
                onChange={handleChange}
                required
              />
            </label>

            <label className="pw-field">
              <span>Water source</span>
              <select name="water_source" value={formData.water_source} onChange={handleChange}>
                {WATER_SOURCE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>

            <label className="pw-field">
              <span>Status</span>
              <select name="status" value={formData.status} onChange={handleChange}>
                {STATUS_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>

            <label className="pw-field">
              <span>Stocking capacity</span>
              <input
                name="stocking_capacity"
                type="number"
                min="1"
                step="1"
                value={formData.stocking_capacity}
                onChange={handleChange}
                required
              />
            </label>

            <label className="pw-field pw-field-notes">
              <span>Notes</span>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows="3"
                placeholder="Optional pond details"
              />
            </label>
          </div>

          {formError && <div className="pw-alert">{formError}</div>}

          <div className="pw-form-actions">
            <button type="button" className="pw-btn pw-btn-secondary" onClick={closeForm}>
              Cancel
            </button>
            <button type="submit" className="pw-btn pw-btn-primary" disabled={isSaving}>
              {isSaving ? 'Saving...' : editingPondId ? 'Update pond' : 'Save pond'}
            </button>
          </div>
        </form>
      )}

      <div className="pw-table-card">
        {isLoading ? (
          <div className="pw-table-state">Loading ponds...</div>
        ) : ponds.length === 0 ? (
          <div className="pw-table-state">No ponds recorded yet.</div>
        ) : (
          <div className="pw-table-scroll">
            <table className="pw-data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Location</th>
                  <th>Area</th>
                  <th>Depth</th>
                  <th>Source</th>
                  <th>Capacity</th>
                  <th>Status</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {ponds.map(pond => {
                  const capacity = Number(pond.stocking_capacity || 0);
                  const fillPercent = maxCapacity > 0 ? Math.round((capacity / maxCapacity) * 100) : 0;

                  return (
                    <tr key={pond.id}>
                      <td>
                        <span className="pw-pond-name">{pond.name}</span>
                        {pond.notes && <span className="pw-pond-notes">{pond.notes}</span>}
                      </td>
                      <td>{pond.location}</td>
                      <td className="pw-num">{formatNumber(pond.area_decimal)}</td>
                      <td className="pw-num">{formatNumber(pond.average_depth_ft, ' ft')}</td>
                      <td>{pond.water_source_display}</td>
                      <td>
                        <div className="pw-capacity-cell">
                          <span className="pw-num">{formatNumber(pond.stocking_capacity)}</span>
                          <div className="pw-capacity-bar">
                            <div className="pw-capacity-fill" style={{ width: `${fillPercent}%` }} />
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`pw-status-pill pw-status-${pond.status}`}>
                          {pond.status_display}
                        </span>
                      </td>
                      <td>
                        <div className="pw-row-actions">
                          <button
                            type="button"
                            className="pw-icon-btn"
                            onClick={() => openEditForm(pond)}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="pw-icon-btn pw-icon-btn-danger"
                            onClick={() => handleDelete(pond)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
