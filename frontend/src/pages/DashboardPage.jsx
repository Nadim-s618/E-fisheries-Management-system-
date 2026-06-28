import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import './DashboardPage.css';

const NAV_ITEMS = [
  { id: 'water',    label: 'Water Quality',      icon: 'M12 2C8 6 4 9 4 13a8 8 0 0016 0c0-4-4-7-8-11z' },
  { id: 'feeding',  label: 'Fish Feeding',        icon: 'M3 12h18M3 6l9-3 9 3M3 18l9 3 9-3' },
  { id: 'health',   label: 'Fish Health',         icon: 'M12 21C7 17 3 13.5 3 9a5 5 0 0110 0 5 5 0 0110 0c0 4.5-4 8-9 12z' },
  { id: 'stock',    label: 'Stock & Growth',      icon: 'M3 20l4-8 4 4 4-6 4 10' },
  { id: 'weather',  label: 'Weather',             icon: 'M12 3v1m0 16v1M4.22 4.22l.7.7m12.16 12.16l.7.7M1 12h1m18 0h1M4.22 19.78l.7-.7M18.36 5.64l.7-.7M12 7a5 5 0 100 10A5 5 0 0012 7z' },
  { id: 'finance',  label: 'Financials',          icon: 'M12 2v20M17 5H9.5a3.5 3.5 0 100 7h5a3.5 3.5 0 110 7H6' },
  { id: 'expert',   label: 'Expert Consultation', icon: 'M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a2 2 0 01-2-2v-6a2 2 0 012-2h8zM7 8V6a2 2 0 012-2h8a2 2 0 012 2v2' },
  { id: 'market',   label: 'Market Bridge',       icon: 'M3 6h18M3 12h18M3 18h12' },
  { id: 'analysis', label: 'Market Analysis',     icon: 'M18 20V10M12 20V4M6 20v-6' },
];

const ALERTS = [
  { pond: 'Purba Madhnagar', issue: 'High oxygen level' },
  { pond: 'Dighi',           issue: 'Low pH level' },
];

