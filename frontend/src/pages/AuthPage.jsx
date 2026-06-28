import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/useAuth';
import './AuthPage.css';


const INITIAL_FORM = {
  full_name: '',
  email: '',
  password: '',
  confirm_password: '',
};


export default function AuthPage({ mode = 'login' }) {
  const isSignup = mode === 'signup';
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, login, signup } = useAuth();
  const [form, setForm] = useState(INITIAL_FORM);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  function updateField(event) {
    const { name, value } = event.target;
    setForm(current => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (isSignup) {
        await signup(form);
      } else {
        await login({
          email: form.email,
          password: form.password,
        });
      }

      navigate('/dashboard');
    } catch (authError) {
      setError(authError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-shell">
        <Link to="/" className="auth-brand">
          <span className="auth-brand-mark">EF</span>
          <span>E-Fisheries</span>
        </Link>

        <section className="auth-card" aria-labelledby="auth-title">
          <p className="auth-eyebrow">{isSignup ? 'Create account' : 'Welcome back'}</p>
          <h1 id="auth-title">{isSignup ? 'Sign up' : 'Sign in'}</h1>

          <form className="auth-form" onSubmit={handleSubmit}>
            {isSignup && (
              <label>
                <span>Full name</span>
                <input
                  type="text"
                  name="full_name"
                  value={form.full_name}
                  onChange={updateField}
                  autoComplete="name"
                  required
                />
              </label>
            )}

            <label>
              <span>Email</span>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={updateField}
                autoComplete="email"
                required
              />
            </label>

            <label>
              <span>Password</span>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={updateField}
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                minLength={8}
                required
              />
            </label>

            {isSignup && (
              <label>
                <span>Confirm password</span>
                <input
                  type="password"
                  name="confirm_password"
                  value={form.confirm_password}
                  onChange={updateField}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </label>
            )}

            {error && <p className="auth-error" role="alert">{error}</p>}

            <button className="auth-submit" type="submit" disabled={isSubmitting || isLoading}>
              {isSubmitting ? 'Please wait...' : isSignup ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <p className="auth-switch">
            {isSignup ? 'Already have an account?' : 'New to E-Fisheries?'}
            {' '}
            <Link to={isSignup ? '/login' : '/signup'}>
              {isSignup ? 'Sign in' : 'Create account'}
            </Link>
          </p>
        </section>
      </div>
    </main>
  );
}
