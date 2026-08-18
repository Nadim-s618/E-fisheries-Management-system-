import React from 'react';
import { Link } from 'react-router-dom';

import homepageContent from '../data/homepage';
import './HomePage.css';

export default function HomePage() {
  const content = homepageContent;
  const heroLead = content?.hero.title.replace(content.hero.accent, '').trim();

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
                {link === 'Fish Store' ? (
                  <Link to="/fish-store">{link}</Link>
                ) : (
                  <a href={`#${link.toLowerCase().replace(/\s+/g, '-')}`}>{link}</a>
                )}
              </li>
            ))}
          </ul>
          <div className="nav-auth">
            <Link to="/signup" className="btn-nav">Sign up</Link>
            <Link to="/login" className="btn-nav">Log in</Link>
          </div>
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

        <Link to="/fish-store" className="hero-store-link">
          <span className="hero-store-image">
            <img src="/store.webp" alt="Fresh fish from the E-Fisheries store" />
          </span>
        </Link>

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
      <section className="page page-closing" id="about">
        <div className="cta-inner cta-panel">
          <span className="cta-mark" aria-hidden="true">✦</span>
          <p className="closing-eyebrow">Built for the whole fishery</p>
          <h2>{content.cta.title}</h2>
          <p className="cta-sub">{content.cta.subtitle}</p>

          <div className="cta-points" aria-label="Platform benefits">
            <span><strong>01</strong> Monitor</span>
            <span><strong>02</strong> Plan</span>
            <span><strong>03</strong> Grow</span>
          </div>

          <ul className="role-pills" aria-label="Who E-Fisheries is built for">
            <li>Farmers</li>
            <li>Pond managers</li>
            <li>Buyers</li>
          </ul>

          <div className="cta-actions">
            <Link to="/signup" className="btn-primary btn-large">{content.cta.buttonText}</Link>
            <Link to="/fish-store" className="cta-store-link">Visit Fish Store →</Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="footer" id="contact">
        <div className="footer-inner footer-grid">

          <div className="footer-col footer-brand">
            <span className="footer-kicker">A smarter way to manage your fishery</span>
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
              <li><Link to="/fish-store">Fish Store</Link></li>
              <li><a href="#about">About</a></li>
              <li><Link to="/login">Log in</Link></li>
              <li><Link to="/signup">Sign up</Link></li>
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
                <a href="mailto:supportefisheries@gmail.com">supportefisheries@gmail.com</a>
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
