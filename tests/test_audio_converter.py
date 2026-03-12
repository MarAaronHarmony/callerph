"""Tests for audio format conversion."""

import base64
import struct

from app.voice.audio import (
    gemini_to_twilio,
    mulaw_to_pcm,
    pcm_to_mulaw,
    resample,
    twilio_to_gemini,
)


def _generate_pcm_silence(num_samples: int = 160, sample_rate: int = 8000) -> bytes:
    """Generate silent PCM audio (all zeros)."""
    return b"\x00\x00" * num_samples


def _generate_pcm_tone(
    frequency: float = 440.0, duration: float = 0.01, sample_rate: int = 8000
) -> bytes:
    """Generate a simple sine wave tone as PCM audio."""
    import math

    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        value = int(16000 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
        samples.append(struct.pack("<h", value))
    return b"".join(samples)


def test_mulaw_to_pcm_and_back():
    """Test mulaw -> PCM -> mulaw round trip."""
    original_pcm = _generate_pcm_tone(sample_rate=8000)
    mulaw = pcm_to_mulaw(original_pcm)
    recovered_pcm = mulaw_to_pcm(mulaw)

    # Mulaw is lossy, so we check length matches
    assert len(recovered_pcm) == len(original_pcm)


def test_pcm_to_mulaw_reduces_size():
    """Mulaw is 8-bit vs PCM 16-bit, so data should be halved."""
    pcm = _generate_pcm_silence(160)
    mulaw = pcm_to_mulaw(pcm)
    assert len(mulaw) == len(pcm) // 2


def test_resample_8000_to_16000():
    pcm_8000 = _generate_pcm_silence(80, 8000)  # 80 samples at 8kHz = 10ms
    pcm_16000 = resample(pcm_8000, 8000, 16000)
    # 16kHz should have roughly double the samples
    assert len(pcm_16000) >= len(pcm_8000)


def test_resample_24000_to_8000():
    pcm_24000 = _generate_pcm_silence(240, 24000)
    pcm_8000 = resample(pcm_24000, 24000, 8000)
    assert len(pcm_8000) < len(pcm_24000)


def test_resample_same_rate():
    pcm = _generate_pcm_silence(100)
    result = resample(pcm, 8000, 8000)
    assert result == pcm


def test_twilio_to_gemini():
    """Test full Twilio -> Gemini conversion pipeline."""
    pcm_8000 = _generate_pcm_tone(sample_rate=8000)
    mulaw = pcm_to_mulaw(pcm_8000)
    b64_payload = base64.b64encode(mulaw).decode("ascii")

    result = twilio_to_gemini(b64_payload)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_gemini_to_twilio():
    """Test full Gemini -> Twilio conversion pipeline."""
    pcm_24000 = _generate_pcm_tone(sample_rate=24000, duration=0.01)

    result = gemini_to_twilio(pcm_24000, sample_rate=24000)
    assert isinstance(result, str)
    # Should be valid base64
    decoded = base64.b64decode(result)
    assert len(decoded) > 0


def test_empty_audio_handling():
    """Test that empty audio doesn't crash."""
    result = twilio_to_gemini(base64.b64encode(b"").decode())
    assert result == b""
