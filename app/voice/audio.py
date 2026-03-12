"""Audio format conversion between Twilio (mulaw/8000) and Gemini (PCM/16000 & PCM/24000)."""

import audioop
import base64


def mulaw_to_pcm(mulaw_data: bytes) -> bytes:
    """Convert mulaw audio to 16-bit PCM."""
    return audioop.ulaw2lin(mulaw_data, 2)


def pcm_to_mulaw(pcm_data: bytes) -> bytes:
    """Convert 16-bit PCM audio to mulaw."""
    return audioop.lin2ulaw(pcm_data, 2)


def resample(audio_data: bytes, from_rate: int, to_rate: int) -> bytes:
    """Resample 16-bit PCM audio from one sample rate to another."""
    if from_rate == to_rate:
        return audio_data
    converted, _ = audioop.ratecv(audio_data, 2, 1, from_rate, to_rate, None)
    return converted


def twilio_to_gemini(base64_payload: str) -> bytes:
    """Convert Twilio media payload (base64 mulaw/8000) to Gemini format (PCM/16000).

    Args:
        base64_payload: Base64-encoded mulaw audio at 8000 Hz from Twilio.

    Returns:
        PCM audio bytes at 16000 Hz, 16-bit mono.
    """
    mulaw_bytes = base64.b64decode(base64_payload)
    pcm_8000 = mulaw_to_pcm(mulaw_bytes)
    pcm_16000 = resample(pcm_8000, 8000, 16000)
    return pcm_16000


def gemini_to_twilio(pcm_data: bytes, sample_rate: int = 24000) -> str:
    """Convert Gemini audio response (PCM/24000) to Twilio format (base64 mulaw/8000).

    Args:
        pcm_data: PCM audio bytes from Gemini.
        sample_rate: Sample rate of Gemini output (default 24000 Hz).

    Returns:
        Base64-encoded mulaw audio string at 8000 Hz for Twilio.
    """
    pcm_8000 = resample(pcm_data, sample_rate, 8000)
    mulaw_bytes = pcm_to_mulaw(pcm_8000)
    return base64.b64encode(mulaw_bytes).decode("ascii")
