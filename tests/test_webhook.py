"""Tests for Twilio incoming call webhook."""

import os

from sqlmodel import select

from app.models.call_log import CallLog


def _post_form(client, url, data):
    """Helper to post form data with correct content type."""
    return client.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})


def test_incoming_call_valid(client, sample_client):
    """Test valid incoming call returns TwiML with stream."""
    os.environ["APP_BASE_URL"] = "https://test.ngrok.app"

    response = _post_form(client, "/voice/incoming", {
        "CallSid": "CA_test_webhook_001",
        "From": "+639181234567",
        "To": "+639171234567",
        "CallStatus": "ringing",
    })

    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    body = response.text
    assert "<Connect>" in body or "<Stream" in body


def test_incoming_call_creates_log(client, sample_client, session):
    """Test that incoming call creates a call log entry."""
    os.environ["APP_BASE_URL"] = "https://test.ngrok.app"

    _post_form(client, "/voice/incoming", {
        "CallSid": "CA_test_webhook_002",
        "From": "+639181234567",
        "To": "+639171234567",
        "CallStatus": "ringing",
    })

    call_log = session.exec(
        select(CallLog).where(CallLog.twilio_call_sid == "CA_test_webhook_002")
    ).first()

    assert call_log is not None
    assert call_log.caller_number == "+639181234567"
    assert call_log.status == "in_progress"


def test_incoming_call_unknown_number(client, sample_client):
    """Test call to unknown number returns error TwiML."""
    response = _post_form(client, "/voice/incoming", {
        "CallSid": "CA_test_unknown",
        "From": "+639181234567",
        "To": "+639999999999",
        "CallStatus": "ringing",
    })

    assert response.status_code == 200
    body = response.text
    assert "not currently active" in body.lower() or "Sorry" in body
