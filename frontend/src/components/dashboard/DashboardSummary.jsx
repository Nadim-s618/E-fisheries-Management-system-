export function DashboardSummary({ alerts, stats }) {
  return (
    <>
      <section className="dp-alert-banner" aria-label="Active alerts">
        <div className="dp-alert-header">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#C0392B" strokeWidth="2" strokeLinecap="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span>Alerts</span>
        </div>
        <div className="dp-alert-rows">
          {alerts.map(alert => (
            <div className="dp-alert-row" key={`${alert.pond}-${alert.issue}`}>
              <span className="dp-alert-pond">{alert.pond}</span>
              <span className="dp-alert-sep">:</span>
              <span className="dp-alert-issue">{alert.issue}</span>
            </div>
          ))}
        </div>
      </section>

      <div className="dp-stats-grid">
        {stats.map(stat => (
          <article className={`dp-stat-card dp-stat-${stat.accent}`} key={stat.label}>
            <p className="dp-stat-label">{stat.label}</p>
            <p className="dp-stat-value">{stat.value}</p>
            <p className="dp-stat-sub">{stat.sub}</p>
          </article>
        ))}
      </div>
    </>
  );
}
