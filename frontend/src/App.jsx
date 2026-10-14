import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './lib/api.js';
import { greeting } from './lib/format.js';
import Sidebar from './components/Sidebar.jsx';
import StatCard from './components/StatCard.jsx';
import AppointmentsTable from './components/AppointmentsTable.jsx';
import DoctorsPanel from './components/DoctorsPanel.jsx';
import BookAppointmentModal from './components/BookAppointmentModal.jsx';
import AddDoctorModal from './components/AddDoctorModal.jsx';
import Toast from './components/Toast.jsx';

const EMPTY_STATS = { total: 0, today: 0, scheduled: 0, checkedIn: 0, completed: 0, cancelled: 0, doctors: 0 };

export default function App() {
  const [view, setView] = useState('dashboard');
  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null); // 'book' | 'doctor' | null
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    try {
      const [a, d, s] = await Promise.all([api.listAppointments(), api.listDoctors(), api.stats()]);
      setAppointments(a);
      setDoctors(d);
      setStats(s);
      setError('');
    } catch (e) {
      setError(e.message === 'Failed to fetch' ? 'Cannot reach the MediSlot API' : e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const notify = (message, tone = 'success') => setToast({ message, tone, id: Date.now() });
  const clearToast = useCallback(() => setToast(null), []);

  // Wraps a mutation: run it, refresh data, report success or the API's error message.
  const mutate = async (action, successMessage) => {
    try {
      await action();
      notify(successMessage);
      await load();
      return true;
    } catch (e) {
      notify(e.message, 'error');
      return false;
    }
  };

  const upcoming = useMemo(() => {
    const now = Date.now() - 60 * 60 * 1000;
    return appointments
      .filter((a) => ['SCHEDULED', 'CHECKED_IN'].includes(a.status) && new Date(a.scheduled_at).getTime() >= now)
      .slice(0, 6);
  }, [appointments]);

  const actions = {
    changeStatus: (appt, status) =>
      mutate(() => api.updateAppointment(appt.id, { status }), `${appt.patient_name}: ${status.replace('_', ' ').toLowerCase()}`),
    remove: (appt) => mutate(() => api.deleteAppointment(appt.id), 'Appointment deleted'),
  };

  const titles = {
    dashboard: { eyebrow: 'CLINIC / OVERVIEW', title: `${greeting()} 👋`, sub: "Here's how the clinic is running today." },
    appointments: { eyebrow: 'CLINIC / APPOINTMENTS', title: 'Appointments', sub: 'Book, check in and complete patient visits.' },
    doctors: { eyebrow: 'CLINIC / DOCTORS', title: 'Doctors', sub: 'Manage the practitioners patients can book.' },
  };
  const heading = titles[view];

  return (
    <div className="app">
      <Sidebar view={view} onNavigate={setView} todayCount={stats.today} />

      <main className="main">
        <header className="page-header">
          <div>
            <p className="eyebrow">{heading.eyebrow}</p>
            <h1>{heading.title}</h1>
            <p className="muted">{heading.sub}</p>
          </div>
          <div className="header-actions">
            {view === 'doctors' && (
              <button className="secondary" onClick={() => setModal('doctor')}>＋ Add doctor</button>
            )}
            <button className="primary" onClick={() => setModal('book')} disabled={!doctors.length}>
              ＋ Book appointment
            </button>
          </div>
        </header>

        {error && (
          <div className="alert" role="alert">
            <strong>⚠ {error}.</strong> Make sure the backend and PostgreSQL are running, then{' '}
            <button className="link" onClick={load}>retry</button>.
          </div>
        )}

        {view === 'dashboard' && (
          <>
            <section className="stats" aria-label="Key figures">
              <StatCard label="Today's appointments" value={stats.today} icon="◷" tone="teal" />
              <StatCard label="Scheduled" value={stats.scheduled} icon="▤" tone="blue" />
              <StatCard label="Checked in" value={stats.checkedIn} icon="➜" tone="amber" />
              <StatCard label="Completed" value={stats.completed} icon="✓" tone="green" />
            </section>
            <section className="content-grid">
              <div className="panel">
                <div className="panel-head">
                  <div>
                    <h2>Upcoming visits</h2>
                    <p className="muted">Next patients across all doctors.</p>
                  </div>
                  <button className="link" onClick={() => setView('appointments')}>View all →</button>
                </div>
                <AppointmentsTable appointments={upcoming} loading={loading} actions={actions} compact />
              </div>
              <DoctorsPanel doctors={doctors} appointments={appointments} compact />
            </section>
          </>
        )}

        {view === 'appointments' && (
          <AppointmentsView appointments={appointments} doctors={doctors} loading={loading} actions={actions} />
        )}

        {view === 'doctors' && (
          <DoctorsPanel
            doctors={doctors}
            appointments={appointments}
            onDelete={(d) => mutate(() => api.deleteDoctor(d.id), `${d.name} removed`)}
          />
        )}
      </main>

      {modal === 'book' && (
        <BookAppointmentModal
          doctors={doctors}
          onClose={() => setModal(null)}
          onSubmit={async (data) => {
            if (await mutate(() => api.bookAppointment(data), `Booked ${data.patient_name}`)) setModal(null);
          }}
        />
      )}
      {modal === 'doctor' && (
        <AddDoctorModal
          onClose={() => setModal(null)}
          onSubmit={async (data) => {
            if (await mutate(() => api.createDoctor(data), `${data.name} added`)) setModal(null);
          }}
        />
      )}
      {toast && <Toast key={toast.id} {...toast} onDone={clearToast} />}
    </div>
  );
}

function AppointmentsView({ appointments, doctors, loading, actions }) {
  const [status, setStatus] = useState('ALL');
  const [doctorId, setDoctorId] = useState('');
  const [search, setSearch] = useState('');

  const visible = appointments.filter(
    (a) =>
      (status === 'ALL' || a.status === status) &&
      (!doctorId || a.doctor_id === Number(doctorId)) &&
      a.patient_name.toLowerCase().includes(search.trim().toLowerCase()),
  );

  return (
    <section className="panel">
      <div className="panel-head wrap">
        <div className="filters" role="tablist" aria-label="Filter by status">
          {['ALL', 'SCHEDULED', 'CHECKED_IN', 'COMPLETED', 'CANCELLED'].map((s) => (
            <button key={s} role="tab" aria-selected={status === s} className={status === s ? 'selected' : ''} onClick={() => setStatus(s)}>
              {s === 'ALL' ? 'All' : s.replace('_', ' ').toLowerCase()}
            </button>
          ))}
        </div>
        <div className="toolbar">
          <input type="search" placeholder="Search patient…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search patient" />
          <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)} aria-label="Filter by doctor">
            <option value="">All doctors</option>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
      </div>
      <AppointmentsTable appointments={visible} loading={loading} actions={actions} />
    </section>
  );
}
