# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2026-03-11-voice-agent-mvp/spec.md

> Created: 2026-03-11
> Status: In Progress

## Execution Strategy

### Parallel Execution Map

```
Round 1: Task 1 (Scaffolding)
    │
Round 2: ├── Task 2 (Database)        ← parallel
    │    ├── Task 3 (Prompts)          ← parallel
    │    └── Task 5 (Audio Converter)  ← parallel
    │
Round 3: ├── Task 4 (Twilio Webhook)  ← needs Task 2
    │    └── Task 6 (Gemini Agent)     ← needs Task 5
    │
Round 4: ├── Task 7 (WebSocket Bridge) ← needs Tasks 4, 5, 6
    │    └── Task 8 (Status/API)       ← needs Tasks 2, 4
    │
Round 5: └── Task 9 (Deploy + E2E)    ← needs everything
```

### Dev Tools Setup (Before Task 1)

| Tool | Install Command | Purpose |
|------|----------------|---------|
| ngrok | `choco install ngrok` or download from ngrok.com | Tunnel localhost to public URL for Twilio webhooks during local dev |
| Twilio CLI | `npm install -g twilio-cli` | Manage phone numbers, test webhooks, view logs from terminal |
| ruff | Added to dev requirements | Python linter + formatter (replaces black, isort, flake8) |

## Tasks

### Round 1: Foundation

- [x] 1. Project scaffolding and configuration
  - [x] 1.1 Initialize Python project with `requirements.txt` (core + dev dependencies) and virtual environment
  - [x] 1.2 Create project directory structure (`app/voice/`, `app/models/`, `app/db/`, `app/api/`, `prompts/`, `tests/fixtures/`)
  - [x] 1.3 Set up `.env.example` with all required environment variables (Twilio credentials, Gemini API key, database URL, ngrok URL)
  - [x] 1.4 Create `app/config.py` with Pydantic Settings for type-safe config loading
  - [x] 1.5 Create `app/main.py` FastAPI application entry with health check endpoint
  - [x] 1.6 Create `.gitignore` (exclude .env, __pycache__, *.db, .venv)
  - [x] 1.7 Write tests for health check endpoint
  - [ ] 1.8 Install and configure dev tools (ngrok account, Twilio CLI login, ruff config)
  - [x] 1.9 Verify all tests pass and server starts with `uvicorn`

### Round 2: Independent Components (Parallel)

- [x] 2. Database models and client lookup
  - [x] 2.1 Write tests for Client and CallLog models (create, read, update)
  - [x] 2.2 Create `app/db/database.py` with SQLite engine and session management
  - [x] 2.3 Create `app/models/client.py` with Client SQLModel
  - [x] 2.4 Create `app/models/call_log.py` with CallLog SQLModel
  - [x] 2.5 Create database initialization (auto-create tables on startup)
  - [x] 2.6 Write tests for client lookup by phone number
  - [x] 2.7 Create `app/db/seed.py` — seed script for PagePro client record
  - [x] 2.8 Verify all tests pass

- [x] 3. System prompt engine
  - [x] 3.1 Write tests for prompt loading from markdown files
  - [x] 3.2 Create `app/voice/prompts.py` — load and parse prompt markdown files
  - [x] 3.3 Create `prompts/pagepro.md` — full PagePro system prompt
  - [x] 3.4 Implement phone number → prompt file mapping via Client model
  - [x] 3.5 Verify all tests pass

- [x] 5. Audio format converter
  - [x] 5.1 Write tests for mulaw/8000 ↔ PCM/16000 and PCM/24000 ↔ mulaw/8000 conversions
  - [x] 5.2 Create `app/voice/audio.py` with conversion functions (mulaw_to_pcm, pcm_to_mulaw, resample)
  - [x] 5.3 Implement base64 encode/decode helpers for Twilio media format
  - [x] 5.4 Create test audio fixtures in `tests/fixtures/audio_samples/`
  - [x] 5.5 Verify all tests pass

### Round 3: Integration Components (Parallel)

- [x] 4. Twilio incoming call webhook
  - [x] 4.1 Write tests for POST /voice/incoming endpoint (valid call, unknown number, TwiML response format)
  - [x] 4.2 Create `app/voice/handler.py` with incoming call webhook handler
  - [x] 4.3 Implement TwiML response generation with Media Stream connection
  - [ ] 4.4 Implement Twilio webhook signature validation
  - [x] 4.5 Create initial call log entry on incoming call
  - [x] 4.6 Register route in FastAPI app
  - [ ] 4.7 Local test: start ngrok + uvicorn, configure Twilio phone number to point to ngrok URL, make a test call
  - [x] 4.8 Verify all tests pass

- [x] 6. Gemini Native Audio integration
  - [x] 6.1 Create `app/voice/gemini_agent.py` — Gemini 2.5 Flash Live API client
  - [x] 6.2 Implement WebSocket connection to Gemini Live API with Native Audio mode
  - [x] 6.3 Implement system prompt injection at session start
  - [x] 6.4 Implement audio input streaming (send caller audio chunks to Gemini)
  - [x] 6.5 Implement audio response receiving (get Gemini audio response chunks)
  - [x] 6.6 Implement conversation summary generation at call end (text API call)
  - [ ] 6.7 Test with a local audio file to verify Gemini responds correctly
  - [ ] 6.8 Verify Gemini handles Tagalog/Taglish input correctly

### Round 4: Bridge & API (Parallel)

- [x] 7. WebSocket media stream (Twilio ↔ Gemini bridge)
  - [x] 7.1 Create WebSocket endpoint in `app/voice/handler.py` — `/voice/stream/{call_sid}`
  - [x] 7.2 Handle Twilio Media Stream events (connected, start, media, stop)
  - [x] 7.3 Bridge incoming Twilio audio → audio converter → Gemini agent
  - [x] 7.4 Bridge Gemini response audio → audio converter → Twilio stream
  - [x] 7.5 Handle caller interruption (clear queued audio when new speech detected)
  - [x] 7.6 Handle call end — generate summary, update call log with duration and summary
  - [ ] 7.7 Local E2E test: ngrok + full pipeline, call the number and have a real conversation
  - [ ] 7.8 Integration test: simulate full call flow with mocked Gemini

- [x] 8. Twilio status callback and call log API
  - [x] 8.1 Write tests for POST /voice/status and GET /api/calls
  - [x] 8.2 Create POST /voice/status handler — update call log on call completion
  - [x] 8.3 Create GET /api/calls endpoint — list call logs with filtering and pagination
  - [x] 8.4 Register routes in FastAPI app
  - [x] 8.5 Verify all tests pass

### Round 5: Production

- [ ] 9. Deployment and end-to-end testing
  - [ ] 9.1 Deploy to VPS — set up Python venv, install dependencies, configure systemd service
  - [ ] 9.2 Set up HTTPS with Let's Encrypt (required for Twilio webhooks)
  - [ ] 9.3 Point domain subdomain (e.g., `voice.yourdomain.com`) to VPS
  - [ ] 9.4 Configure Twilio phone number webhooks (Voice URL → /voice/incoming, Status Callback → /voice/status)
  - [ ] 9.5 Seed production database with PagePro client record
  - [ ] 9.6 End-to-end test: call the Twilio PH number from a real phone
  - [ ] 9.7 Verify call log is created with conversation summary
  - [ ] 9.8 Verify GET /api/calls returns the test call data
  - [ ] 9.9 Run full test suite one final time to confirm everything passes
