# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2026-03-11-voice-agent-mvp/spec.md

> Created: 2026-03-11
> Version: 1.0.0

## Endpoints

### POST /voice/incoming

**Purpose:** Twilio webhook — called when a phone call comes in. Returns TwiML instructing Twilio to connect the call to our WebSocket media stream.

**Triggered by:** Twilio (configured as the Voice URL for the phone number)

**Parameters (form-encoded from Twilio):**
- `CallSid` — Unique call identifier
- `From` — Caller's phone number
- `To` — Twilio phone number that was called
- `CallStatus` — Current call status

**Response:** TwiML XML
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://yourdomain.com/voice/stream/{call_sid}" />
  </Connect>
</Response>
```

**Logic:**
1. Validate Twilio webhook signature
2. Look up client by `To` phone number in database
3. If client found and active, return TwiML with WebSocket stream URL
4. If client not found, return TwiML with a sorry message and hang up
5. Create initial `call_logs` entry with status `in_progress`

**Errors:**
- 404: Unknown phone number (no client mapped)
- 403: Invalid Twilio signature

---

### WebSocket /voice/stream/{call_sid}

**Purpose:** Real-time bidirectional audio stream between Twilio and Gemini Native Audio

**Protocol:** WebSocket

**Flow:**
1. Twilio connects and sends `connected` event with stream metadata
2. Twilio sends `media` events containing base64-encoded mulaw/8000 audio chunks
3. Server converts audio to PCM/16000 and forwards to Gemini Live API
4. Gemini processes and returns audio response
5. Server converts Gemini's PCM/24000 response to mulaw/8000
6. Server sends audio back to Twilio as base64-encoded `media` events
7. On `stop` event, finalize call: generate summary, update call log

**Twilio Media Stream Events:**
- `connected` — Stream established, includes `streamSid`
- `start` — Stream metadata (encoding, sample rate, tracks)
- `media` — Audio data payload (base64 encoded)
- `stop` — Call ended

**Server → Twilio Events:**
- `media` — Audio response payload (base64 encoded)
- `clear` — Clear any queued audio (for interruption handling)

---

### POST /voice/status

**Purpose:** Twilio status callback — called when call status changes (completed, failed, etc.)

**Triggered by:** Twilio (configured as Status Callback URL)

**Parameters (form-encoded from Twilio):**
- `CallSid` — Unique call identifier
- `CallStatus` — New status (completed, failed, busy, no-answer)
- `CallDuration` — Call duration in seconds
- `From` — Caller's phone number

**Response:** 200 OK (empty)

**Logic:**
1. Find call log by `twilio_call_sid`
2. Update `ended_at`, `duration_seconds`, `status`
3. Trigger conversation summary generation (async)

**Errors:**
- 404: Call SID not found in database

---

### GET /api/calls

**Purpose:** Simple API to list recent call logs (for MVP testing, no auth required)

**Parameters (query string):**
- `client_id` — Filter by client (optional)
- `limit` — Number of results (default: 20, max: 100)
- `offset` — Pagination offset (default: 0)

**Response:**
```json
{
  "calls": [
    {
      "id": 1,
      "client_name": "PagePro",
      "caller_number": "+639171234567",
      "started_at": "2026-03-11T22:15:00Z",
      "duration_seconds": 120,
      "caller_name": "Juan Dela Cruz",
      "caller_inquiry": "Interested in Premium landing page package",
      "conversation_summary": "Caller asked about landing page services...",
      "status": "completed"
    }
  ],
  "total": 15
}
```

**Errors:**
- 400: Invalid query parameters

---

### GET /health

**Purpose:** Health check endpoint for monitoring

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "active_clients": 1,
  "uptime_seconds": 86400
}
```
