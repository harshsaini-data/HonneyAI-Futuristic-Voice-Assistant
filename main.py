"""
main.py
───────
HonneyAI — entry point.

Run with:
    python main.py
"""

import sys
import os

# ── Ensure the project root is on sys.path (works when run from any directory)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import log
from utils.config import ASSISTANT_NAME


def main():
    log.info(f"═══ {ASSISTANT_NAME} AI starting ═══")

    # Calibrate microphone in background before the UI appears
    import threading
    from voice.stt import calibrate_microphone
    threading.Thread(target=calibrate_microphone, daemon=True).start()

    # Launch the PyQt5 application
    from ui.main_window import launch_app
    exit_code = launch_app()

    log.info(f"═══ {ASSISTANT_NAME} AI offline ═══")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