const STATS = [
  { label: 'Total Ponds',     value: '5',        sub: '4 healthy',        accent: 'teal'  },
  { label: 'Total Fish',      value: '2,000',    sub: 'across all ponds', accent: 'blue'  },
  { label: 'Avg Temperature', value: '21.7°C',   sub: 'within range',     accent: 'amber' },
  { label: 'Avg Oxygen',      value: '8.1 mg/L', sub: 'optimal',          accent: 'green' },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeNav, setActiveNav] = useState('water');

  async function handleLogout() {
    await logout();
    navigate('/');
  }

  return (
    <div className="dp-root">

      {/* Top Navbar */}
      <header className="dp-navbar">
        <Link to="/" className="dp-logo">
          <div className="dp-logo-mark">
            <svg viewBox="0 0 32 32" fill="none">
              <circle cx="16" cy="16" r="14" fill="#2D6A4F" opacity="0.15"/>
              <path d="M8 20c2-4 4-6 8-6s6 2 8 6" stroke="#2D6A4F" strokeWidth="2" strokeLinecap="round"/>
              <ellipse cx="13" cy="17" rx="2" ry="1.2" fill="#52B788" opacity="0.7"/>
              <ellipse cx="20" cy="17" rx="1.5" ry="1" fill="#52B788" opacity="0.5"/>
              <circle cx="16" cy="13" r="1" fill="#2D6A4F" opacity="0.4"/>
            </svg>
          </div>
          <div className="dp-logo-text">
            <span className="dp-logo-name">e-Fisheries</span>
            <span className="dp-logo-sub">Management System</span>
          </div>
        </Link>

        <nav className="dp-nav-links">
          <a href="#" className="dp-nav-link">Home</a>
          <a href="#" className="dp-nav-link">Pond</a>
          <a href="#" className="dp-nav-link">Tips</a>
        </nav>

        <div className="dp-nav-right">
          <button className="dp-icon-btn" aria-label="Search">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
          </button>
          <button className="dp-icon-btn" aria-label="Notifications" style={{ position: 'relative' }}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/>
            </svg>
            <span className="dp-notif-dot" aria-hidden="true" />
          </button>
          <button className="dp-profile-btn" onClick={handleLogout}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z"/>
            </svg>
            <span>{user?.first_name || 'profile'}</span>
          </button>
        </div>
      </header>

      <div className="dp-body">

        {/* Icon Sidebar */}
        <aside className="dp-sidebar" aria-label="Module navigation">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              type="button"
              className={`dp-sidebar-item ${activeNav === item.id ? 'active' : ''}`}
              onClick={() => setActiveNav(item.id)}
              title={item.label}
              aria-label={item.label}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d={item.icon} />
              </svg>
              <span className="dp-sidebar-label">{item.label}</span>
            </button>
          ))}
        </aside>

        {/* Main Content */}
        <main className="dp-main">

          {/* Alert Banner */}
          <section className="dp-alert-banner" aria-label="Active alerts">
            <div className="dp-alert-header">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#C0392B" strokeWidth="2" strokeLinecap="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <span>Alerts</span>
            </div>
            <div className="dp-alert-rows">
              {ALERTS.map((a, i) => (
                <div className="dp-alert-row" key={i}>
                  <span className="dp-alert-pond">{a.pond}</span>
                  <span className="dp-alert-sep">:</span>
                  <span className="dp-alert-issue">{a.issue}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Stat Cards */}
          <div className="dp-stats-grid">
            {STATS.map(s => (
              <article className={`dp-stat-card dp-stat-${s.accent}`} key={s.label}>
                <p className="dp-stat-label">{s.label}</p>
                <p className="dp-stat-value">{s.value}</p>
                <p className="dp-stat-sub">{s.sub}</p>
              </article>
            ))}
          </div>

          {/* Hero */}
          <section className="dp-hero">
            <div className="dp-hero-text">
              <h1>Welcome to E-Fisheries<br/>Management System</h1>
              <p>
                Efficient fish farming starts with accurate monitoring.
                Keep your pond records updated, monitor water quality,
                and track fish growth regularly to maximize production and profitability.
              </p>
              <div className="dp-hero-actions">
                <button type="button" className="dp-btn-primary">View all ponds</button>
                <button type="button" className="dp-btn-secondary">Add water test</button>
              </div>
            </div>

            <div className="dp-hero-art" aria-hidden="true">
              <svg viewBox="0 0 440 270" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Background glow / sky */}
                <ellipse cx="220" cy="120" rx="180" ry="90" fill="#B7DFD0" opacity="0.18"/>

                {/* Water body layers */}
                <ellipse cx="220" cy="210" rx="200" ry="56" fill="#B7DFD0" opacity="0.4"/>
                <ellipse cx="220" cy="210" rx="170" ry="44" fill="#74C69D" opacity="0.28"/>
                <ellipse cx="220" cy="210" rx="135" ry="31" fill="#52B788" opacity="0.22"/>

                {/* Ripple rings */}
                <ellipse cx="220" cy="210" rx="82"  ry="19" stroke="#2D6A4F" strokeWidth="1"    opacity="0.18"/>
                <ellipse cx="220" cy="210" rx="115" ry="27" stroke="#2D6A4F" strokeWidth="0.75" opacity="0.11"/>
                <ellipse cx="220" cy="210" rx="152" ry="38" stroke="#2D6A4F" strokeWidth="0.5"  opacity="0.07"/>

                {/* Reeds — left */}
                <line x1="52"  y1="232" x2="44"  y2="160" stroke="#1B4332" strokeWidth="2.2" strokeLinecap="round" opacity="0.5"/>
                <line x1="64"  y1="238" x2="74"  y2="168" stroke="#1B4332" strokeWidth="1.6" strokeLinecap="round" opacity="0.38"/>
                <ellipse cx="44"  cy="154" rx="6"  ry="15" fill="#2D6A4F" opacity="0.38"/>
                <ellipse cx="74"  cy="162" rx="5"  ry="12" fill="#40916C" opacity="0.3"/>
                <ellipse cx="58"  cy="158" rx="4"  ry="10" fill="#52B788" opacity="0.22"/>

                {/* Reeds — right */}
                <line x1="390" y1="228" x2="384" y2="164" stroke="#1B4332" strokeWidth="2.2" strokeLinecap="round" opacity="0.45"/>
                <line x1="376" y1="234" x2="368" y2="170" stroke="#1B4332" strokeWidth="1.6" strokeLinecap="round" opacity="0.35"/>
                <ellipse cx="384" cy="158" rx="6"  ry="14" fill="#2D6A4F" opacity="0.33"/>
                <ellipse cx="368" cy="165" rx="4.5" ry="11" fill="#40916C" opacity="0.25"/>

                {/* Lily pads */}
                <ellipse cx="102" cy="220" rx="20" ry="7.5" fill="#40916C" opacity="0.38"/>
                <path d="M102 220 L102 212" stroke="#40916C" strokeWidth="1" opacity="0.4"/>
                <ellipse cx="340" cy="218" rx="16" ry="6"   fill="#40916C" opacity="0.32"/>
                <path d="M340 218 L340 211" stroke="#40916C" strokeWidth="1" opacity="0.35"/>

                {/* Main fish — large, left-swimming */}
                <g transform="translate(145,198)">
                  <ellipse cx="0" cy="0" rx="30" ry="11" fill="#1B4332" opacity="0.88"/>
                  <path d="M30 0 L46 -10 L41 0 L46 10 Z" fill="#1B4332" opacity="0.88"/>
                  <circle cx="-20" cy="-3.5" r="3" fill="#D8F3DC"/>
                  <path d="M-5 -4 Q0 0 -5 4" stroke="#D8F3DC" strokeWidth="0.75" opacity="0.3"/>
                </g>

                {/* Second fish — mid, teal */}
                <g transform="translate(286,204) scale(0.7)">
                  <ellipse cx="0" cy="0" rx="30" ry="11" fill="#40916C" opacity="0.85"/>
                  <path d="M30 0 L46 -10 L41 0 L46 10 Z" fill="#40916C" opacity="0.85"/>
                  <circle cx="-20" cy="-3.5" r="3" fill="#D8F3DC"/>
                </g>

                {/* Third fish — tiny, opposite direction */}
                <g transform="translate(192,216) scale(-0.42,0.42)">
                  <ellipse cx="0" cy="0" rx="30" ry="11" fill="#52B788" opacity="0.7"/>
                  <path d="M30 0 L46 -10 L41 0 L46 10 Z" fill="#52B788" opacity="0.7"/>
                  <circle cx="-20" cy="-3.5" r="2.5" fill="#D8F3DC"/>
                </g>

                {/* Oxygen / bubbles */}
                <circle cx="162" cy="183" r="4"   stroke="#52B788" strokeWidth="1.2" opacity="0.5"/>
                <circle cx="170" cy="170" r="2.8" stroke="#52B788" strokeWidth="1"   opacity="0.35"/>
                <circle cx="176" cy="160" r="2"   stroke="#74C69D" strokeWidth="0.9" opacity="0.22"/>
                <circle cx="256" cy="187" r="4.5" stroke="#52B788" strokeWidth="1.2" opacity="0.45"/>
                <circle cx="263" cy="173" r="3"   stroke="#52B788" strokeWidth="1"   opacity="0.3"/>
                <circle cx="220" cy="178" r="3.5" stroke="#74C69D" strokeWidth="1"   opacity="0.38"/>
                <circle cx="226" cy="166" r="2.2" stroke="#74C69D" strokeWidth="0.8" opacity="0.23"/>

                {/* Water probe / sensor */}
                <rect x="212" y="162" width="5" height="44" rx="2.5" fill="#40916C" opacity="0.7"/>
                <rect x="205" y="158" width="18" height="10" rx="4" fill="#1B4332" opacity="0.8"/>
                <circle cx="214.5" cy="163" r="2.5" fill="#D8F3DC" opacity="0.9"/>

                {/* Sensor readout chip */}
                <rect x="226" y="142" width="76" height="30" rx="7" fill="#1B4332" opacity="0.85"/>
                <text x="264" y="153" textAnchor="middle" fill="#D8F3DC" fontSize="8.5" fontFamily="system-ui,sans-serif" opacity="0.95">pH 7.2 · 21.7 °C</text>
                <text x="264" y="165" textAnchor="middle" fill="#74C69D"  fontSize="7.5" fontFamily="system-ui,sans-serif" opacity="0.8">O₂  8.1 mg/L</text>
                {/* Dashed connector to probe */}
                <line x1="214" y1="158" x2="229" y2="157" stroke="#74C69D" strokeWidth="0.8" strokeDasharray="2.5 2" opacity="0.45"/>
              </svg>
            </div>
          </section>

        </main>
      </div>
    </div>
  );
}