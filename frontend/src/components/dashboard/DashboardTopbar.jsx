import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAiAdvisor, getPonds } from '../../lib/api';
import './DashboardTopbar.css';

export function DashboardTopbar({
  onPondsClick,
  onHomeClick,
  onNotificationClick,
  onNotificationRead,
  onNotificationsRead,
  onLogout,
  user,
  notifications = [],
  notificationsLoading = false,
}) {
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isTipsOpen, setIsTipsOpen] = useState(false);
  const [ponds, setPonds] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [tips, setTips] = useState(null);
  const [tipsLoading, setTipsLoading] = useState(false);
  const [tipsError, setTipsError] = useState('');
  const navigate = useNavigate();

  const notificationCount = notifications.length;
  const initial = (user?.first_name || 'P').charAt(0).toUpperCase();
  const userName = user?.first_name || 'Profile';
  const userEmail = user?.email || 'user@fisheries.local';

  const handleNotification = () => {
    setIsProfileOpen(false);
    setIsNotificationOpen(current => !current);
    onNotificationClick?.();
  };

  const handleProfileClick = () => {
    setIsNotificationOpen(false);
    setIsTipsOpen(false);
    setIsProfileOpen(!isProfileOpen);
  };

  const loadTips = async (pondId) => {
    if (!pondId) return;

    setSelectedPondId(String(pondId));
    setTipsLoading(true);
    setTipsError('');

    try {
      const data = await getAiAdvisor(pondId);
      setTips(data);
    } catch (error) {
      setTips(null);
      setTipsError(error.message || 'Unable to load tips.');
    } finally {
      setTipsLoading(false);
    }
  };

  const handleTipsClick = async () => {
    setIsNotificationOpen(false);
    setIsProfileOpen(false);
    const opening = !isTipsOpen;
    setIsTipsOpen(opening);

    if (opening && ponds.length === 0) {
      setTipsLoading(true);
      setTipsError('');
      try {
        const data = await getPonds();
        const availablePonds = data || [];
        setPonds(availablePonds);
        if (availablePonds[0]?.id) {
          await loadTips(availablePonds[0].id);
        }
      } catch (error) {
        setTipsError(error.message || 'Unable to load ponds.');
        setTipsLoading(false);
      }
    }
  };

  const handleNavigation = (path) => {
    setIsProfileOpen(false);
    navigate(path);
  };

  const handleLogout = async () => {
    setIsProfileOpen(false);
    await onLogout?.();
  };

  const handleNotificationItemClick = async (notification) => {
    await onNotificationRead?.(notification);
    setIsNotificationOpen(false);
  };

  const handleMarkAllRead = async () => {
    await onNotificationsRead?.();
    setIsNotificationOpen(false);
  };

  return (
    <header className="dp-navbar">
      {/* Logo Section */}
      <Link to="/dashboard" className="dp-logo" onClick={onHomeClick}>
        <div className="dp-logo-mark">
          <img src="/logo.png" alt="e-Fisheries logo" />
        </div>
        <div className="dp-logo-text">
          <span className="dp-logo-name">e-Fisheries</span>
          <span className="dp-logo-sub">Management System</span>
        </div>
      </Link>

      {/* Center Navigation Links */}
      <nav className="dp-nav-links">
        <button type="button" className="dp-nav-link" onClick={onHomeClick}>
          Home
        </button>
        <button
          type="button"
          className="dp-nav-link"
          onClick={onPondsClick}
          style={{ background: 'none', border: 'none', cursor: 'pointer' }}
        >
          Ponds
        </button>
        <div className="dp-tips-wrapper">
          <button
            type="button"
            className="dp-nav-link"
            onClick={handleTipsClick}
            aria-expanded={isTipsOpen}
            aria-controls="dashboard-tips-menu"
          >
            Tips
          </button>

          {isTipsOpen && (
            <div id="dashboard-tips-menu" className="dp-tips-menu" role="dialog" aria-label="Pond tips">
              <div className="dp-tips-header">
                <div>
                  <span className="dp-tips-kicker">AI Advisor</span>
                  <strong>Pond tips</strong>
                </div>
                <label className="dp-tips-field">
                  <span>Pond</span>
                  <select
                    value={selectedPondId}
                    onChange={event => loadTips(event.target.value)}
                    disabled={!ponds.length || tipsLoading}
                  >
                    {!ponds.length ? (
                      <option value="">No ponds</option>
                    ) : ponds.map(pond => (
                      <option key={pond.id} value={pond.id}>{pond.name}</option>
                    ))}
                  </select>
                </label>
              </div>

              {tipsLoading ? (
                <div className="dp-tips-state">Loading tips...</div>
              ) : tipsError ? (
                <div className="dp-tips-state dp-tips-error">{tipsError}</div>
              ) : !ponds.length ? (
                <div className="dp-tips-state">Add a pond before generating tips.</div>
              ) : tips ? (
                <div className="dp-tips-content">
                  <div className="dp-tips-summary">
                    <span>{tips.ai_enabled ? 'Gemini AI' : 'Fallback Advisor'}</span>
                    <strong>{tips.priority || 'Normal'}</strong>
                    <p>{tips.summary}</p>
                  </div>
                  {[
                    ['Recommendations', tips.recommendations, 'recommendations'],
                    ['Risks to watch', tips.risks, 'risks'],
                    ['Next actions', tips.next_actions, 'actions'],
                    ['Daily farm tips', tips.daily_tips, 'daily'],
                  ].map(([title, items, type]) => items?.length > 0 && (
                    <section className={`dp-tips-section dp-tips-${type}`} key={title}>
                      <strong>{title}</strong>
                      <ul>{items.map(item => <li key={item}>{item}</li>)}</ul>
                    </section>
                  ))}
                </div>
              ) : (
                <div className="dp-tips-state">Select a pond to generate tips.</div>
              )}
            </div>
          )}
        </div>
      </nav>

      {/* Right Section */}
      <div className="dp-nav-right">
        {/* Notification Button */}
        <div className="dp-notif-wrapper">
          <button
            className="dp-icon-btn dp-notif-btn"
            onClick={handleNotification}
            aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount} new)` : ''}`}
            title="Notifications"
            aria-expanded={isNotificationOpen}
          >
            <svg
              width="17"
              height="17"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 01-3.46 0" />
            </svg>
            {notificationCount > 0 && (
              <span className="dp-notif-badge" aria-label={`${notificationCount} new notifications`}>
                {notificationCount > 9 ? '9+' : notificationCount}
              </span>
            )}
          </button>

          {isNotificationOpen && (
            <div className="dp-notif-menu" role="dialog" aria-label="Notifications">
              <div className="dp-notif-menu-header">
                <div>
                  <span>Notifications</span>
                  <small>{notificationCount} unread</small>
                </div>
                <div className="dp-notif-header-actions">
                  {notificationCount > 0 && (
                    <button type="button" className="dp-notif-clear" onClick={handleMarkAllRead}>Mark all read</button>
                  )}
                  <button type="button" className="dp-notif-close" onClick={() => setIsNotificationOpen(false)} aria-label="Close notifications">×</button>
                </div>
              </div>
              <div className="dp-notif-list">
                {notificationsLoading ? (
                  <div className="dp-notif-menu-empty">Loading notifications...</div>
                ) : notifications.length > 0 ? (
                  notifications.map((notification, index) => (
                    <button
                      key={notification.id || `${notification.pond}-${notification.parameter}-${index}`}
                      type="button"
                      className="dp-notif-menu-item"
                      onClick={() => handleNotificationItemClick(notification)}
                    >
                      <span className="dp-notif-item-topline">
                        <strong>{notification.pond_name || notification.pond || 'Fish Store'}</strong>
                      </span>
                      <span className="dp-notif-issue">
                        {notification.parameter}
                        {notification.current_value ? ` · ${notification.current_value}` : ''}
                      </span>
                      <span>{notification.reason}</span>
                    </button>
                  ))
                ) : (
                  <div className="dp-notif-menu-empty">No new notifications.</div>
                )}
              </div>
            </div>
          )}

          {isNotificationOpen && (
            <div className="dp-notif-backdrop" onClick={() => setIsNotificationOpen(false)} aria-hidden="true" />
          )}
        </div>

        {/* Profile Dropdown */}
        <div className="dp-profile-wrapper">
          <button
            className="dp-profile-display"
            onClick={handleProfileClick}
            aria-label="Profile menu"
            aria-expanded={isProfileOpen}
            title={userName}
          >
            <span className="dp-profile-avatar" aria-hidden="true">
              {user?.profile_picture_url ? <img src={user.profile_picture_url} alt="" /> : initial}
            </span>
            <span className="dp-profile-name">{userName}</span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="dp-chevron-icon"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {/* Profile Dropdown Menu */}
          {isProfileOpen && (
            <div className="dp-profile-menu" role="menu">
              <div className="dp-profile-menu-header">
                <div className="dp-profile-avatar-lg">
                  {user?.profile_picture_url ? <img src={user.profile_picture_url} alt="" /> : initial}
                </div>
                <div className="dp-profile-info">
                  <p className="dp-profile-name-full">{userName}</p>
                  <p className="dp-profile-email">{userEmail}</p>
                </div>
              </div>

              <div className="dp-profile-menu-divider" />

              <a
                href="#profile"
                className="dp-profile-menu-item"
                role="menuitem"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('/profile');
                }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                My Profile
              </a>

              <div className="dp-profile-menu-divider" />

              <button
                className="dp-profile-menu-item dp-profile-logout"
                role="menuitem"
                onClick={handleLogout}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Log Out
              </button>
            </div>
          )}

          {/* Backdrop to close menu */}
          {isProfileOpen && (
            <div
              className="dp-profile-backdrop"
              onClick={() => setIsProfileOpen(false)}
              aria-hidden="true"
            />
          )}
        </div>
      </div>
    </header>
  );
}
