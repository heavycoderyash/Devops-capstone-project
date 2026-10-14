import { formatDay, formatTime, initials, nextStatus, statusLabel } from '../lib/format.js';

const ACTION_LABEL = { CHECKED_IN: 'Check in', COMPLETED: 'Complete' };

export default function AppointmentsTable({ appointments, loading, actions, compact = false }) {
  if (loading) return <div className="empty">Loading appointments…</div>;
  if (!appointments.length) return <div className="empty">No appointments to show.</div>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Patient</th>
            <th>Doctor</th>
            <th>When</th>
            <th>Status</th>
            <th><span className="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((a) => {
            const next = nextStatus(a.status);
            return (
              <tr key={a.id}>
                <td data-label="Patient">
                  <div className="person">
                    <span className="avatar small" aria-hidden="true">{initials(a.patient_name)}</span>
                    <div>
                      <b>{a.patient_name}</b>
                      <small>{compact ? a.patient_phone : a.reason || a.patient_phone}</small>
                    </div>
                  </div>
                </td>
                <td data-label="Doctor">
                  <b className="cell-title">{a.doctor.name}</b>
                  <small>{a.doctor.specialty}</small>
                </td>
                <td data-label="When">
                  <b className="cell-title">{formatTime(a.scheduled_at)}</b>
                  <small>{formatDay(a.scheduled_at)} · {a.duration_minutes} min</small>
                </td>
                <td data-label="Status">
                  <span className={`status ${a.status.toLowerCase()}`}>{statusLabel(a.status)}</span>
                </td>
                <td className="row-actions">
                  {next && (
                    <button className="chip" onClick={() => actions.changeStatus(a, next)}>{ACTION_LABEL[next]}</button>
                  )}
                  {a.status === 'SCHEDULED' && (
                    <button className="chip ghost" onClick={() => actions.changeStatus(a, 'CANCELLED')}>Cancel</button>
                  )}
                  {!compact && ['COMPLETED', 'CANCELLED'].includes(a.status) && (
                    <button className="icon-btn" title="Delete appointment" aria-label="Delete appointment" onClick={() => actions.remove(a)}>🗑</button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
