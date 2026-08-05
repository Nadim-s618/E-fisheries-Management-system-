import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../context/useAuth';
import { getHomepage } from '../lib/api';
import './HomePage.css';

export default function HomePage() {
  const [content, setContent] = useState(null);
  const [loadError, setLoadError] = useState('');
  const { user, logout } = useAuth();
  const heroLead = content?.hero.title.replace(content.hero.accent, '').trim();

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
              <img src="/logo.png" alt="E-Fisheries logo" className="logo-icon" />
              <span className="logo-text">
                <span className="logo-name">E-Fisheries</span>
                <span className="logo-sub">Management System</span>
              </span>
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
            <img src="/logo.png" alt="E-Fisheries logo" className="logo-icon" />
            <span className="logo-text">
              <span className="logo-name">E-Fisheries</span>
              <span className="logo-sub">Management System</span>
            </span>
          </span>
          <ul className="nav-links">
            {content.navLinks.map(link => (
              <li key={link}>
                <a href={`#${link.toLowerCase()}`}>{link}</a>
              </li>
            ))}
          </ul>
          {user ? (
            <div className="nav-auth">
              <span className="nav-user">Hi, {user.first_name || user.username}</span>
              <button type="button" className="btn-nav" onClick={logout}>Sign Out</button>
            </div>
          ) : (
            <Link to="/login" className="btn-nav">Sign In</Link>
          )}
        </div>
      </nav>

      {/* ══════════════ PAGE 1 — Hero + Stats ══════════════ */}
      <section className="page page-hero" id="home">
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

        <div className="stats-strip">
          {content.stats.map(s => (
            <div className="stat-item" key={s.label}>
              <span className="stat-value">{s.value}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════════ PAGE 2 — Features ══════════════ */}
      <section className="page page-features" id="features">
        <div className="section-inner">
          <p className="section-eyebrow">What's included</p>
          <h2 className="section-title">Everything your fishery needs</h2>
          <div className="section-dots" aria-hidden="true">
            <span /><span /><span />
          </div>
          <p className="section-sub">
            From individual farmers to large investors, E-Fisheries covers every
            operational layer of a modern fisheries business.
          </p>
          <div className="features-grid">
            {content.features.map((f, index) => (
              <div className="feature-card" key={f.title}>
                <div className="feature-media">
                  <img
                    src={`/feature-${index + 1}.png`}
                    alt=""
                    aria-hidden="true"
                    className="feature-image"
                  />
                </div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════ PAGE 3 — Closing / CTA ══════════════ */}
      <section className="page page-closing">
        <div className="cta-inner">
          <p className="closing-eyebrow">Built for the whole fishery</p>
          <h2>{content.cta.title}</h2>
          <p className="cta-sub">{content.cta.subtitle}</p>

          <ul className="role-pills" aria-label="Who E-Fisheries is built for">
            <li>Farmers</li>
            <li>Pond managers</li>
            <li>Investors</li>
            <li>Consultants</li>
          </ul>

          <Link to="/signup" className="btn-primary btn-large">{content.cta.buttonText}</Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="footer">
        <div className="footer-inner footer-grid">

          <div className="footer-col footer-brand">
            <span className="logo logo-footer">
              <img src="/logo.png" alt="E-Fisheries logo" className="logo-icon" />
              <span className="logo-text">
                <span className="logo-name">E-Fisheries</span>
                <span className="logo-sub">Management System</span>
              </span>
            </span>
            <p className="footer-tagline">
              A complete platform for fish farmers, pond managers, investors,
              and consultants to monitor, plan, and grow their operations.
            </p>
          </div>

          <div className="footer-col">
            <h4 className="footer-heading">Quick Links</h4>
            <ul className="footer-links">
              <li><a href="#home">Home</a></li>
              <li><a href="#features">Features</a></li>
              <li><a href="#about">About</a></li>
              {!user && (
                <>
                  <li><Link to="/login">Sign in</Link></li>
                  <li><Link to="/signup">Sign up</Link></li>
                </>
              )}
            </ul>
          </div>

          <div className="footer-col">
            <h4 className="footer-heading">Resources</h4>
            <ul className="footer-links">
              <li><a href="#features">Water Quality Monitoring</a></li>
              <li><a href="#features">Feeding Management</a></li>
              <li><a href="#features">Pond &amp; Stock Tracking</a></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4 className="footer-heading">Contact</h4>
            <ul className="footer-contact">
              <li>
                <a href="mailto:support@efisheries.example">support@efisheries.example</a>
              </li>
              <li>Dhaka, Bangladesh</li>
            </ul>
          </div>

        </div>

        <div className="footer-bottom">
          <p className="footer-copy">© 2026 E-Fisheries. All rights reserved.</p>
          <ul className="footer-legal">
            <li><a href="#privacy">Privacy Policy</a></li>
            <li><a href="#terms">Terms of Service</a></li>
          </ul>
        </div>
      </footer>

    </div>
  );
}