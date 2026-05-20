const navigationItems = [
  { id: 'overview', label: 'Overview' },
  { id: 'metricDetail', label: 'Metric Detail' },
  { id: 'alerts', label: 'Alerts' },
  { id: 'evaluation', label: 'Evaluation' },
];

function Layout({ activePage, children, onNavigate }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Academic MVP</p>
          <h1>Event Quality Dashboard</h1>
        </div>
        <nav className="nav-list" aria-label="Dashboard pages">
          {navigationItems.map((item) => (
            <button
              className={item.id === activePage ? 'nav-item active' : 'nav-item'}
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}

export default Layout;

