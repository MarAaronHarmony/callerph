# Product Roadmap

> Last Updated: 2026-03-11
> Version: 1.0.0
> Status: Planning

## Phase 1: Core MVP — Voice Agent (2 weeks)

**Goal:** Build a working AI voice agent that answers a Twilio phone call using Gemini Native Audio, customized for PagePro as the first test client
**Success Criteria:** Call the Twilio PH number, have a natural conversation about PagePro services, and receive a lead capture summary

### Must-Have Features

- [ ] Twilio account setup with PH phone number `S`
- [ ] Gemini 2.5 Flash Live API integration with Native Audio `M`
- [ ] Twilio Media Streams (WebSocket) for real-time audio streaming `M`
- [ ] System prompt engine — load business-specific instructions per phone number `S`
- [ ] PagePro demo system prompt (services, pricing, FAQs in English + Taglish) `S`
- [ ] Basic call logging to SQLite (caller number, timestamp, duration) `S`
- [ ] Deployment to VPS with HTTPS endpoint for Twilio webhooks `S`

### Should-Have Features

- [ ] Conversation summary generation after call ends `S`
- [ ] Environment-based config (.env for API keys, Twilio credentials) `XS`

### Dependencies

- Google AI Studio API key (free)
- Twilio account with PH number (~$5/mo)
- VPS with Python 3.11+ and HTTPS

## Phase 2: Lead Capture & Notifications (1 week)

**Goal:** Capture caller information during conversations and notify the business owner immediately
**Success Criteria:** After a call, business owner receives SMS/email with caller name, number, inquiry, and conversation summary

### Must-Have Features

- [ ] Lead extraction from conversation (name, contact, inquiry type, callback preference) `M`
- [ ] Lead storage in database with status tracking `S`
- [ ] SMS notification to business owner after each call (via Twilio SMS) `S`
- [ ] Email notification option (via SMTP or SendGrid free tier) `S`

### Should-Have Features

- [ ] Lead status management (new, contacted, converted, lost) `S`
- [ ] Daily summary digest (total calls, new leads, missed) `S`

### Dependencies

- Phase 1 complete
- Business owner contact details for notifications

## Phase 3: Client Dashboard (2 weeks)

**Goal:** Web dashboard where business owners can view call logs, leads, and manage their voice agent settings
**Success Criteria:** Client logs in, sees today's calls, reviews leads, and can update business info

### Must-Have Features

- [ ] FastAPI JWT authentication system `M`
- [ ] Nuxt 3 client dashboard with Vuetify `L`
- [ ] Call log view — list of all calls with timestamp, duration, summary `M`
- [ ] Lead management view — table of captured leads with status `M`
- [ ] Business profile editor — update hours, services, pricing, FAQs `S`

### Should-Have Features

- [ ] Basic analytics — calls per day/week chart `S`
- [ ] System prompt preview/test from dashboard `M`
- [ ] Mobile-responsive design `S`

### Dependencies

- Phase 2 complete
- Domain pointed to VPS

## Phase 4: Multi-Client & Admin (2 weeks)

**Goal:** Support multiple business clients from a single deployment with an admin panel for you to manage all clients
**Success Criteria:** 3+ clients running simultaneously, each with their own phone number and system prompt, managed from one admin dashboard

### Must-Have Features

- [ ] Multi-tenant architecture — route calls to correct client by phone number `M`
- [ ] Admin dashboard — manage all clients, view all call logs, deploy new agents `L`
- [ ] Client onboarding flow — create new client, assign number, write prompt `M`
- [ ] Per-client billing tracking (cost per client per month) `S`

### Should-Have Features

- [ ] Client self-service prompt editor with guardrails `M`
- [ ] Automated Twilio number provisioning `S`
- [ ] Usage limits and overage alerts `S`

### Dependencies

- Phase 3 complete
- Multiple Twilio PH numbers

## Phase 5: Scale & Revenue (3+ weeks)

**Goal:** Production-grade system ready for 20+ clients with marketing site, demo mode, and payment collection
**Success Criteria:** Landing page live, demo mode working, GCash/Maya payment integrated, 5+ paying clients

### Must-Have Features

- [ ] CallerPH marketing landing page `M`
- [ ] Live demo mode — prospects call a demo number and experience the agent `M`
- [ ] GCash/Maya payment integration for monthly retainer collection `L`
- [ ] Client referral tracking `S`
- [ ] Production monitoring and alerting (uptime, error tracking) `M`

### Should-Have Features

- [ ] Voice customization options (tone, speed, personality) `M`
- [ ] Call recording with consent (for quality assurance) `M`
- [ ] Tagalog-first system prompt templates for common business types `S`
- [ ] WhatsApp/Messenger integration as upsell `L`
- [ ] Migrate from SQLite to PostgreSQL `M`

### Dependencies

- Phase 4 stable with 3+ clients
- Payment gateway registration (GCash/Maya merchant)
- Business registration (DTI/BIR) for legitimate invoicing
