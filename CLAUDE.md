# CallerPH

> Affordable AI Voice Agent Service for Philippine Small Businesses

## Agent OS Documentation

### Product Context
- **Mission & Vision:** @.agent-os/product/mission.md
- **Technical Architecture:** @.agent-os/product/tech-stack.md
- **Development Roadmap:** @.agent-os/product/roadmap.md
- **Decision History:** @.agent-os/product/decisions.md

### Development Standards
- **Code Style:** @~/.agent-os/standards/code-style.md
- **Best Practices:** @~/.agent-os/standards/best-practices.md

### Project Management
- **Active Specs:** @.agent-os/specs/
- **Spec Planning:** Use `@~/.agent-os/instructions/create-spec.md`
- **Tasks Execution:** Use `@~/.agent-os/instructions/execute-tasks.md`

## Project-Specific Standards

### Language & Framework
- **Backend:** Python 3.11+ with FastAPI
- **AI Engine:** Google Gemini 2.5 Flash Live API (Native Audio)
- **Telephony:** Twilio Programmable Voice + Media Streams (WebSocket)
- **Database:** SQLite (MVP) → PostgreSQL (scale)
- **Dashboard (Phase 3):** Nuxt 3 + Vuetify 3

### Code Style (Python)
- Follow PEP 8 standards
- Use type hints throughout
- Async/await for all I/O operations
- Use `pydantic` for data validation
- Environment variables via `.env` + `python-dotenv`

### Project Structure
```
callerph/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py             # Settings and environment
│   ├── voice/
│   │   ├── handler.py        # Twilio webhook handler
│   │   ├── gemini_agent.py   # Gemini Live API integration
│   │   └── prompts.py        # System prompt loader
│   ├── models/
│   │   ├── call_log.py       # Call log model
│   │   └── lead.py           # Lead capture model
│   ├── api/
│   │   └── routes.py         # API routes (dashboard)
│   └── db/
│       └── database.py       # Database connection
├── prompts/
│   └── pagepro.md            # PagePro system prompt
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

### Key Conventions
- System prompts live in `prompts/` as markdown files
- One prompt file per client business
- Call routing is by Twilio phone number → client mapping
- All Twilio webhooks go through `app/voice/handler.py`

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check @.agent-os/product/roadmap.md for current priorities
2. **Then**, follow the appropriate instruction file:
   - For new features: @~/.agent-os/instructions/create-spec.md
   - For tasks execution: @~/.agent-os/instructions/execute-tasks.md
3. **Always**, adhere to the standards in the files listed above

## Important Notes

- This project uses **Python**, not the standard Laravel + Nuxt stack
- Product-specific files in `.agent-os/product/` override any global standards
- User's specific instructions override (or amend) instructions found in `.agent-os/specs/...`
- Always adhere to established patterns, code style, and best practices documented above
- **First test client:** PagePro (https://pagepro.live/) — landing page service for Filipino entrepreneurs
