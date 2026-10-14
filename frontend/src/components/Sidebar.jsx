const NAV = [
  { id: 'dashboard', icon: '▦', label: 'Dashboard' },
  { id: 'appointments', icon: '◷', label: 'Appointments' },
  { id: 'doctors', icon: '⚕', label: 'Doctors' },
];

export default function Sidebar({ view, onNavigate, todayCount }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">✚</span>
        <div>
          <b>MediSlot</b>
          <small>Clinic scheduling</small>
        </div>
      </div>
      <nav aria-label="Main">
        {NAV.map((item) => (
          <button
            key={item.id}
            className={view === item.id ? 'active' : ''}
            aria-current={view === item.id ? 'page' : undefined}
            onClick={() => onNavigate(item.id)}
          >
            <span aria-hidden="true">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
            {item.id === 'appointments' && todayCount > 0 && <span className="badge">{todayCount}</span>}
          </button>
        ))}
      </nav>
      <div className="side-bottom">
        <div className="callout">
          <strong>Front desk mode</strong>
          <p>Check patients in as they arrive to keep doctors' queues accurate.</p>
        </div>
      </div>
    </aside>
  );
}
