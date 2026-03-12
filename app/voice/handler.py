"""Twilio voice webhook handlers — incoming calls and WebSocket media stream."""

import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlmodel import Session
from twilio.twiml.voice_response import Connect, VoiceResponse

from app.config import settings
from app.db.database import get_engine
from app.models.call_log import CallLog
from app.models.client import Client
from app.voice.audio import gemini_to_twilio, twilio_to_gemini
from app.voice.gemini_agent import GeminiVoiceAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


def _lookup_client(phone_number: str) -> Client | None:
    """Look up a client by their Twilio phone number."""
    from sqlmodel import select

    with Session(get_engine()) as session:
        return session.exec(
            select(Client).where(
                Client.phone_number == phone_number, Client.is_active == True  # noqa: E712
            )
        ).first()


def _create_call_log(client_id: int, call_sid: str, caller_number: str) -> CallLog:
    """Create an initial call log entry."""
    with Session(get_engine()) as session:
        call_log = CallLog(
            client_id=client_id,
            twilio_call_sid=call_sid,
            caller_number=caller_number,
            status="in_progress",
        )
        session.add(call_log)
        session.commit()
        session.refresh(call_log)
        return call_log


@router.post("/incoming")
async def incoming_call(request: Request):
    """Handle incoming Twilio voice call.

    Returns TwiML that connects the call to our WebSocket media stream.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    from_number = form_data.get("From", "")
    to_number = form_data.get("To", "")

    logger.info(f"Incoming call: {from_number} -> {to_number} (SID: {call_sid})")

    # Look up client by the number that was called
    client = _lookup_client(to_number)

    if not client:
        logger.warning(f"No client mapped to number: {to_number}")
        response = VoiceResponse()
        response.say(
            "Sorry, this number is not currently active. Please try again later.",
            voice="Polly.Joanna",
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Create call log entry
    _create_call_log(client_id=client.id, call_sid=call_sid, caller_number=from_number)

    # Build TwiML to connect to our WebSocket
    response = VoiceResponse()
    connect = Connect()
    stream_url = f"wss://{_get_host(request)}/voice/stream/{call_sid}"
    connect.stream(url=stream_url)
    response.append(connect)

    logger.info(f"Connecting call {call_sid} to stream: {stream_url}")
    return Response(content=str(response), media_type="application/xml")


def _get_host(request: Request) -> str:
    """Get the host from the request or fall back to config."""
    if settings.app_base_url and settings.app_base_url != "http://localhost:8000":
        # Strip protocol for WebSocket URL
        return settings.app_base_url.replace("https://", "").replace("http://", "")
    return request.headers.get("host", "localhost:8000")


@router.websocket("/stream/{call_sid}")
async def media_stream(websocket: WebSocket, call_sid: str):
    """Handle real-time audio stream between Twilio and Gemini.

    Uses an asyncio.Queue to decouple Gemini's background receive loop from
    WebSocket sends, avoiding concurrent access to the WebSocket object.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for call: {call_sid}")

    stream_sid = None
    gemini_agent = None
    outgoing_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def _outgoing_sender():
        """Drain the outgoing queue and send audio to Twilio via WebSocket.

        Runs as a separate task so only this coroutine ever calls
        websocket.send_text(), avoiding concurrent WebSocket writes.
        """
        try:
            while True:
                audio_data = await outgoing_queue.get()
                if audio_data is None:
                    break
                if not stream_sid:
                    continue
                try:
                    payload = gemini_to_twilio(audio_data)
                    message = {
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {"payload": payload},
                    }
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending audio to Twilio: {e}", exc_info=True)
        except asyncio.CancelledError:
            pass

    sender_task = asyncio.create_task(_outgoing_sender())

    async def _queue_audio(audio_data: bytes):
        """Callback given to GeminiVoiceAgent — just enqueues, never touches WS."""
        await outgoing_queue.put(audio_data)

    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            event_type = data.get("event")

            if event_type == "connected":
                logger.info(f"Twilio stream connected for call: {call_sid}")

            elif event_type == "start":
                start_data = data["start"]
                stream_sid = start_data["streamSid"]
                logger.info(
                    f"Stream started: SID={stream_sid}, "
                    f"tracks={start_data.get('tracks')}, "
                    f"mediaFormat={start_data.get('mediaFormat')}"
                )
                call_log = _get_call_log(call_sid)
                if call_log:
                    client = _get_client(call_log.client_id)
                    if client:
                        prompt = _load_prompt_safe(client.prompt_file)
                        if prompt:
                            gemini_agent = GeminiVoiceAgent(
                                system_prompt=prompt,
                                call_sid=call_sid,
                                on_audio_response=_queue_audio,
                            )
                            await gemini_agent.connect()
                            logger.info(
                                f"Gemini agent started for call {call_sid} "
                                f"(client: {client.name})"
                            )

            elif event_type == "media":
                if gemini_agent and gemini_agent.is_connected:
                    media_data = data["media"]
                    payload = media_data["payload"]
                    # Log raw payload stats periodically
                    chunk_num = media_data.get("chunk", "?")
                    if str(chunk_num) in ("1", "50", "100", "200", "500"):
                        import base64
                        raw = base64.b64decode(payload)
                        logger.info(
                            f"Twilio media chunk #{chunk_num}: "
                            f"track={media_data.get('track')}, "
                            f"raw_len={len(raw)}, "
                            f"first_bytes={raw[:8].hex()}, "
                            f"payload_preview={payload[:20]}"
                        )
                    pcm_audio = twilio_to_gemini(payload)
                    await gemini_agent.send_audio(pcm_audio)

            elif event_type == "stop":
                logger.info(f"Twilio stream stopped for call: {call_sid}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call: {call_sid}")
    except Exception as e:
        logger.error(f"Error in media stream for call {call_sid}: {e}", exc_info=True)
    finally:
        # Clean up: disconnect Gemini, stop sender task, finalize call
        if gemini_agent:
            summary = await gemini_agent.generate_summary()
            await gemini_agent.disconnect()
            _finalize_call(call_sid, summary)
        else:
            summary = None

        await outgoing_queue.put(None)  # signal sender to stop
        sender_task.cancel()
        try:
            await sender_task
        except asyncio.CancelledError:
            pass



