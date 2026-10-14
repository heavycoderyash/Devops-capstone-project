import Modal from './Modal.jsx';

const SPECIALTIES = ['General Medicine', 'Cardiology', 'Dermatology', 'Pediatrics', 'Orthopedics', 'ENT', 'Gynecology', 'Neurology'];

export default function AddDoctorModal({ onClose, onSubmit }) {
  const submit = (form) =>
    onSubmit({ name: form.name.trim(), specialty: form.specialty, email: form.email.trim(), room: form.room.trim() });

  return (
    <Modal eyebrow="NEW DOCTOR" title="Add a practitioner" onClose={onClose} onSubmit={submit}>
      <label>
        Full name
        <input name="name" required minLength={2} placeholder="Dr. Kavya Nair" autoFocus />
      </label>
      <div className="form-row">
        <label>
          Specialty
          <select name="specialty">
            {SPECIALTIES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </label>
        <label>
          Room
          <input name="room" maxLength={20} placeholder="e.g. 105" />
        </label>
      </div>
      <label>
        Email
        <input name="email" type="email" required placeholder="kavya.nair@medislot.clinic" />
      </label>
      <button className="primary full">Add doctor</button>
    </Modal>
  );
}
