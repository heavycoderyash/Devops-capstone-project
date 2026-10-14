from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..metrics import APPOINTMENT_STATUS_CHANGES, APPOINTMENTS_BOOKED, BOOKING_CONFLICTS
from ..models import Appointment, Doctor
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentUpdate, StatsOut, Status, to_utc
from .doctors import get_doctor_or_404

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

MAX_DURATION = timedelta(minutes=240)


def _day_window(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def _ensure_slot_free(db: Session, doctor_id: int, start: datetime, minutes: int, exclude_id: int | None = None) -> None:
    """Reject the booking if it overlaps another active appointment for the same doctor."""
    end = start + timedelta(minutes=minutes)
    query = select(Appointment).where(
        Appointment.doctor_id == doctor_id,
        Appointment.status != "CANCELLED",
        Appointment.scheduled_at > start - MAX_DURATION,
        Appointment.scheduled_at < end,
    )
    if exclude_id is not None:
        query = query.where(Appointment.id != exclude_id)
    for other in db.scalars(query):
        other_start = to_utc(other.scheduled_at)
        if other_start < end and start < other_start + timedelta(minutes=other.duration_minutes):
            BOOKING_CONFLICTS.inc()
            raise HTTPException(status_code=409, detail="Doctor already has an appointment in this time slot")


def _get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id, options=[joinedload(Appointment.doctor)])
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    status: Status | None = None,
    doctor_id: int | None = None,
    day: date | None = None,
    db: Session = Depends(get_db),
):
    query = select(Appointment).options(joinedload(Appointment.doctor)).order_by(Appointment.scheduled_at)
    if status:
        query = query.where(Appointment.status == status)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if day:
        start, end = _day_window(day)
        query = query.where(Appointment.scheduled_at >= start, Appointment.scheduled_at < end)
    return list(db.scalars(query))


@router.get("/stats", response_model=StatsOut)
def appointment_stats(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status)).all())
    start, end = _day_window(datetime.now(timezone.utc).date())
    today = db.scalar(
        select(func.count(Appointment.id)).where(Appointment.scheduled_at >= start, Appointment.scheduled_at < end)
    )
    return StatsOut(
        total=sum(counts.values()),
        today=today or 0,
        scheduled=counts.get("SCHEDULED", 0),
        checkedIn=counts.get("CHECKED_IN", 0),
        completed=counts.get("COMPLETED", 0),
        cancelled=counts.get("CANCELLED", 0),
        doctors=db.scalar(select(func.count(Doctor.id))) or 0,
    )


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return _get_appointment_or_404(db, appointment_id)


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    doctor = get_doctor_or_404(db, payload.doctor_id)
    _ensure_slot_free(db, doctor.id, payload.scheduled_at, payload.duration_minutes)
    appointment = Appointment(**payload.model_dump(), status="SCHEDULED")
    db.add(appointment)
    db.commit()
    APPOINTMENTS_BOOKED.labels(specialty=doctor.specialty).inc()
    return _get_appointment_or_404(db, appointment.id)


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appointment = _get_appointment_or_404(db, appointment_id)
    changes = payload.model_dump(exclude_unset=True)
    if "doctor_id" in changes:
        get_doctor_or_404(db, changes["doctor_id"])

    rescheduling = {"doctor_id", "scheduled_at", "duration_minutes"} & changes.keys()
    new_status = changes.get("status", appointment.status)
    if rescheduling and new_status != "CANCELLED":
        _ensure_slot_free(
            db,
            changes.get("doctor_id", appointment.doctor_id),
            changes.get("scheduled_at", to_utc(appointment.scheduled_at)),
            changes.get("duration_minutes", appointment.duration_minutes),
            exclude_id=appointment.id,
        )

    if "status" in changes and changes["status"] != appointment.status:
        APPOINTMENT_STATUS_CHANGES.labels(status=changes["status"]).inc()
    for key, value in changes.items():
        setattr(appointment, key, value)
    db.commit()
    db.expire_all()
    return _get_appointment_or_404(db, appointment.id)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = _get_appointment_or_404(db, appointment_id)
    db.delete(appointment)
    db.commit()
