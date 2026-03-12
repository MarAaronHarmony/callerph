# Spec Requirements Document

> Spec: Voice Agent MVP
> Created: 2026-03-11
> Status: Planning

## Overview

Build a fully functional AI voice agent that answers incoming phone calls via a Twilio PH number, conducts natural conversations using Gemini 2.5 Flash Native Audio, and logs call details — deployed on an existing VPS with PagePro as the first test client.

## User Stories

### A Caller Reaches PagePro After Hours

As a potential PagePro customer, I want to call and speak with someone about landing page services at any time, so that I can get answers and leave my contact info even when Aron is unavailable.

A caller dials the PagePro Twilio number at 10 PM. The AI agent picks up instantly, greets them warmly in English/Taglish, explains PagePro's services (Basic ₱15K, Premium ₱25K), answers FAQs about delivery time, GCash payment, and revisions, then collects the caller's name, contact number, and what they need. After the call, the conversation summary is stored in the database.

### The Business Owner Reviews Missed-Hour Leads

As the PagePro business owner, I want to see a log of every call the AI agent handled, so that I can follow up with leads the next morning.

Aron checks the call log (via database query or simple API endpoint) and sees 3 calls from last night — each with caller name, phone number, inquiry type, and a brief conversation summary. He calls them back and converts 2 into paying clients.

### Deploying a New Client Takes Minutes

As the CallerPH operator, I want to onboard a new business by simply writing a system prompt file, so that I can scale without rebuilding the system.

Aron signs a new client (a dental clinic). He creates `prompts/dental-clinic.md` with the clinic's services, hours, pricing, and FAQs. He maps the clinic's Twilio number to this prompt in the config. The voice agent now answers calls for the dental clinic with zero code changes.

## Spec Scope

1. **Twilio Integration** - Set up a PH phone number with Twilio Media Streams (WebSocket) to receive and stream call audio in real-time
2. **Gemini Native Audio Engine** - Connect Gemini 2.5 Flash Live API to process incoming audio and generate spoken responses directly (audio-to-audio)
3. **System Prompt Engine** - Load business-specific system prompts from markdown files, mapped to Twilio phone numbers
4. **PagePro Demo Prompt** - Write a complete system prompt for PagePro covering services, pricing, FAQs, and lead capture instructions
5. **Call Logging** - Store call metadata (caller number, timestamp, duration, conversation summary) in SQLite via SQLModel

## Out of Scope

- Client-facing web dashboard (Phase 3)
- Multi-tenant admin panel (Phase 4)
- SMS/email notifications after calls (Phase 2)
- Lead status management and CRM features (Phase 2)
- Payment collection or billing (Phase 5)
- Call recording or audio storage
- Outbound calling capabilities

## Expected Deliverable

1. Call the Twilio PH number from any phone, have a natural voice conversation about PagePro's services in English or Taglish, and receive intelligent responses
2. After the call ends, query the SQLite database and see the call log entry with caller number, timestamp, duration, and conversation summary
3. Create a new `.md` prompt file for a different business, update the config mapping, and have the agent answer calls for that business without any code changes

## Spec Documentation

- Tasks: @.agent-os/specs/2026-03-11-voice-agent-mvp/tasks.md
- Technical Specification: @.agent-os/specs/2026-03-11-voice-agent-mvp/sub-specs/technical-spec.md
- API Specification: @.agent-os/specs/2026-03-11-voice-agent-mvp/sub-specs/api-spec.md
- Database Schema: @.agent-os/specs/2026-03-11-voice-agent-mvp/sub-specs/database-schema.md
- Tests Specification: @.agent-os/specs/2026-03-11-voice-agent-mvp/sub-specs/tests.md
