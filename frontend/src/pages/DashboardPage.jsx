import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DashboardSidebar } from '../components/dashboard/DashboardSidebar';
import { DashboardSummary } from '../components/dashboard/DashboardSummary';
import { DashboardTopbar } from '../components/dashboard/DashboardTopbar';
import { PondManagement } from '../components/dashboard/PondManagement';
import { StockGrowthManagement } from '../components/dashboard/StockGrowthManagement';
import FishHealthManagement from '../components/fish_health/FishHealthManagement';
import FinancialManagement from '../components/financials/FinancialManagement';
import MarketAnalysis from '../components/market_analysis/MarketAnalysis';
import MarketBridge from '../components/market_bridge/MarketBridge';
import FeedingManagement from '../components/feeding/FeedingManagement';
import WeatherManagement from '../components/weather/WeatherManagement';
import WaterQualityManagement from '../components/water_quality/WaterQualityManagement';
import { useAuth } from '../context/useAuth';
import { getNotifications, markNotificationRead, markNotificationsRead } from '../lib/api';
import {
  DASHBOARD_NAV_ITEMS,
  DASHBOARD_STATS,
} from '../data/dashboard';
import './DashboardPage.css';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeNav, setActiveNav] = useState('water');
  const [pondFormOpenSignal, setPondFormOpenSignal] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);

  const loadNotifications = useCallback(async () => {
    if (!user) {
      setNotifications([]);
      return;
    }

    setNotificationsLoading(true);
    try {
      const data = await getNotifications({ unread: true, limit: 20 });
      setNotifications(data || []);
    } catch {
      setNotifications([]);
    } finally {
      setNotificationsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    const timer = window.setTimeout(loadNotifications, 0);

    if (!user) {
      return () => window.clearTimeout(timer);
    }

    const interval = window.setInterval(loadNotifications, 30000);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(interval);
    };
  }, [loadNotifications, user]);

  async function handleLogout() {
    await logout();
    setNotifications([]);
    navigate('/');
  }

  function handleAddPond() {
    setActiveNav('ponds');
    setPondFormOpenSignal(current => current + 1);
  }

  function handleViewPonds() {
    setActiveNav('ponds');
  }

  async function handleNotificationRead(notification) {
    if (!notification?.id) return;

    setNotifications(current => current.filter(item => item.id !== notification.id));
    try {
      await markNotificationRead(notification.id);
    } catch {
      loadNotifications();
    }
  }

  async function handleNotificationsRead() {
    const previousNotifications = notifications;
    setNotifications([]);
    try {
      await markNotificationsRead();
    } catch {
      setNotifications(previousNotifications);
    }
  }

  const summaryAlerts = notifications.map(notification => ({
    pond: notification.pond_name || notification.pond,
    issue: notification.parameter,
  }));

  return (
    <div className="dp-root">
      <DashboardTopbar
        onPondsClick={handleViewPonds}
        onNotificationClick={loadNotifications}
        onNotificationRead={handleNotificationRead}
        onNotificationsRead={handleNotificationsRead}
        user={user}
        notifications={notifications}
        notificationsLoading={notificationsLoading}
      />

      <div className="dp-body">
        <DashboardSidebar
          activeNav={activeNav}
          navItems={DASHBOARD_NAV_ITEMS}
          onAddPond={handleAddPond}
          onNavChange={setActiveNav}
          onLogout={handleLogout}
        />

        {/* Main Content */}
        <main className="dp-main">
          {activeNav === 'ponds' ? (
            <PondManagement key={pondFormOpenSignal} openOnMount={pondFormOpenSignal > 0} />
          ) : activeNav === 'stock' ? (
            <StockGrowthManagement />
          ) : activeNav === 'water' ? (
            <WaterQualityManagement />
          ) : activeNav === 'health' ? (
            <FishHealthManagement />
          ) : activeNav === 'weather' ? (
            <WeatherManagement />
          ) : activeNav === 'finance' ? (
            <FinancialManagement />
          ) : activeNav === 'feeding' ? (
            <FeedingManagement onNotificationChange={loadNotifications} />
          ) : activeNav === 'analysis' ? (
            <MarketAnalysis />
          ) : activeNav === 'market' ? (
            <MarketBridge />
          ) : (
            <>
              <DashboardSummary alerts={summaryAlerts} stats={DASHBOARD_STATS} />

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
                    <button type="button" className="dp-btn-primary" onClick={handleViewPonds}>View all ponds</button>
                    <button type="button" className="dp-btn-secondary">Add water test</button>
                  </div>
                </div>

                <div className="dp-hero-art" aria-hidden="true">
                  {/* Existing SVG illustration remains exactly the same */}
                  <svg viewBox="0 0 440 270" fill="none" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="220" cy="120" rx="180" ry="90" fill="#B7DFD0" opacity="0.18"/>
                <ellipse cx="220" cy="210" rx="200" ry="56" fill="#B7DFD0" opacity="0.4"/>
                <ellipse cx="220" cy="210" rx="170" ry="44" fill="#74C69D" opacity="0.28"/>
                <ellipse cx="220" cy="210" rx="135" ry="31" fill="#52B788" opacity="0.22"/>
                <ellipse cx="220" cy="210" rx="82"  ry="19" stroke="#2D6A4F" strokeWidth="1"    opacity="0.18"/>
                <ellipse cx="220" cy="210" rx="115" ry="27" stroke="#2D6A4F" strokeWidth="0.75" opacity="0.11"/>
                <ellipse cx="220" cy="210" rx="152" ry="38" stroke="#2D6A4F" strokeWidth="0.5"  opacity="0.07"/>
                <line x1="52"  y1="232" x2="44"  y2="160" stroke="#1B4332" strokeWidth="2.2" strokeLinecap="round" opacity="0.5"/>
                <line x1="64"  y1="238" x2="74"  y2="168" stroke="#1B4332" strokeWidth="1.6" strokeLinecap="round" opacity="0.38"/>
                <ellipse cx="44"  cy="154" rx="6"  ry="15" fill="#2D6A4F" opacity="0.38"/>
                <ellipse cx="74"  cy="162" rx="5"  ry="12" fill="#40916C" opacity="0.3"/>
                <ellipse cx="58"  cy="158" rx="4"  ry="10" fill="#52B788" opacity="0.22"/>
                <line x1="390" y1="228" x2="384" y2="164" stroke="#1B4332" strokeWidth="2.2" strokeLinecap="round" opacity="0.45"/>
                <line x1="376" y1="234" x2="368" y2="170" stroke="#1B4332" strokeWidth="1.6" strokeLinecap="round" opacity="0.35"/>
                <ellipse cx="384" cy="158" rx="6"  ry="14" fill="#2D6A4F" opacity="0.33"/>
                <ellipse cx="368" cy="165" rx="4.5" ry="11" fill="#40916C" opacity="0.25"/>
                <ellipse cx="102" cy="220" rx="20" ry="7.5" fill="#40916C" opacity="0.38"/>
                <path d="M102 220 L102 212" stroke="#40916C" strokeWidth="1" opacity="0.4"/>
                <ellipse cx="340" cy="218" rx="16" ry="6"   fill="#40916C" opacity="0.32"/>
                <path d="M340 218 L340 211" stroke="#40916C" strokeWidth="1" opacity="0.35"/>
                <g transform="translate(145,198)">
                  <ellipse cx="0" cy="0" rx="30" ry="11" fill="#1B4332" opacity="0.88"/>
                  <path d="M30 0 L46 -10 L41 0 L46 10 Z" fill="#1B4332" opacity="0.88"/>
                  <circle cx="-20" cy="-3.5" r="3" fill="#D8F3DC"/>
                  <path d="M-5 -4 Q0 0 -5 4" stroke="#D8F3DC" strokeWidth="0.75" opacity="0.3"/>
                </g>
                <g transform="translate(286,204) scale(0.7)">
                  <ellipse cx="0" cy="0" rx="30" ry="11" fill="#40916C" opacity="0.85"/>
                  <path d="M30 0 L46 -10 L41 0 L46 10 Z" fill="#40916C" opacity="0.85"/>
                  <circle cx="-20" cy="-3.5" r="3" fill="#D8F3DC"/>
                </g>
                <g transform="translate(192,216) scale(-0.42,0.42)">
                  <ellipse cx="0" cy="0" rx="30" ry="11" fill="#52B788" opacity="0.7"/>
                  <path d="M30 0 L46 -10 L41 0 L46 10 Z" fill="#52B788" opacity="0.7"/>
                  <circle cx="-20" cy="-3.5" r="2.5" fill="#D8F3DC"/>
                </g>
                <circle cx="162" cy="183" r="4"   stroke="#52B788" strokeWidth="1.2" opacity="0.5"/>
                <circle cx="170" cy="170" r="2.8" stroke="#52B788" strokeWidth="1"   opacity="0.35"/>
                <circle cx="176" cy="160" r="2"   stroke="#74C69D" strokeWidth="0.9" opacity="0.22"/>
                <circle cx="256" cy="187" r="4.5" stroke="#52B788" strokeWidth="1.2" opacity="0.45"/>
                <circle cx="263" cy="173" r="3"   stroke="#52B788" strokeWidth="1"   opacity="0.3"/>
                <circle cx="220" cy="178" r="3.5" stroke="#74C69D" strokeWidth="1"   opacity="0.38"/>
                <circle cx="226" cy="166" r="2.2" stroke="#74C69D" strokeWidth="0.8" opacity="0.23"/>
                <rect x="212" y="162" width="5" height="44" rx="2.5" fill="#40916C" opacity="0.7"/>
                <rect x="205" y="158" width="18" height="10" rx="4" fill="#1B4332" opacity="0.8"/>
                <circle cx="214.5" cy="163" r="2.5" fill="#D8F3DC" opacity="0.9"/>
                <rect x="226" y="142" width="76" height="30" rx="7" fill="#1B4332" opacity="0.85"/>
                <text x="264" y="153" textAnchor="middle" fill="#D8F3DC" fontSize="8.5" fontFamily="system-ui,sans-serif" opacity="0.95">pH 7.2 · 21.7 °C</text>
                <text x="264" y="165" textAnchor="middle" fill="#74C69D"  fontSize="7.5" fontFamily="system-ui,sans-serif" opacity="0.8">O₂  8.1 mg/L</text>
                <line x1="214" y1="158" x2="229" y2="157" stroke="#74C69D" strokeWidth="0.8" strokeDasharray="2.5 2" opacity="0.45"/>
                  </svg>
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
