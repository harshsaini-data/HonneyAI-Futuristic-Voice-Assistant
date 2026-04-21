"""
from __future__ import annotations

voice/stt.py
────────────
Speech-to-text (STT) using Google Web Speech API via SpeechRecognition.

Key improvements over original:
  • Ambient noise calibration on first call (or when requested)
  • Configurable timeout / phrase limit
  • Structured return: dict with 'text', 'confidence', 'error'
  • Wake-word detection helper
"""

import speech_recognition as sr
from utils.logger import log
from utils.config import (
    SR_PAUSE_THRESHOLD,
    SR_ENERGY_THRESHOLD,
    SR_PHRASE_TIME_LIMIT,
    SR_LANGUAGE,
    WAKE_WORD,
)

# ── Shared recogniser ─────────────────────────────────────────────────────────
_recogniser = sr.Recognizer()
_recogniser.pause_threshold       = SR_PAUSE_THRESHOLD
_recogniser.energy_threshold      = SR_ENERGY_THRESHOLD
_recogniser.dynamic_energy_threshold = True

_calibrated = False   # calibrate once on startup


def calibrate_microphone(duration: float = 1.5) -> None:
    """
    Calibrate the recogniser for ambient background noise.
    Should be called once before the main loop starts.
    """
    global _calibrated
    try:
        with sr.Microphone() as source:
            log.info("Calibrating microphone for ambient noise…")
            _recogniser.adjust_for_ambient_noise(source, duration=duration)
        _calibrated = True
        log.info(f"Mic calibrated (energy_threshold={_recogniser.energy_threshold:.0f})")
    except Exception as exc:
        log.warning(f"Mic calibration failed: {exc}")


def listen(timeout: float | None = None, phrase_limit: float = SR_PHRASE_TIME_LIMIT) -> dict:
    """
    Listen for a single voice command.

    Returns a dict::

        {
            "text":       str | None,   # transcribed text (lowercase)
            "raw":        str | None,   # original casing from Google
            "error":      str | None,   # human-readable error message
            "timed_out":  bool,
        }
    """
    result = {"text": None, "raw": None, "error": None, "timed_out": False}

    if not _calibrated:
        calibrate_microphone()

    try:
        with sr.Microphone() as source:
            log.debug("Listening…")
            audio = _recogniser.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit,
            )
    except sr.WaitTimeoutError:
        result["timed_out"] = True
        result["error"] = "Timed out waiting for speech."
        log.debug("Listen timed out.")
        return result
    except Exception as exc:
        result["error"] = f"Microphone error: {exc}"
        log.error(result["error"])
        return result

    # ── Transcribe ────────────────────────────────────────────────────────────
    try:
        raw = _recogniser.recognize_google(audio, language=SR_LANGUAGE)
        result["raw"]  = raw
        result["text"] = raw.lower().strip()
        log.info(f"Heard: {result['text']!r}")

    except sr.UnknownValueError:
        result["error"] = "Could not understand audio."
        log.debug("Audio not understood.")

    except sr.RequestError as exc:
        result["error"] = f"Google STT service error: {exc}"
        log.error(result["error"])

    return result


def contains_wake_word(text: str) -> bool:
    """Return True if *text* contains the configured wake word."""
    return WAKE_WORD in text.lower()


def strip_wake_word(text: str) -> str:
    """Remove the wake word prefix from *text*, if present."""
    return text.lower().replace(WAKE_WORD, "").strip()
