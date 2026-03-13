"""Voice Activity Detection — RMS energy with debounce.

Tuned for Twilio telephone audio (mulaw 8kHz upsampled to PCM 16kHz).
WebRTC VAD doesn't work reliably with mulaw-converted audio, so we use
energy-based detection with debounce to filter transient noise (coughs, etc).
"""

import logging
import struct
import time

logger = logging.getLogger(__name__)

# --- Configuration ---
SPEECH_START_RMS = 300       # RMS above this = potential speech
SPEECH_END_RMS = 150         # RMS below this = potential silence
SPEECH_START_FRAMES = 2      # consecutive loud frames to confirm speech start
SILENCE_TIMEOUT = 0.4        # seconds of silence before ending activity


def rms_energy(pcm_audio: bytes) -> float:
    """Calculate RMS energy of 16-bit PCM audio."""
    if len(pcm_audio) < 2:
        return 0.0
    n_samples = len(pcm_audio) // 2
    samples = struct.unpack(f"<{n_samples}h", pcm_audio[:n_samples * 2])
    sum_sq = sum(s * s for s in samples)
    return (sum_sq / n_samples) ** 0.5


class VoiceActivityDetector:
    """Detects speech in PCM audio using RMS energy with debounce."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.is_speaking = False
        self._speech_start_count = 0
        self._silence_start: float | None = None

    def process_frame(self, pcm_audio: bytes) -> str:
        """Process an audio frame and return the VAD event.

        Returns:
            "speech_start", "speech_continue", "silence", or "speech_end"
        """
        rms = rms_energy(pcm_audio)

        if not self.is_speaking:
            if rms > SPEECH_START_RMS:
                self._speech_start_count += 1
                if self._speech_start_count >= SPEECH_START_FRAMES:
                    self.is_speaking = True
                    self._speech_start_count = 0
                    self._silence_start = None
                    return "speech_start"
                return "silence"  # still accumulating
            else:
                self._speech_start_count = 0
                return "silence"
        else:
            # Currently speaking
            if rms < SPEECH_END_RMS:
                now = time.monotonic()
                if self._silence_start is None:
                    self._silence_start = now
                elif now - self._silence_start >= SILENCE_TIMEOUT:
                    self.is_speaking = False
                    self._silence_start = None
                    return "speech_end"
                return "speech_continue"  # brief pause, still in speech
            else:
                self._silence_start = None
                return "speech_continue"

    def reset(self):
        """Reset VAD state."""
        self.is_speaking = False
        self._speech_start_count = 0
        self._silence_start = None
