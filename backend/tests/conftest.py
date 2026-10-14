"""Test fixtures: every test runs against a fresh in-memory SQLite database,
never the real PostgreSQL instance."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def doctor(client):
    response = client.post(
        "/api/doctors",
        json={"name": "Dr. Test House", "specialty": "Cardiology", "email": "house@test.clinic", "room": "2B"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture()
def booking(doctor):
    """Factory returning a valid appointment payload for the fixture doctor."""
    def _make(**overrides):
        payload = {
            "patient_name": "Priya Sharma",
            "patient_phone": "+91 98765 43210",
            "doctor_id": doctor["id"],
            "scheduled_at": "2030-01-15T10:00:00Z",
            "duration_minutes": 30,
            "reason": "Routine check-up",
        }
        payload.update(overrides)
        return payload
    return _make
