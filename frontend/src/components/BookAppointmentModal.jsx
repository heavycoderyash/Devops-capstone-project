import Modal from './Modal.jsx';
import { localInputToIso, nextHalfHourInput } from '../lib/format.js';

export default function BookAppointmentModal({ doctors, onClose, onSubmit }) {
  const submit = (form) =>
    onSubmit({
      patient_name: form.patient_name.trim(),
      patient_phone: form.patient_phone.trim(),
      doctor_id: Number(form.doctor_id),
      scheduled_at: localInputToIso(form.scheduled_at),
      duration_minutes: Number(form.duration_minutes),
      reason: form.reason.trim(),
    });

  return (
    <Modal eyebrow="NEW APPOINTMENT" title="Book a patient visit" onClose={onClose} onSubmit={submit}>
      <div className="form-row">
        <label>
          Patient name
          <input name="patient_name" required minLength={2} placeholder="e.g. Priya Sharma" autoFocus />
        </label>
        <label>
          Phone
          <input name="patient_phone" required type="tel" pattern="\+?[0-9 \-]{7,20}" placeholder="+91 98765 43210" />
        </label>
      </div>
      <label>
        Doctor
        <select name="doctor_id" required>
          {doctors.map((d) => (
            <option key={d.id} value={d.id}>{d.name} — {d.specialty}</option>
          ))}
        </select>
      </label>
      <div className="form-row">
        <label>
          Date &amp; time
          <input name="scheduled_at" type="datetime-local" required defaultValue={nextHalfHourInput()} step={900} />
        </label>
        <label>
          Duration
          <select name="duration_minutes" defaultValue="30">
            {[15, 30, 45, 60].map((m) => <option key={m} value={m}>{m} minutes</option>)}
          </select>
        </label>
      </div>
      <label>
        Reason for visit
        <textarea name="reason" maxLength={1000} placeholder="Symptoms, follow-up, routine check-up…" />
      </label>
      <button className="primary full">Book appointment</button>
    </Modal>
  );
}
