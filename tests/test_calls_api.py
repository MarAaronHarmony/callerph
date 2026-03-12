"""Tests for call log API endpoint."""


def test_list_calls_empty(client):
    """Test empty call list."""
    response = client.get("/api/calls")
    assert response.status_code == 200
    data = response.json()
    assert data["calls"] == []
    assert data["total"] == 0


def test_list_calls_with_data(client, sample_call_log):
    """Test call list returns data."""
    response = client.get("/api/calls")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["calls"]) == 1

    call = data["calls"][0]
    assert call["client_name"] == "PagePro"
    assert call["caller_number"] == "+639181234567"
    assert call["status"] == "in_progress"


def test_list_calls_filter_by_client(client, sample_call_log, sample_client):
    """Test filtering calls by client ID."""
    response = client.get(f"/api/calls?client_id={sample_client.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

    # Filter by non-existent client
    response = client.get("/api/calls?client_id=999")
    data = response.json()
    assert data["total"] == 0


def test_list_calls_pagination(client, sample_call_log):
    """Test pagination parameters."""
    response = client.get("/api/calls?limit=1&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["calls"]) <= 1


def test_list_clients(client, sample_client):
    """Test clients list endpoint."""
    response = client.get("/api/clients")
    assert response.status_code == 200
    data = response.json()
    assert len(data["clients"]) == 1
    assert data["clients"][0]["name"] == "PagePro"
