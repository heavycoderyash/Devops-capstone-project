export default function StatCard({ label, value, icon, tone }) {
  return (
    <div className={`stat tone-${tone}`}>
      <div className="stat-icon" aria-hidden="true">{icon}</div>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
      </div>
    </div>
  );
}
