"""Tests for health check endpoint."""


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "active_clients" in data
    assert "uptime_seconds" in data


def test_health_check_shows_active_clients(client, sample_client):
    response = client.get("/health")
    data = response.json()
    assert data["active_clients"] == 1