def _get_call_log(call_sid: str) -> CallLog | None:
    """Get call log by Twilio call SID."""
    from sqlmodel import select

    with Session(get_engine()) as session:
        return session.exec(
            select(CallLog).where(CallLog.twilio_call_sid == call_sid)
        ).first()


def _get_client(client_id: int) -> Client | None:
    """Get client by ID."""
    with Session(get_engine()) as session:
        return session.get(Client, client_id)


def _load_prompt_safe(prompt_file: str) -> str | None:
    """Load a prompt file, returning None if not found."""
    try:
        from app.voice.prompts import load_prompt

        return load_prompt(prompt_file)
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_file}")
        return None


def _finalize_call(call_sid: str, summary: str | None):
    """Update call log with summary and mark as completed."""
    from sqlmodel import select

    with Session(get_engine()) as session:
        call_log = session.exec(
            select(CallLog).where(CallLog.twilio_call_sid == call_sid)
        ).first()
        if call_log:
            call_log.status = "completed"
            call_log.ended_at = datetime.utcnow()
            if call_log.started_at:
                delta = call_log.ended_at - call_log.started_at
                call_log.duration_seconds = int(delta.total_seconds())
            if summary:
                call_log.conversation_summary = summary
                # Try to extract caller name and inquiry from summary
                _extract_lead_info(call_log, summary)
            session.add(call_log)
            session.commit()
            logger.info(f"Call {call_sid} finalized: {call_log.status}")


def _extract_lead_info(call_log: CallLog, summary: str):
    """Simple extraction of caller name and inquiry from summary text."""
    # This is a basic extraction — Gemini's summary generation prompt
    # will structure the output to make this easier
    lines = summary.lower().split("\n")
    for line in lines:
        if "name:" in line and not call_log.caller_name:
            call_log.caller_name = line.split("name:", 1)[1].strip().title()
        elif "inquiry:" in line and not call_log.caller_inquiry:
            call_log.caller_inquiry = line.split("inquiry:", 1)[1].strip()


@router.post("/status")
async def call_status(request: Request):
    """Handle Twilio call status callback."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")
    call_duration = form_data.get("CallDuration")

    logger.info(f"Call status update: {call_sid} -> {call_status}")

    from sqlmodel import select

    with Session(get_engine()) as session:
        call_log = session.exec(
            select(CallLog).where(CallLog.twilio_call_sid == call_sid)
        ).first()

        if call_log:
            call_log.status = call_status
            if call_duration:
                call_log.duration_seconds = int(call_duration)
            if call_status in ("completed", "failed", "busy", "no-answer"):
                call_log.ended_at = datetime.utcnow()
            session.add(call_log)
            session.commit()

    return Response(content="", status_code=200)
