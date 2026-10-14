import { initials } from '../lib/format.js';

export default function DoctorsPanel({ doctors, appointments, onDelete, compact = false }) {
  const activeCount = (doctorId) =>
    appointments.filter((a) => a.doctor_id === doctorId && ['SCHEDULED', 'CHECKED_IN'].includes(a.status)).length;
  const hasHistory = (doctorId) => appointments.some((a) => a.doctor_id === doctorId);

  if (compact) {
    return (
      <aside className="panel">
        <div className="panel-head">
          <div>
            <h2>Doctors on duty</h2>
            <p className="muted">Open appointments per doctor.</p>
          </div>
        </div>
        {doctors.map((d) => (
          <div className="doctor-row" key={d.id}>
            <span className="avatar" aria-hidden="true">{initials(d.name)}</span>
            <div>
              <b>{d.name}</b>
              <small>{d.specialty}{d.room && ` · Room ${d.room}`}</small>
            </div>
            <span className="count" title="Open appointments">{activeCount(d.id)}</span>
          </div>
        ))}
        {!doctors.length && <div className="empty">No doctors yet.</div>}
      </aside>
    );
  }

  return (
    <section className="doctor-grid">
      {doctors.map((d) => (
        <article className="panel doctor-card" key={d.id}>
          <span className="avatar large" aria-hidden="true">{initials(d.name)}</span>
          <h2>{d.name}</h2>
          <p className="specialty">{d.specialty}</p>
          <dl>
            <div><dt>Room</dt><dd>{d.room || '—'}</dd></div>
            <div><dt>Open visits</dt><dd>{activeCount(d.id)}</dd></div>
          </dl>
          <a href={`mailto:${d.email}`} className="muted email">{d.email}</a>
          {onDelete && (
            <button
              className="chip ghost"
              disabled={hasHistory(d.id)}
              title={hasHistory(d.id) ? 'Doctors with appointments cannot be removed' : 'Remove doctor'}
              onClick={() => onDelete(d)}
            >
              Remove
            </button>
          )}
        </article>
      ))}
      {!doctors.length && <div className="panel empty">No doctors yet — add one to start booking.</div>}
    </section>
  );
}
