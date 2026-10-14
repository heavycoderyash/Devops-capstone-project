def test_health_reports_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_root_identifies_service(client):
    body = client.get("/").json()
    assert body["service"] == "MediSlot API"
    assert body["docs"] == "/docs"


def test_metrics_are_prometheus_formatted(client, doctor, booking):
    client.post("/api/appointments", json=booking())
    text = client.get("/metrics").text
    assert "http_requests_total" in text
    assert 'medislot_appointments_booked_total{specialty="Cardiology"}' in text
