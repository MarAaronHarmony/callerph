# Technical Stack

> Last Updated: 2026-03-11
> Version: 1.0.0

## Core Technologies

### Application Framework
- **Language:** Python 3.11+
- **Web Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Purpose:** Handles Twilio webhooks, serves client dashboard API, manages voice agent logic

### AI & Voice
- **AI Engine:** Google Gemini 2.5 Flash (Live API with Native Audio)
- **Audio Processing:** Gemini Native Audio (speech-to-speech, no separate STT/TTS needed)
- **Fallback TTS:** Google Cloud Text-to-Speech (free tier)
- **Fallback STT:** Google Cloud Speech-to-Text (free tier)
- **API Access:** Google AI Studio free tier (15 RPM, 1,500 requests/day)

### Telephony
- **Provider:** Twilio
- **Features:** Programmable Voice, WebSocket streaming, PH phone numbers
- **Integration:** Twilio Media Streams (WebSocket) for real-time audio
- **Cost:** ~$5/mo per PH number + per-minute call charges

### Database
- **Engine:** SQLite (MVP) → PostgreSQL (scale)
- **ORM:** SQLAlchemy / SQLModel
- **Purpose:** Call logs, client configurations, lead data, user accounts

## Frontend Stack (Client Dashboard — Phase 2)

### Framework
- **Framework:** Nuxt 3
- **Rendering:** SSR / Static
- **Language:** TypeScript + Composition API

### UI Libraries
- **UI Framework:** Vuetify 3
- **CSS Framework:** TailwindCSS

### Auth
- **Method:** JWT tokens via FastAPI backend
- **Storage:** localStorage / httpOnly cookies

## Infrastructure

### Hosting
- **Application Server:** Existing work VPS
- **Footprint:** Minimal — small Python process + SQLite file
- **SSL:** Let's Encrypt (for Twilio webhook HTTPS requirement)

### Domain
- **Domain:** User-owned (TBD — callerph.com or similar)
- **DNS:** Pointed to VPS

### Environment Separation
- **Local:** Development on Windows (MINGW64)
- **Production:** VPS deployment

## Deployment

### Strategy
- **Method:** Git pull + systemd service (or PM2/supervisor)
- **CI/CD:** Manual initially → GitHub Actions later

### Code Repository
- **Platform:** GitHub
- **Account:** dacoroon@gmail.com
- **Repository:** TBD (github.com/dacoroon/callerph)

## Development Tools

### Local Development
- **ngrok** — Tunnel localhost to public HTTPS URL for Twilio webhook testing
- **Twilio CLI** — Manage phone numbers, inspect call logs, test webhooks from terminal
- **ruff** — Python linter + formatter (replaces black, isort, flake8 in one tool)

### Local Dev Workflow
```
1. Start FastAPI:    uvicorn app.main:app --reload --port 8000
2. Start ngrok:      ngrok http 8000
3. Copy ngrok URL → set as Twilio Voice webhook URL
4. Call Twilio number → audio flows through ngrok → localhost → Gemini → back
```

## Dependencies (Python)

### Core
- `fastapi` — Web framework
- `uvicorn[standard]` — ASGI server with WebSocket support
- `twilio` — Twilio SDK
- `google-genai` — Gemini API client
- `websockets` — WebSocket handling for Twilio Media Streams
- `sqlmodel` — Database ORM
- `python-dotenv` — Environment variables
- `pydantic` — Data validation
- `pydantic-settings` — Type-safe settings management

### Dev Dependencies
- `pytest` — Test runner
- `pytest-asyncio` — Async test support for FastAPI + WebSockets
- `httpx` — FastAPI async test client
- `pytest-cov` — Test coverage reporting
- `ruff` — Linter + formatter

### Optional / Phase 2+
- `jinja2` — Email/SMS templates
- `alembic` — Database migrations (when moving to PostgreSQL)

## Cost Structure Per Client

| Item | Monthly Cost |
|------|-------------|
| Twilio PH number | ~$5 (₱280) |
| Twilio call minutes (~200 min) | ~$2-4 (₱110-220) |
| Gemini API | $0 (free tier) |
| VPS (shared) | $0 (existing) |
| **Total per client** | **~$7-9 (₱390-500)** |
