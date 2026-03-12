"""Voice Activity Detection — WebRTC VAD with pure-Python fallback.

Uses webrtcvad (C library, highly accurate) when available.
Falls back to energy + zero-crossing rate analysis when not installed.
"""

import logging
import struct
import time

logger = logging.getLogger(__name__)

# Try to import webrtcvad; fall back to pure-Python VAD
try:
    import webrtcvad

    _HAS_WEBRTCVAD = True
    logger.info("Using WebRTC VAD (high accuracy)")
except ImportError:
    _HAS_WEBRTCVAD = False
    logger.info("WebRTC VAD not available, using energy-based fallback")


# --- Configuration ---
# How many consecutive speech/silence frames to require before state change
SPEECH_START_FRAMES = 2  # ~40ms of speech to start (fast detection)
SPEECH_END_FRAMES = 12  # ~240ms of silence to end (at 20ms per frame)
SILENCE_TIMEOUT = 0.4  # seconds of confirmed silence before activity_end


class VoiceActivityDetector:
    """Detects speech in PCM audio using WebRTC VAD or energy fallback."""

    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 1):
        """Initialize VAD.

        Args:
            sample_rate: Audio sample rate (8000, 16000, 32000, or 48000).
            aggressiveness: WebRTC VAD aggressiveness (0-3).
                0 = least aggressive (fewer false negatives, more false positives)
                3 = most aggressive (more false negatives, fewer false positives)
                1 = good for telephone audio (mulaw-converted, lower quality)
        """
        self.sample_rate = sample_rate
        self.is_speaking = False
        self._speech_frame_count = 0
        self._silence_frame_count = 0
        self._silence_start: float | None = None

        if _HAS_WEBRTCVAD:
            self._vad = webrtcvad.Vad(aggressiveness)
        else:
            self._vad = None
            # Fallback thresholds — lower for telephone-quality audio
            self._energy_threshold = 250
            self._zcr_speech_max = 0.5  # wider range for mulaw-converted audio

    def process_frame(self, pcm_audio: bytes) -> str:
        """Process an audio frame and return the VAD event.

        Args:
            pcm_audio: PCM 16-bit mono audio bytes.

        Returns:
            One of:
            - "speech_start": Speech just started (transition from silence)
            - "speech_continue": Speech is ongoing
            - "silence": No speech detected
            - "speech_end": Speech just ended (enough silence after speech)
        """
        is_speech = self._detect_speech(pcm_audio)

        if not self.is_speaking:
            if is_speech:
                self._speech_frame_count += 1
                self._silence_frame_count = 0
                if self._speech_frame_count >= SPEECH_START_FRAMES:
                    self.is_speaking = True
                    self._speech_frame_count = 0
                    self._silence_start = None
                    return "speech_start"
            else:
                self._speech_frame_count = 0
            return "silence"
        else:
            # Currently speaking
            if is_speech:
                self._silence_frame_count = 0
                self._silence_start = None
                return "speech_continue"
            else:
                self._silence_frame_count += 1
                now = time.monotonic()
                if self._silence_start is None:
                    self._silence_start = now

                if (self._silence_frame_count >= SPEECH_END_FRAMES
                        and now - self._silence_start >= SILENCE_TIMEOUT):
                    self.is_speaking = False
                    self._silence_frame_count = 0
                    self._silence_start = None
                    return "speech_end"
                return "speech_continue"  # still in speech mode, brief pause

    def _detect_speech(self, pcm_audio: bytes) -> bool:
        """Detect if audio frame contains speech."""
        if self._vad is not None:
            return self._detect_webrtc(pcm_audio)
        return self._detect_energy(pcm_audio)

    def _detect_webrtc(self, pcm_audio: bytes) -> bool:
        """Use WebRTC VAD for speech detection."""
        # WebRTC VAD needs exactly 10, 20, or 30ms frames
        # At 16kHz, 20ms = 320 samples = 640 bytes
        frame_size = int(self.sample_rate * 0.02) * 2  # 20ms frame in bytes

        if len(pcm_audio) < frame_size:
            return False

        # Check multiple 20ms frames, return True if any has speech
        speech_frames = 0
        total_frames = 0
        for i in range(0, len(pcm_audio) - frame_size + 1, frame_size):
            frame = pcm_audio[i:i + frame_size]
            try:
                if self._vad.is_speech(frame, self.sample_rate):
                    speech_frames += 1
            except Exception:
                continue
            total_frames += 1

        if total_frames == 0:
            return False
        # Speech if ANY frame has speech (lenient for telephone audio)
        return speech_frames > 0

    def _detect_energy(self, pcm_audio: bytes) -> bool:
        """Fallback: energy + zero-crossing rate analysis."""
        if len(pcm_audio) < 4:
            return False

        n_samples = len(pcm_audio) // 2
        samples = struct.unpack(f"<{n_samples}h", pcm_audio[:n_samples * 2])

        # RMS energy
        sum_sq = sum(s * s for s in samples)
        rms = (sum_sq / n_samples) ** 0.5

        if rms < self._energy_threshold:
            return False

        # Zero-crossing rate — speech has a characteristic ZCR
        # Pure tones (beeps) have very low ZCR, noise has very high ZCR
        crossings = 0
        for i in range(1, n_samples):
            if (samples[i] >= 0) != (samples[i - 1] >= 0):
                crossings += 1
        zcr = crossings / n_samples

        # Speech typically has ZCR between 0.02 and 0.3
        return 0.02 < zcr < self._zcr_speech_max

    def reset(self):
        """Reset VAD state."""
        self.is_speaking = False
        self._speech_frame_count = 0
        self._silence_frame_count = 0
        self._silence_start = None
