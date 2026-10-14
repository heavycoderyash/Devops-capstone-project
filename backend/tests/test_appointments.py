from datetime import datetime, timezone


def test_book_appointment(client, doctor, booking):
    response = client.post("/api/appointments", json=booking())
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SCHEDULED"
    assert body["doctor"]["name"] == "Dr. Test House"
    assert body["scheduled_at"].startswith("2030-01-15T10:00:00")


def test_booking_requires_existing_doctor(client, booking):
    response = client.post("/api/appointments", json=booking(doctor_id=999))
    assert response.status_code == 404


def test_booking_validates_payload(client, booking):
    response = client.post("/api/appointments", json=booking(patient_phone="call me", duration_minutes=5))
    assert response.status_code == 422


def test_overlapping_booking_is_rejected(client, booking):
    assert client.post("/api/appointments", json=booking()).status_code == 201
    clash = client.post("/api/appointments", json=booking(patient_name="Arjun Rao", scheduled_at="2030-01-15T10:15:00Z"))
    assert clash.status_code == 409


def test_adjacent_booking_is_allowed(client, booking):
    assert client.post("/api/appointments", json=booking()).status_code == 201
    next_slot = client.post("/api/appointments", json=booking(scheduled_at="2030-01-15T10:30:00Z"))
    assert next_slot.status_code == 201


def test_cancelled_slot_can_be_rebooked(client, booking):
    first = client.post("/api/appointments", json=booking()).json()
    client.put(f"/api/appointments/{first['id']}", json={"status": "CANCELLED"})
    assert client.post("/api/appointments", json=booking(patient_name="Arjun Rao")).status_code == 201


def test_list_filters_by_status_and_day(client, booking):
    a = client.post("/api/appointments", json=booking()).json()
    client.post("/api/appointments", json=booking(scheduled_at="2030-01-16T09:00:00Z"))
    client.put(f"/api/appointments/{a['id']}", json={"status": "CHECKED_IN"})

    checked_in = client.get("/api/appointments", params={"status": "CHECKED_IN"}).json()
    assert [x["id"] for x in checked_in] == [a["id"]]
    on_16th = client.get("/api/appointments", params={"day": "2030-01-16"}).json()
    assert len(on_16th) == 1


def test_update_status_flow(client, booking):
    appt = client.post("/api/appointments", json=booking()).json()
    for status in ("CHECKED_IN", "COMPLETED"):
        response = client.put(f"/api/appointments/{appt['id']}", json={"status": status})
        assert response.status_code == 200
        assert response.json()["status"] == status


def test_reschedule_into_conflict_is_rejected(client, booking):
    client.post("/api/appointments", json=booking())
    other = client.post("/api/appointments", json=booking(scheduled_at="2030-01-15T12:00:00Z")).json()
    response = client.put(f"/api/appointments/{other['id']}", json={"scheduled_at": "2030-01-15T10:10:00Z"})
    assert response.status_code == 409


def test_delete_appointment(client, booking):
    appt = client.post("/api/appointments", json=booking()).json()
    assert client.delete(f"/api/appointments/{appt['id']}").status_code == 204
    assert client.get(f"/api/appointments/{appt['id']}").status_code == 404


def test_stats(client, booking):
    today = datetime.now(timezone.utc).replace(hour=23, minute=0, second=0, microsecond=0).isoformat()
    client.post("/api/appointments", json=booking(scheduled_at=today))
    cancelled = client.post("/api/appointments", json=booking()).json()
    client.put(f"/api/appointments/{cancelled['id']}", json={"status": "CANCELLED"})

    stats = client.get("/api/appointments/stats").json()
    assert stats == {
        "total": 2, "today": 1, "scheduled": 1, "checkedIn": 0,
        "completed": 0, "cancelled": 1, "doctors": 1,
    }
