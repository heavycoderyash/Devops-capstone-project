"""Business metrics exposed on /metrics alongside the HTTP metrics."""
from prometheus_client import Counter

APPOINTMENTS_BOOKED = Counter(
    "medislot_appointments_booked_total",
    "Appointments successfully booked",
    ["specialty"],
)
APPOINTMENT_STATUS_CHANGES = Counter(
    "medislot_appointment_status_changes_total",
    "Appointment status transitions",
    ["status"],
)
BOOKING_CONFLICTS = Counter(
    "medislot_booking_conflicts_total",
    "Bookings rejected because the doctor was already booked",
)
