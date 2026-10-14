from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Appointment, Doctor
from ..schemas import DoctorCreate, DoctorOut, DoctorUpdate

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


def get_doctor_or_404(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A doctor with this email already exists")


@router.get("", response_model=list[DoctorOut])
def list_doctors(specialty: str | None = None, db: Session = Depends(get_db)):
    query = select(Doctor).order_by(Doctor.name)
    if specialty:
        query = query.where(Doctor.specialty == specialty)
    return list(db.scalars(query))


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    return get_doctor_or_404(db, doctor_id)


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    _commit(db)
    db.refresh(doctor)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, payload: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = get_doctor_or_404(db, doctor_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(doctor, key, value)
    _commit(db)
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = get_doctor_or_404(db, doctor_id)
    booked = db.scalar(select(func.count(Appointment.id)).where(Appointment.doctor_id == doctor_id))
    if booked:
        raise HTTPException(status_code=409, detail="Doctor has appointments; cancel or reassign them first")
    db.delete(doctor)
    db.commit()
