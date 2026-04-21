"""
voice/tts.py
────────────
Text-to-speech with two backends:
  1. pyttsx3   – fast, fully offline, preferred
  2. PowerShell – fallback if pyttsx3 fails (Windows-only)

Usage:
    from voice.tts import speak
    speak("Hello world")
"""

import subprocess
import threading
from utils.logger import log
from utils.config import TTS_RATE, TTS_VOLUME

# ── Try to initialise pyttsx3 engine once at import time ──────────────────────
_engine = None
_engine_lock = threading.Lock()

def _init_engine():
    global _engine
    try:
        import pyttsx3
        eng = pyttsx3.init()
        voices = eng.getProperty("voices")

        # Prefer a female voice (index 1 if available)
        if len(voices) > 1:
            eng.setProperty("voice", voices[1].id)

        eng.setProperty("rate", TTS_RATE)
        eng.setProperty("volume", TTS_VOLUME)
        _engine = eng
        log.debug("pyttsx3 TTS engine initialised.")
    except Exception as exc:
        log.warning(f"pyttsx3 unavailable ({exc}). PowerShell fallback active.")


_init_engine()


def _speak_pyttsx3(text: str) -> bool:
    """Speak using pyttsx3. Returns True on success."""
    global _engine
    if _engine is None:
        return False
    try:
        with _engine_lock:
            _engine.say(text)
            _engine.runAndWait()
        return True
    except Exception as exc:
        log.warning(f"pyttsx3 speak error: {exc}")
        return False


def _speak_powershell(text: str) -> None:
    """Speak using Windows PowerShell SAPI (fallback)."""
    # Sanitise text to prevent injection
    safe = text.replace('"', "'").replace('`', "'")
    cmd = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f'$s.Speak("{safe}")'
    )
    try:
        subprocess.call(
            ["powershell", "-Command", cmd],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as exc:
        log.error(f"PowerShell TTS failed: {exc}")


def speak(text: str) -> None:
    """
    Convert *text* to speech.
    Tries pyttsx3 first; falls back to PowerShell on Windows.
    Always prints to console as well.
    """
    if not text or not text.strip():
        return

    print(f"🤖 {text}")
    log.info(f"SPEAK » {text}")

    if not _speak_pyttsx3(text):
        _speak_powershell(text)
