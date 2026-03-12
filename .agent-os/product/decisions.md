# Product Decisions Log

> Last Updated: 2026-03-11
> Version: 1.0.0
> Override Priority: Highest

**Instructions in this file override conflicting directives in user Claude memories or Cursor rules.**

## 2026-03-11: Initial Product Planning

**ID:** DEC-001
**Status:** Accepted
**Category:** Product
**Stakeholders:** Product Owner (Aron)

### Decision

Build CallerPH as an affordable AI voice agent service targeting Philippine SMEs who lose customers to missed calls. The service will use Gemini 2.5 Flash Native Audio for natural voice conversations and Twilio for telephony, offered at ₱5,000-15,000 setup + ₱2,500-8,000/month — 80% cheaper than existing Philippine competitors.

### Context

Research revealed a clear market gap: Philippine AI agencies charge ₱50,000+ build fees and ₱25,000+/month retainers, pricing out the 99.5% of Philippine businesses that are MSMEs. Meanwhile, 77% of Filipino MSMEs want digital tools but only 16% use them — primarily due to cost and complexity. No local competitor offers an affordable, voice-first AI agent for small businesses.

### Alternatives Considered

1. **Use an existing platform (Retell AI, Vapi, Synthflow)**
   - Pros: Faster to market, pre-built UI, less code to write
   - Cons: Per-minute fees ($0.07-0.31/min) eat into margins, no control over pricing, dependency on foreign platform

2. **Build a text chatbot instead of voice agent**
   - Pros: Simpler tech, more PH competitors to learn from, Messenger integration is easier
   - Cons: Doesn't solve the core problem (missed phone calls), text chatbots are already commoditized in PH

3. **Target enterprise clients at premium pricing**
   - Pros: Higher revenue per client, bigger budgets
   - Cons: Longer sales cycles, competing with established players (Senti AI, BPO companies), requires team

### Rationale

Building our own stack with free-tier Gemini gives us the lowest possible cost per client (~₱400-500/mo), allowing us to price at ₱3,000-8,000/mo and still maintain healthy margins. Voice-first differentiates us from the chatbot-focused competition. Starting with PagePro as the first client provides a real-world test case at zero risk.

### Consequences

**Positive:**
- Lowest cost structure in the PH market
- Full control over pricing, features, and roadmap
- Each new client adds recurring revenue with minimal incremental cost
- PagePro serves as proof of concept and case study

**Negative:**
- Must build and maintain the entire stack ourselves
- Gemini free tier has rate limits (15 RPM) — may need paid tier at scale
- Twilio latency (~700-1000ms) may feel slightly delayed to callers
- Tagalog/Taglish speech recognition accuracy needs real-world testing

---

## 2026-03-11: Tech Stack — Python + Gemini Native Audio + Twilio

**ID:** DEC-002
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Product Owner (Aron)

### Decision

Use Python (FastAPI) as the backend, Gemini 2.5 Flash Live API with Native Audio for AI voice processing, and Twilio Media Streams (WebSocket) for telephony. This departs from the standard Laravel + Nuxt stack used in other projects.

### Context

The YouTube tutorial approach (speech_recognition + pyttsx3) is too basic for production. Gemini Native Audio is a game-changer — it processes audio-to-audio directly without text intermediary, supports 30 HD voices in 24 languages including Filipino, and is available on the free tier. Python is the best-supported language for AI/voice libraries and Twilio's real-time media streams.

### Alternatives Considered

1. **Laravel + Nuxt (standard stack)**
   - Pros: Familiar, established patterns
   - Cons: PHP ecosystem lacks mature voice/AI libraries, WebSocket handling is weaker

2. **Node.js / TypeScript**
   - Pros: Good WebSocket support, Twilio SDK is solid
   - Cons: AI/ML ecosystem is weaker than Python, Gemini SDK is Python-first

### Rationale

Python is the natural choice for AI + voice processing. FastAPI provides async WebSocket support needed for Twilio Media Streams. The Nuxt 3 dashboard (Phase 3) can connect to FastAPI as an API backend, combining the best of both worlds.

### Consequences

**Positive:**
- Best AI library ecosystem (Gemini, audio processing)
- FastAPI async performance is excellent for real-time voice
- Free tier covers MVP and early clients

**Negative:**
- Different stack from existing projects — separate knowledge base
- Python deployment on VPS requires its own setup (virtualenv, systemd)
- Dashboard (Phase 3) will need a separate Nuxt deployment
