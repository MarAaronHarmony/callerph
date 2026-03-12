# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2026-03-11-voice-agent-mvp/spec.md

> Created: 2026-03-11
> Version: 1.0.0

## Test Framework

- **Framework:** pytest
- **Async support:** pytest-asyncio
- **HTTP testing:** httpx (FastAPI TestClient)
- **Coverage:** pytest-cov

## Test Coverage

### Unit Tests

**SystemPromptLoader**
- Test loading a valid prompt markdown file returns correct content
- Test loading a nonexistent prompt file raises appropriate error
- Test prompt file path is resolved relative to prompts/ directory

**AudioConverter**
- Test mulaw/8000 to PCM/16000 conversion produces valid PCM audio
- Test PCM/24000 to mulaw/8000 conversion produces valid mulaw audio
- Test base64 encoding/decoding round-trip preserves audio data
- Test empty audio input is handled gracefully

**ClientLookup**
- Test lookup by phone number returns correct client
- Test lookup with unknown phone number returns None
- Test lookup with inactive client returns None

**CallLog Model**
- Test creating a call log entry with required fields
- Test updating call log with duration and summary
- Test status transitions (in_progress → completed, in_progress → failed)

### Integration Tests

**Twilio Incoming Call Webhook**
- Test POST /voice/incoming with valid Twilio payload returns correct TwiML
- Test TwiML response contains WebSocket stream URL with call SID
- Test unknown phone number returns error TwiML
- Test call log entry is created in database on incoming call

**Twilio Status Callback**
- Test POST /voice/status updates call log with duration and status
- Test completed status triggers summary generation
- Test unknown CallSid returns 404

**Call Log API**
- Test GET /api/calls returns list of call logs
- Test filtering by client_id works correctly
- Test pagination with limit and offset
- Test empty database returns empty list

**Health Check**
- Test GET /health returns 200 with status ok
- Test active_clients count reflects database state

### Feature Tests (Manual / E2E)

**Full Call Flow**
- Call the Twilio number from a real phone
- Verify AI agent picks up and greets caller
- Ask about PagePro services and verify accurate response
- Provide name and contact info, verify agent acknowledges
- Hang up and verify call log is created with summary
- Verify caller_name and caller_inquiry are populated

**System Prompt Switching**
- Create a new prompt file for a different business
- Add client mapping in database
- Call the new number and verify agent responds with new business context

**Language Handling**
- Call and speak in English — verify English response
- Call and speak in Tagalog — verify appropriate response
- Call and switch between languages mid-conversation

## Mocking Requirements

- **Twilio:** Mock webhook payloads using `twilio` SDK's test utilities. Mock WebSocket connections using `websockets` test server.
- **Gemini Live API:** Mock the Gemini WebSocket connection to return pre-recorded audio responses. Use recorded audio fixtures for testing audio conversion.
- **Database:** Use in-memory SQLite for test isolation. Reset between tests.
- **Time:** Mock `datetime.utcnow` for consistent timestamp testing.

## Test File Structure

```
tests/
├── conftest.py              # Shared fixtures (test client, db, mocks)
├── test_audio_converter.py  # Audio format conversion tests
├── test_prompt_loader.py    # System prompt loading tests
├── test_client_lookup.py    # Client lookup by phone number
├── test_call_log.py         # CallLog model tests
├── test_webhook.py          # Twilio webhook endpoint tests
├── test_status_callback.py  # Twilio status callback tests
├── test_calls_api.py        # Call log API endpoint tests
├── test_health.py           # Health check tests
└── fixtures/
    ├── sample_prompt.md     # Test prompt file
    └── audio_samples/       # Short audio clips for conversion tests
```
