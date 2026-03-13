"""Gemini 2.5 Flash Live API voice agent with robust VAD and auto-reconnect."""

import asyncio
import logging
import time
from typing import Callable, Optional

from google import genai
from google.genai import types
from sqlmodel import Session

from app.config import settings
from app.db.database import get_engine
from app.models.call_log import CallLog
from app.voice.vad import VoiceActivityDetector, rms_energy

logger = logging.getLogger(__name__)

# Audio buffering — accumulate small chunks before sending to Gemini
_BUFFER_DURATION_MS = 100  # send audio in 100ms batches
_BUFFER_SIZE_BYTES = int(16000 * 2 * _BUFFER_DURATION_MS / 1000)  # 3200 bytes at 16kHz 16-bit

# Auto-reconnect settings
_MAX_RECONNECT_ATTEMPTS = 3
_RECONNECT_DELAY_S = 1.0

# Tool declaration for real-time lead capture
_SAVE_LEAD_TOOL = {
    "function_declarations": [
        {
            "name": "save_lead",
            "description": (
                "Save caller's lead information to the database. "
                "Call this function as soon as the caller provides their name, "
                "contact number, or describes their inquiry. "
                "You can call this multiple times as you gather more details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "caller_name": {
                        "type": "string",
                        "description": "The caller's full name",
                    },
                    "contact_number": {
                        "type": "string",
                        "description": "The caller's phone number or email for follow-up",
                    },
                    "inquiry": {
                        "type": "string",
                        "description": "What the caller is asking about or interested in",
                    },
                },
                "required": [],
            },
        }
    ]
}


