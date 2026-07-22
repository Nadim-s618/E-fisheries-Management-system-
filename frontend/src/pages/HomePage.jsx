import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../context/useAuth';
import { getHomepage } from '../lib/api';
import './HomePage.css';

const FEATURE_ICONS = {
  water: '🌊',
  feed: '🐟',
  growth: '📊',
  health: '🏥',
  weather: '🌤️',
  finance: '💰',
  market: '📈',
  bridge: '🤝',
};

export default function HomePage() {
  const [content, setContent] = useState(null);
  const [loadError, setLoadError] = useState('');
  const { user, logout } = useAuth();
  const heroLead = content?.hero.title.replace(content.hero.accent, '').trim();

  function getNavTarget(link) {
    if (link.toLowerCase() === 'dashboard') {
      return '/dashboard';
    }

    return `#${link.toLowerCase()}`;
  }

  useEffect(() => {
    let isMounted = true;

    getHomepage()
      .then(data => {
        if (isMounted) {
          setContent(data);
          setLoadError('');
        }
      })
      .catch(() => {
        if (isMounted) {
          setLoadError('Homepage content is unavailable right now.');
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (!content) {
    return (
      <div className="homepage">
        <nav className="navbar">
          <div className="navbar-inner">
            <span className="logo">
              <span className="logo-icon">🐠</span>
              E-Fisheries
            </span>
            <Link to="/login" className="btn-nav">Sign In</Link>
          </div>
        </nav>
        <main className="homepage-status" role={loadError ? 'alert' : 'status'}>
          <h1>{loadError || 'Loading E-Fisheries...'}</h1>
          {loadError && <p>Please check that the backend server is running.</p>}
        </main>
      </div>
    );
  }

  return (
    <div className="homepage">

      {/* ── Navbar ── */}
      <nav className="navbar">
        <div className="navbar-inner">
          <span className="logo">
            <span className="logo-icon">🐠</span>
            E-Fisheries
          </span>
          <ul className="nav-links">
            {content.navLinks.map(link => (
              <li key={link}>
                {link.toLowerCase() === 'dashboard' ? (
                  <Link to={getNavTarget(link)}>{link}</Link>
                ) : (
                  <a href={getNavTarget(link)}>{link}</a>
                )}
              </li>
            ))}
          </ul>
          {user ? (
            <div className="nav-auth">
              <span className="nav-user">Hi, {user.first_name || user.username}</span>
              <Link to="/dashboard" className="btn-nav">Dashboard</Link>
              <button type="button" className="btn-nav" onClick={logout}>Sign Out</button>
            </div>
          ) : (
            <Link to="/login" className="btn-nav">Sign In</Link>
          )}
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero" id="home">
        <div className="hero-overlay" />
        <div className="hero-inner">
          <span className="hero-eyebrow">{content.hero.eyebrow}</span>
          <h1 className="hero-title">
            {heroLead}<br />
            <span className="hero-accent">{content.hero.accent}</span>
          </h1>
          <p className="hero-sub">
            {content.hero.subtitle}
          </p>
          <div className="hero-actions">
            <Link to="/signup" className="btn-primary">Get started free</Link>
            <a href="#features" className="btn-ghost">See all features ↓</a>
          </div>
        </div>

        {/* Decorative wave */}
        <div className="hero-wave" aria-hidden="true">
          <svg viewBox="0 0 1440 80" preserveAspectRatio="none">
            <path d="M0,40 C360,80 1080,0 1440,40 L1440,80 L0,80 Z" fill="white" />
          </svg>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="stats-bar">
        {content.stats.map(s => (
          <div className="stat-item" key={s.label}>
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </section>

      {/* ── Features ── */}
      <section className="features-section" id="features">
        <div className="section-inner">
          <p className="section-eyebrow">What's included</p>
          <h2 className="section-title">Everything your fishery needs</h2>
          <p className="section-sub">
            From individual farmers to large investors, E-Fisheries covers every
            operational layer of a modern fisheries business.
          </p>
          <div className="features-grid">
            {content.features.map(f => (
              <div className="feature-card" key={f.title}>
                <span className="feature-icon" aria-hidden="true">{FEATURE_ICONS[f.icon] || f.icon}</span>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section className="cta-section">
        <div className="cta-inner">
          <h2>{content.cta.title}</h2>
          <p>{content.cta.subtitle}</p>
          <Link to="/signup" className="btn-primary btn-large">{content.cta.buttonText}</Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="footer">
        <div className="footer-inner">
          <span className="logo logo-footer">
            <span className="logo-icon">🐠</span>
            E-Fisheries
          </span>
          <p className="footer-copy">© 2026 E-Fisheries. E-Fisheries Management System.</p>
          <ul className="footer-links">
            <li><a href="#features">Features</a></li>
            <li><a href="#about">About</a></li>
            <li><Link to="/login">Sign in</Link></li>
          </ul>
        </div>
      </footer>

    </div>
  );
}
