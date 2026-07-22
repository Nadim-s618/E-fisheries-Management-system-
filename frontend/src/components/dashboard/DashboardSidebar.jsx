import "./DashboardSidebar.css";

export function DashboardSidebar({
  activeNav,
  navItems,
  onAddPond,
  onNavChange,
  onLogout,
}) {
  return (
    <aside className="dp-sidebar" aria-label="Module navigation">
      <div className="dp-sidebar-brand">
        <span className="dp-sidebar-brand-mark" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12c3-4 8-6 13-6 2 0 4 .5 5.5 1.5-1 2-3 3.5-5.5 3.5-5 0-10-2-13 1z" />
            <path d="M17 7.5c1.2-1.5 2.6-2.2 4-2.2-.3 1.8-1.3 3.2-2.6 4.2" />
            <circle cx="7" cy="11.6" r="0.8" fill="currentColor" stroke="none" />
          </svg>
        </span>
        <div className="dp-sidebar-brand-text">
          <span className="dp-sidebar-brand-name">E-Fisheries</span>
          <span className="dp-sidebar-brand-sub">Farm Management</span>
        </div>
      </div>

      <button className="dp-btn-add-pond" onClick={onAddPond}>
        <span className="dp-sidebar-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </span>
        Add New Pond
      </button>

      <p className="dp-sidebar-heading">Menu</p>

      <nav className="dp-sidebar-nav">
        {navItems.map((item, index) => (
          <button
            key={item.id}
            type="button"
            className={`dp-sidebar-item ${activeNav === item.id ? 'active' : ''}`}
            style={{ '--i': index }}
            onClick={() => onNavChange(item.id)}
            title={item.label}
            aria-label={item.label}
            aria-current={activeNav === item.id ? 'page' : undefined}
          >
            <span className="dp-sidebar-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d={item.icon} />
              </svg>
            </span>
            <span className="dp-sidebar-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <button className="dp-btn-signout" onClick={onLogout}>
        <span className="dp-sidebar-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </span>
        Sign Out
      </button>
    </aside>
  );
}