class GeminiVoiceAgent:
    """Manages a real-time voice conversation with Gemini Live API."""

    def __init__(
        self,
        system_prompt: str,
        call_sid: str,
        on_audio_response: Optional[Callable] = None,
    ):
        self.system_prompt = system_prompt
        self.call_sid = call_sid
        self.on_audio_response = on_audio_response
        self.session = None
        self.is_connected = False
        self._client = None
        self._conversation_turns: list[str] = []
        self._receive_task: asyncio.Task | None = None
        self._session_context = None
        self._audio_send_count = 0
        self._audio_recv_count = 0
        self._greeting_done = False
        # VAD
        self._vad = VoiceActivityDetector(sample_rate=16000)
        # Audio buffer
        self._audio_buffer = bytearray()
        # Reconnect state
        self._reconnect_count = 0
        # Echo suppression — suppress VAD while Gemini is outputting audio
        self._gemini_is_speaking = False
        self._gemini_last_audio_time: float = 0

    def _build_config(self) -> types.LiveConnectConfig:
        """Build the Gemini Live API connection config."""
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=self.system_prompt)]
            ),
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=True
                )
            ),
            tools=[_SAVE_LEAD_TOOL],
        )

    async def connect(self):
        """Establish connection to Gemini Live API."""
        try:
            self._client = genai.Client(api_key=settings.gemini_api_key)
            config = self._build_config()

            self._session_context = self._client.aio.live.connect(
                model="gemini-2.5-flash-native-audio-latest",
                config=config,
            )
            self.session = await self._session_context.__aenter__()
            self.is_connected = True

            # Start receiving responses in background
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Send initial prompt to trigger greeting
            await self.session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part(text="A caller has just connected. Greet them now.")]
                ),
                turn_complete=True,
            )

            logger.info("Gemini Live API connected, greeting triggered")

        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}", exc_info=True)
            self.is_connected = False
            raise

    async def _reconnect(self) -> bool:
        """Attempt to reconnect to Gemini after a connection drop.

        Returns True if reconnection succeeded.
        """
        if self._reconnect_count >= _MAX_RECONNECT_ATTEMPTS:
            logger.error(
                f"Max reconnect attempts ({_MAX_RECONNECT_ATTEMPTS}) reached, giving up"
            )
            return False

        self._reconnect_count += 1
        logger.warning(
            f"Attempting reconnect {self._reconnect_count}/{_MAX_RECONNECT_ATTEMPTS}..."
        )

        # Clean up old session
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_context = None
            self.session = None

        await asyncio.sleep(_RECONNECT_DELAY_S)

        try:
            config = self._build_config()
            self._session_context = self._client.aio.live.connect(
                model="gemini-2.5-flash-native-audio-latest",
                config=config,
            )
            self.session = await self._session_context.__aenter__()

            # Re-send context so Gemini knows the conversation state
            if self._conversation_turns:
                context = "Conversation so far:\n" + "\n".join(self._conversation_turns[-5:])
                await self.session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part(text=context + "\nPlease continue the conversation.")]
                    ),
                    turn_complete=True,
                )
            else:
                await self.session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part(text="Continue the conversation.")]
                    ),
                    turn_complete=True,
                )

            self._greeting_done = True  # skip greeting on reconnect
            self._vad.reset()
            logger.info(f"Reconnected successfully (attempt {self._reconnect_count})")
            return True

        except Exception as e:
            logger.error(f"Reconnect attempt {self._reconnect_count} failed: {e}")
            return False

    async def send_audio(self, pcm_audio: bytes):
        """Send audio chunk to Gemini with voice activity detection and buffering.

        Args:
            pcm_audio: PCM audio bytes at 16000 Hz, 16-bit mono.
        """
        if not self.is_connected or not self.session:
            return

        if not self._greeting_done:
            return

        # Echo suppression: skip VAD while Gemini is speaking or during
        # the cooldown window after it stops (lets echo decay in Twilio path)
        _ECHO_COOLDOWN_S = 0.3
        if self._gemini_is_speaking:
            return
        if (
            self._gemini_last_audio_time > 0
            and time.monotonic() - self._gemini_last_audio_time < _ECHO_COOLDOWN_S
        ):
            return

        # VAD processing
        event = self._vad.process_frame(pcm_audio)

        # Log VAD state periodically for diagnostics
        self._vad_frame_count = getattr(self, "_vad_frame_count", 0) + 1
        if self._vad_frame_count % 100 == 1:
            rms = rms_energy(pcm_audio)
            logger.info(
                f"VAD #{self._vad_frame_count}: event={event}, "
                f"RMS={rms:.0f}, speaking={self._vad.is_speaking}"
            )

        try:
            if event == "speech_start":
                # Flush any buffered audio and signal activity start
                self._audio_buffer.clear()
                await self.session.send_realtime_input(
                    activity_start=types.ActivityStart()
                )
                # Send the current chunk immediately
                self._audio_buffer.extend(pcm_audio)
                await self._flush_buffer()
                logger.info("VAD: Speech started")

            elif event == "speech_continue":
                # Buffer audio and send when buffer is full
                self._audio_buffer.extend(pcm_audio)
                if len(self._audio_buffer) >= _BUFFER_SIZE_BYTES:
                    await self._flush_buffer()

            elif event == "speech_end":
                # Flush remaining audio and signal activity end
                if self._audio_buffer:
                    await self._flush_buffer()
                await self.session.send_realtime_input(
                    activity_end=types.ActivityEnd()
                )
                logger.info(
                    f"VAD: Speech ended (sent {self._audio_send_count} chunks total)"
                )

            # "silence" — do nothing

        except Exception as e:
            logger.error(f"Error sending audio to Gemini: {e}", exc_info=True)
            # Connection may have dropped — attempt reconnect
            if "ConnectionClosed" in type(e).__name__ or "closed" in str(e).lower():
                await self._handle_connection_drop()

    async def _flush_buffer(self):
        """Send buffered audio to Gemini and clear the buffer."""
        if not self._audio_buffer:
            return

        data = bytes(self._audio_buffer)
        self._audio_buffer.clear()

        await self.session.send_realtime_input(
            media=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
        )
        self._audio_send_count += 1

        if self._audio_send_count % 100 == 1:
            logger.info(f"Audio chunk #{self._audio_send_count} sent to Gemini")

    async def _handle_connection_drop(self):
        """Handle a dropped Gemini connection by attempting to reconnect."""
        logger.warning("Gemini connection dropped, attempting reconnect...")

        # Cancel existing receive loop
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        success = await self._reconnect()
        if success:
            # Restart receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())
        else:
            self.is_connected = False

    async def _receive_loop(self):
        """Continuously receive audio responses from Gemini.

        Wraps session.receive() in a while loop because the async generator
        may exit after each turn_complete, requiring a fresh call.
        """
        if not self.session:
            return

        try:
            while self.is_connected:
                logger.info("Starting receive iteration...")
                try:
                    async for response in self.session.receive():
                        if not self.is_connected:
                            break

                        # Handle tool calls (real-time lead capture)
                        tool_call = getattr(response, "tool_call", None)
                        if tool_call:
                            await self._handle_tool_call(tool_call)
                            continue

                        server_content = getattr(response, "server_content", None)
                        if not server_content:
                            continue

                        model_turn = getattr(server_content, "model_turn", None)
                        turn_complete = getattr(server_content, "turn_complete", False)
                        interrupted = getattr(server_content, "interrupted", False)

                        if model_turn and model_turn.parts:
                            for part in model_turn.parts:
                                inline_data = getattr(part, "inline_data", None)
                                if inline_data and inline_data.data:
                                    self._audio_recv_count += 1
                                    # Echo suppression: mark Gemini as speaking
                                    self._gemini_is_speaking = True
                                    self._gemini_last_audio_time = time.monotonic()
                                    if self._audio_recv_count % 100 == 1:
                                        logger.info(
                                            f"Gemini audio chunk #{self._audio_recv_count}"
                                        )
                                    if self.on_audio_response:
                                        await self.on_audio_response(inline_data.data)

                                text = getattr(part, "text", None)
                                if text:
                                    self._conversation_turns.append(f"Agent: {text}")

                        if turn_complete:
                            # Echo suppression: Gemini finished speaking
                            self._gemini_is_speaking = False
                            self._gemini_last_audio_time = time.monotonic()
                            if not self._greeting_done:
                                self._greeting_done = True
                                logger.info(
                                    f"Greeting complete "
                                    f"({self._audio_recv_count} audio chunks). "
                                    f"Now accepting caller audio."
                                )
                            else:
                                logger.info(
                                    f"Turn complete "
                                    f"(recv {self._audio_recv_count} chunks)"
                                )

                        if interrupted:
                            self._gemini_is_speaking = False
                            logger.info("Gemini response interrupted by caller")

                except Exception as inner_e:
                    err_str = str(inner_e).lower()
                    if "closed" in err_str or "keepalive" in err_str:
                        logger.warning(f"Gemini connection lost in receive: {inner_e}")
                        if self.is_connected:
                            success = await self._reconnect()
                            if success:
                                continue  # restart the while loop with new session
                            else:
                                break
                    else:
                        raise

                logger.info("session.receive() iterator ended, restarting...")

        except asyncio.CancelledError:
            logger.info("Gemini receive loop cancelled")
        except Exception as e:
            logger.error(f"Error in Gemini receive loop: {e}", exc_info=True)

    async def _handle_tool_call(self, tool_call):
        """Handle function calls from Gemini (e.g., save_lead)."""
        for fc in tool_call.function_calls:
            if fc.name == "save_lead":
                args = fc.args or {}
                logger.info(f"Gemini called save_lead: {args}")
                self._save_lead_to_db(
                    caller_name=args.get("caller_name"),
                    contact_number=args.get("contact_number"),
                    inquiry=args.get("inquiry"),
                )
                # Send tool response back to Gemini so it continues
                await self.session.send_tool_response(
                    function_responses=types.FunctionResponse(
                        name="save_lead",
                        response={"status": "saved"},
                        id=fc.id,
                    )
                )
            else:
                logger.warning(f"Unknown tool call: {fc.name}")

    def _save_lead_to_db(
        self,
        caller_name: str | None = None,
        contact_number: str | None = None,
        inquiry: str | None = None,
    ):
        """Save lead info to the CallLog record for this call."""
        from sqlmodel import select

        try:
            with Session(get_engine()) as session:
                call_log = session.exec(
                    select(CallLog).where(CallLog.twilio_call_sid == self.call_sid)
                ).first()
                if not call_log:
                    logger.warning(f"No call log found for SID: {self.call_sid}")
                    return

                if caller_name:
                    call_log.caller_name = caller_name
                if contact_number:
                    call_log.caller_inquiry = (
                        f"{call_log.caller_inquiry or ''}\n"
                        f"Contact: {contact_number}"
                    ).strip()
                if inquiry:
                    existing = call_log.caller_inquiry or ""
                    if inquiry not in existing:
                        call_log.caller_inquiry = (
                            f"{existing}\n{inquiry}" if existing else inquiry
                        ).strip()

                session.add(call_log)
                session.commit()
                logger.info(
                    f"Lead saved for call {self.call_sid}: "
                    f"name={caller_name}, contact={contact_number}, inquiry={inquiry}"
                )
        except Exception as e:
            logger.error(f"Error saving lead to DB: {e}", exc_info=True)

    async def generate_summary(self) -> str | None:
        """Generate a conversation summary using Gemini text API."""
        if not self._client:
            return None

        if not self._conversation_turns:
            return "No conversation recorded."

        conversation_text = "\n".join(self._conversation_turns)
        summary_prompt = f"""Summarize this phone conversation in a structured format:

{conversation_text}

Provide the summary in this exact format:
Name: [caller's name if mentioned, otherwise "Unknown"]
Inquiry: [what they were asking about in one sentence]
Summary: [2-3 sentence summary of the conversation]
Interested In: [which package or service they showed interest in, if any]
Follow Up: [yes/no — should the business owner call them back?]"""

        try:
            response = await self._client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=summary_prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return (
                f"Summary generation failed. "
                f"Conversation had {len(self._conversation_turns)} turns."
            )

    async def disconnect(self):
        """Close the Gemini Live API connection."""
        self.is_connected = False

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing Gemini session: {e}")
            self._session_context = None
            self.session = None

        logger.info(
            f"Gemini agent disconnected "
            f"(sent: {self._audio_send_count}, recv: {self._audio_recv_count})"
        )
