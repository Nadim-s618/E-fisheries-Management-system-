import React, { useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../context/useAuth';
import { updateUserProfile } from '../lib/api';
import './ProfilePage.css';

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    full_name: user?.full_name || `${user?.first_name || ''} ${user?.last_name || ''}`.trim(),
    email: user?.email || '',
    address: user?.address || '',
    new_password: '',
    confirm_password: '',
  });
  const [picture, setPicture] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  function updateField(event) {
    const { name, value } = event.target;
    setForm(current => ({ ...current, [name]: value }));
  }

  async function submitProfile(event) {
    event.preventDefault();
    setSaving(true);
    setMessage('');
    setError('');

    const payload = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      if (value) payload.append(key, value);
    });
    if (picture) payload.append('profile_picture', picture);

    try {
      const response = await updateUserProfile(payload);
      updateUser(response.user);
      setForm(current => ({ ...current, new_password: '', confirm_password: '' }));
      setPicture(null);
      event.target.reset();
      setMessage('Profile updated successfully.');
    } catch (saveError) {
      setError(saveError.message || 'Unable to update profile.');
    } finally {
      setSaving(false);
    }
  }

  const avatar = user?.profile_picture_url;
  const initial = (user?.first_name || 'P').charAt(0).toUpperCase();

  return (
    <main className="profile-page">
      <header className="profile-page-header">
        <Link to="/dashboard" className="profile-brand">E-Fisheries</Link>
        <Link to="/dashboard" className="profile-back-link">← Back to dashboard</Link>
      </header>

      <section className="profile-card" aria-labelledby="profile-title">
        <div className="profile-card-heading">
          <div>
            <span className="profile-kicker">Account</span>
            <h1 id="profile-title">My Profile</h1>
            <p>Update your personal details and account password.</p>
          </div>
          <div className="profile-avatar-large">
            {avatar ? <img src={avatar} alt="Current profile" /> : initial}
          </div>
        </div>

        {message && <div className="profile-message profile-message-success" role="status">{message}</div>}
        {error && <div className="profile-message profile-message-error" role="alert">{error}</div>}

        <form onSubmit={submitProfile}>
          <label className="profile-field profile-picture-field">
            <span>Profile picture</span>
            <input type="file" accept="image/*" onChange={event => setPicture(event.target.files?.[0] || null)} />
          </label>

          <div className="profile-form-grid">
            <label className="profile-field">
              <span>Full name</span>
              <input name="full_name" value={form.full_name} onChange={updateField} required />
            </label>
            <label className="profile-field">
              <span>Email address</span>
              <input name="email" type="email" value={form.email} onChange={updateField} required />
            </label>
          </div>

          <label className="profile-field">
            <span>Address</span>
            <textarea name="address" rows="3" value={form.address} onChange={updateField} placeholder="Your address" />
          </label>

          <div className="profile-password-heading">
            <h2>Change password</h2>
            <span>Leave blank to keep your current password.</span>
          </div>
          <div className="profile-form-grid">
            <label className="profile-field">
              <span>New password</span>
              <input name="new_password" type="password" minLength="8" value={form.new_password} onChange={updateField} autoComplete="new-password" />
            </label>
            <label className="profile-field">
              <span>Confirm new password</span>
              <input name="confirm_password" type="password" minLength="8" value={form.confirm_password} onChange={updateField} autoComplete="new-password" />
            </label>
          </div>

          <button type="submit" className="profile-save-button" disabled={saving}>
            {saving ? 'Saving...' : 'Save changes'}
          </button>
        </form>
      </section>
    </main>
  );
}
