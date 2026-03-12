"""Tests for Twilio status callback."""

from sqlmodel import Session, select

from app.db.database import get_engine
from app.models.call_log import CallLog


def _post_form(client, url, data):
    """Helper to post form data with correct content type."""
    return client.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})


def test_status_callback_completed(client, sample_call_log):
    """Test status callback updates call log."""
    response = _post_form(client, "/voice/status", {
        "CallSid": "CA1234567890abcdef",
        "CallStatus": "completed",
        "CallDuration": "120",
    })

    assert response.status_code == 200

    # Use fresh session to read updated data
    with Session(get_engine()) as fresh_session:
        updated = fresh_session.exec(
            select(CallLog).where(CallLog.twilio_call_sid == "CA1234567890abcdef")
        ).first()

        assert updated is not None
        assert updated.status == "completed"
        assert updated.duration_seconds == 120


def test_status_callback_failed(client, sample_call_log):
    """Test failed call status update."""
    response = _post_form(client, "/voice/status", {
        "CallSid": "CA1234567890abcdef",
        "CallStatus": "failed",
    })

    assert response.status_code == 200

    with Session(get_engine()) as fresh_session:
        updated = fresh_session.exec(
            select(CallLog).where(CallLog.twilio_call_sid == "CA1234567890abcdef")
        ).first()

        assert updated is not None
        assert updated.status == "failed"
        assert updated.ended_at is not None


def test_status_callback_unknown_sid(client, sample_client):
    """Test status callback for unknown call SID doesn't crash."""
    response = _post_form(client, "/voice/status", {
        "CallSid": "CA_nonexistent",
        "CallStatus": "completed",
    })

    assert response.status_code == 200
