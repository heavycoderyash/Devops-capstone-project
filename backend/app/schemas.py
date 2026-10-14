from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Status = Literal["SCHEDULED", "CHECKED_IN", "COMPLETED", "CANCELLED"]


def to_utc(value: datetime) -> datetime:
    """Treat naive datetimes as UTC and normalise aware ones to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# ---------- Doctors ----------

class DoctorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=80)
    email: EmailStr
    room: str = Field(default="", max_length=20)


class DoctorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    specialty: str | None = Field(default=None, min_length=2, max_length=80)
    email: EmailStr | None = None
    room: str | None = Field(default=None, max_length=20)


class DoctorOut(DoctorCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DoctorBrief(BaseModel):
    id: int
    name: str
    specialty: str
    model_config = ConfigDict(from_attributes=True)


# ---------- Appointments ----------

class AppointmentCreate(BaseModel):
    patient_name: str = Field(min_length=2, max_length=120)
    patient_phone: str = Field(min_length=7, max_length=20, pattern=r"^\+?[0-9 \-]{7,20}$")
    doctor_id: int = Field(gt=0)
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=10, le=240)
    reason: str = Field(default="", max_length=1000)

    @field_validator("scheduled_at")
    @classmethod
    def _normalise_time(cls, value: datetime) -> datetime:
        return to_utc(value)


class AppointmentUpdate(BaseModel):
    patient_name: str | None = Field(default=None, min_length=2, max_length=120)
    patient_phone: str | None = Field(default=None, min_length=7, max_length=20, pattern=r"^\+?[0-9 \-]{7,20}$")
    doctor_id: int | None = Field(default=None, gt=0)
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=10, le=240)
    reason: str | None = Field(default=None, max_length=1000)
    status: Status | None = None

    @field_validator("scheduled_at")
    @classmethod
    def _normalise_time(cls, value: datetime | None) -> datetime | None:
        return to_utc(value) if value is not None else None


class AppointmentOut(BaseModel):
    id: int
    patient_name: str
    patient_phone: str
    doctor_id: int
    doctor: DoctorBrief
    scheduled_at: datetime
    duration_minutes: int
    reason: str
    status: Status
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_validator("scheduled_at", "created_at")
    @classmethod
    def _normalise_time(cls, value: datetime) -> datetime:
        # SQLite drops tzinfo; make API responses consistently UTC-aware.
        return to_utc(value)


class StatsOut(BaseModel):
    total: int
    today: int
    scheduled: int
    checkedIn: int
    completed: int
    cancelled: int
    doctors: int
