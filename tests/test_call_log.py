"""Tests for CallLog model."""

from datetime import datetime

from app.models.call_log import CallLog


def test_create_call_log(session, sample_client):
    call_log = CallLog(
        client_id=sample_client.id,
        twilio_call_sid="CA_test_123",
        caller_number="+639181111111",
        status="in_progress",
    )
    session.add(call_log)
    session.commit()
    session.refresh(call_log)

    assert call_log.id is not None
    assert call_log.client_id == sample_client.id
    assert call_log.caller_number == "+639181111111"
    assert call_log.status == "in_progress"


def test_update_call_log_completion(session, sample_call_log):
    sample_call_log.status = "completed"
    sample_call_log.ended_at = datetime.utcnow()
    sample_call_log.duration_seconds = 120
    sample_call_log.conversation_summary = "Caller asked about Basic package."
    session.add(sample_call_log)
    session.commit()
    session.refresh(sample_call_log)

    assert sample_call_log.status == "completed"
    assert sample_call_log.duration_seconds == 120
    assert sample_call_log.ended_at is not None


def test_call_log_with_lead_info(session, sample_client):
    call_log = CallLog(
        client_id=sample_client.id,
        twilio_call_sid="CA_lead_456",
        caller_number="+639182222222",
        caller_name="Juan Dela Cruz",
        caller_inquiry="Interested in Premium landing page package",
        status="completed",
    )
    session.add(call_log)
    session.commit()
    session.refresh(call_log)

    assert call_log.caller_name == "Juan Dela Cruz"
    assert "Premium" in call_log.caller_inquiry
