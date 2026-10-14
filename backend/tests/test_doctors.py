def test_create_and_list_doctors(client, doctor):
    response = client.get("/api/doctors")
    assert response.status_code == 200
    assert [d["email"] for d in response.json()] == ["house@test.clinic"]


def test_get_doctor_not_found(client):
    assert client.get("/api/doctors/999").status_code == 404


def test_duplicate_doctor_email_conflicts(client, doctor):
    response = client.post(
        "/api/doctors",
        json={"name": "Dr. Other", "specialty": "Dermatology", "email": "house@test.clinic"},
    )
    assert response.status_code == 409


def test_invalid_doctor_email_rejected(client):
    response = client.post("/api/doctors", json={"name": "Dr. X", "specialty": "ENT", "email": "not-an-email"})
    assert response.status_code == 422


def test_update_doctor(client, doctor):
    response = client.put(f"/api/doctors/{doctor['id']}", json={"room": "3C"})
    assert response.status_code == 200
    assert response.json()["room"] == "3C"
    assert response.json()["name"] == "Dr. Test House"


def test_cannot_delete_doctor_with_appointments(client, doctor, booking):
    client.post("/api/appointments", json=booking())
    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 409


def test_delete_doctor_without_appointments(client, doctor):
    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 204
    assert client.get(f"/api/doctors/{doctor['id']}").status_code == 404
