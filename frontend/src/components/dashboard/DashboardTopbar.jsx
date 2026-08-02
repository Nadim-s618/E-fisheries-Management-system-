import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import './DashboardTopbar.css';

export function DashboardTopbar({
  onPondsClick,
  onSearchClick,
  onNotificationClick,
  onNotificationRead,
  onNotificationsRead,
  onProfileClick,
  user,
  notifications = [],
  notificationsLoading = false,
}) {
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const navigate = useNavigate();

  const notificationCount = notifications.length;
  const initial = (user?.first_name || 'P').charAt(0).toUpperCase();
  const userName = user?.first_name || 'Profile';
  const userEmail = user?.email || 'user@fisheries.local';

  const handleSearch = () => {
    setIsSearchActive(!isSearchActive);
    onSearchClick?.();
  };

  const handleNotification = () => {
    setIsProfileOpen(false);
    setIsNotificationOpen(current => !current);
    onNotificationClick?.();
  };

  const handleProfileClick = () => {
    setIsNotificationOpen(false);
    setIsProfileOpen(!isProfileOpen);
  };

  const handleNavigation = (path) => {
    setIsProfileOpen(false);
    navigate(path);
  };

  const handleLogout = () => {
    setIsProfileOpen(false);
    onProfileClick?.('logout');
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
      <Link to="/" className="dp-logo">
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
        <Link to="/" className="dp-nav-link">
          Home
        </Link>
        <button
          type="button"
          className="dp-nav-link"
          onClick={onPondsClick}
          style={{ background: 'none', border: 'none', cursor: 'pointer' }}
        >
          Ponds
        </button>
        <a href="#tips" className="dp-nav-link">
          Tips
        </a>
      </nav>

      {/* Right Section */}
      <div className="dp-nav-right">
        {/* Search Button */}
        <button
          className="dp-icon-btn dp-search-btn"
          onClick={handleSearch}
          aria-label="Search"
          title="Search"
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
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
        </button>

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
            <div className="dp-notif-menu" role="menu" aria-label="Notifications">
              <div className="dp-notif-menu-header">
                <div>
                  <span>Notifications</span>
                  <small>{notificationCount} unread</small>
                </div>
                {notificationCount > 0 && (
                  <button type="button" className="dp-notif-clear" onClick={handleMarkAllRead}>
                    Mark all read
                  </button>
                )}
              </div>
              <div className="dp-notif-list">
                {notificationsLoading ? (
                  <div className="dp-notif-menu-empty">Loading notifications...</div>
                ) : notifications.length > 0 ? (
                  notifications.map((notification, index) => (
                    <button
                      key={notification.id || `${notification.pond}-${notification.parameter}-${index}`}
                      type="button"
                      className={`dp-notif-menu-item ${notification.priority ? `priority-${notification.priority.toLowerCase()}` : ''}`}
                      onClick={() => handleNotificationItemClick(notification)}
                    >
                      <span className="dp-notif-item-topline">
                        <strong>{notification.pond_name || notification.pond}</strong>
                        <small>{notification.priority}</small>
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
              {initial}
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
                <div className="dp-profile-avatar-lg">{initial}</div>
                <div className="dp-profile-info">
                  <p className="dp-profile-name-full">{userName}</p>
                  <p className="dp-profile-email">{userEmail}</p>
                </div>
              </div>

              <div className="dp-profile-menu-divider" />

              <a
                href="#settings"
                className="dp-profile-menu-item"
                role="menuitem"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('/settings');
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
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m2.12 2.12l4.24 4.24M1 12h6m6 0h6m-1.78 7.78l-4.24-4.24m-2.12-2.12l-4.24-4.24" />
                </svg>
                Settings
              </a>

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

              <a
                href="#help"
                className="dp-profile-menu-item"
                role="menuitem"
                onClick={(e) => {
                  e.preventDefault();
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
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 16v-4M12 8h.01" />
                </svg>
                Help & Support
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
