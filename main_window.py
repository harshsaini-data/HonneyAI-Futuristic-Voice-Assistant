"""
from __future__ import annotations

ui/main_window.py
─────────────────
HonneyAI — main application window.

Layout (dark futuristic dashboard):

  ┌─────────────────────────────────────────────────────┐
  │  [●] HONNEY AI          ───   STANDBY   [■][□][✕]  │  ← top bar
  ├──────────────────┬──────────────────────────────────┤
  │                  │                                  │
  │  COMMAND HISTORY │     (mic button + waveform)      │
  │                  │     [last AI response text]      │
  │   scrollable     │                                  │
  │   list           ├──────────────────────────────────┤
  │                  │  [__type a command___] [SEND ▶]  │
  └──────────────────┴──────────────────────────────────┘

Threading model:
  • ListenThread   — runs STT in background so UI never freezes
  • SpeakThread    — runs TTS in background
  • ProcessThread  — runs command processing in background
"""

import sys
import threading

from PyQt5.QtCore import (
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPalette,
)
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.styles import (
    ACCENT_CYAN,
    ACCENT_PURPLE,
    BG_CARD,
    BG_DEEP,
    BG_ELEVATED,
    BORDER,
    MAIN_STYLE,
    TEXT_DIM,
)
from ui.widgets import MicButton, StatusBadge, WaveformWidget, make_history_item
from utils.config import ASSISTANT_NAME, MAX_HISTORY, WINDOW_H, WINDOW_TITLE, WINDOW_W
from utils.logger import log


# ─────────────────────────────────────────────────────────────────────────────
# Background worker threads
# ─────────────────────────────────────────────────────────────────────────────

class ListenThread(QThread):
    """Runs STT in background. Emits `result` with the recognised text or None."""
    result = pyqtSignal(object)   # str | None

    def run(self):
        from voice.stt import listen
        data = listen()
        self.result.emit(data.get("text"))


class SpeakThread(QThread):
    """Runs TTS in background so the UI stays responsive."""
    finished = pyqtSignal()

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text

    def run(self):
        from voice.tts import speak
        speak(self._text)
        self.finished.emit()


class ProcessThread(QThread):
    """Runs command processing in background. Emits (reply, keep_running)."""
    result = pyqtSignal(str, bool)

    def __init__(self, query: str, parent=None):
        super().__init__(parent)
        self._query = query

    def run(self):
        from core.assistant import process_query
        reply, keep_running = process_query(self._query)
        self.result.emit(reply, keep_running)


# ─────────────────────────────────────────────────────────────────────────────
# Rename Dialog (inline, not a popup)
# ─────────────────────────────────────────────────────────────────────────────

class RenameThread(QThread):
    """Listen for the new name after a rename command."""
    result = pyqtSignal(object)

    def run(self):
        from voice.stt import listen
        data = listen(phrase_limit=5)
        self.result.emit(data.get("text"))


# ─────────────────────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    # Internal signals so worker threads can update the UI safely
    _update_status  = pyqtSignal(str)
    _append_history = pyqtSignal(str, str)      # (text, role)
    _update_reply   = pyqtSignal(str)
    _set_mic_anim   = pyqtSignal(bool)
    _set_wave_anim  = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._assistant_name = ASSISTANT_NAME
        self._listening      = False
        self._busy           = False     # True while processing / speaking
        self._listen_thread: ListenThread | None  = None
        self._speak_thread:  SpeakThread | None   = None
        self._process_thread: ProcessThread | None = None

        self._build_ui()
        self._connect_signals()
        self._greet()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_W, WINDOW_H)
        self.setMinimumSize(800, 550)
        self.setStyleSheet(MAIN_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {BORDER}; }}")
        splitter.addWidget(self._build_history_panel())
        splitter.addWidget(self._build_main_panel())
        splitter.setSizes([300, 760])

        root.addWidget(splitter, 1)

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BG_CARD},
                    stop:0.5 #0a0a22,
                    stop:1 {BG_CARD}
                );
                border-bottom: 1px solid {BORDER};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)

        # Dot indicator
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {TEXT_DIM}; font-size: 14px;")
        lay.addWidget(self._status_dot)

        # Title
        title = QLabel(f"  {self._assistant_name.upper()}  AI")
        font = QFont("Segoe UI", 15, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 3)
        title.setFont(font)
        title.setStyleSheet(f"""
            color: transparent;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {ACCENT_CYAN}, stop:1 {ACCENT_PURPLE}
            );
            -webkit-background-clip: text;
        """)
        # Qt doesn't support CSS text-clip; use a simpler gradient label
        title.setStyleSheet(f"color: {ACCENT_CYAN}; letter-spacing: 3px;")
        lay.addWidget(title)

        lay.addStretch(1)

        self._status_badge = StatusBadge()
        lay.addWidget(self._status_badge)

        lay.addSpacing(16)

        # Settings / about button
        btn_about = QPushButton("⚙")
        btn_about.setFixedSize(34, 34)
        btn_about.setToolTip("Settings")
        btn_about.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER};
                border-radius: 17px;
                color: {TEXT_DIM};
                font-size: 15px;
            }}
            QPushButton:hover {{ border-color: {ACCENT_CYAN}; color: {ACCENT_CYAN}; }}
        """)
        btn_about.clicked.connect(self._show_about)
        lay.addWidget(btn_about)

        return bar

    def _build_history_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {BG_CARD};")
        panel.setMinimumWidth(220)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 14, 12, 12)

        header = QLabel("COMMAND HISTORY")
        header.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 10px;
            letter-spacing: 2px;
            font-weight: bold;
        """)
        lay.addWidget(header)
        lay.addSpacing(6)

        self._history_list = QListWidget()
        self._history_list.setWordWrap(True)
        self._history_list.setSpacing(2)
        lay.addWidget(self._history_list, 1)

        btn_clear = QPushButton("Clear History")
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 5px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {ACCENT_CYAN}; border-color: {ACCENT_CYAN}; }}
        """)
        btn_clear.clicked.connect(self._clear_ui_history)
        lay.addWidget(btn_clear)

        return panel

    def _build_main_panel(self) -> QWidget:
        panel = QWidget()
        lay   = QVBoxLayout(panel)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(12)

        # ── Mic button + status ────────────────────────────────────────────────
        mic_row = QHBoxLayout()
        mic_row.addStretch(1)

        mic_col = QVBoxLayout()
        mic_col.setAlignment(Qt.AlignCenter)

        self._mic_btn = MicButton()
        self._mic_btn.clicked.connect(self._on_mic_clicked)
        mic_col.addWidget(self._mic_btn, 0, Qt.AlignCenter)

        mic_col.addSpacing(8)

        self._mic_label = QLabel("TAP TO SPEAK")
        self._mic_label.setAlignment(Qt.AlignCenter)
        self._mic_label.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 10px;
            letter-spacing: 2px;
        """)
        mic_col.addWidget(self._mic_label)

        mic_row.addLayout(mic_col)
        mic_row.addStretch(1)
        lay.addLayout(mic_row)

        # ── Waveform ──────────────────────────────────────────────────────────
        self._waveform = WaveformWidget()
        lay.addWidget(self._waveform)

        # ── Response text area ────────────────────────────────────────────────
        resp_label = QLabel("LAST RESPONSE")
        resp_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; letter-spacing: 2px;")
        lay.addWidget(resp_label)

        self._response_box = QTextEdit()
        self._response_box.setReadOnly(True)
        self._response_box.setMinimumHeight(120)
        self._response_box.setPlaceholderText(
            f"Waiting for a command, {self._assistant_name} is ready…"
        )
        lay.addWidget(self._response_box, 1)

        # ── Text input row ────────────────────────────────────────────────────
        input_row = QHBoxLayout()
        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Type a command or question…")
        self._text_input.returnPressed.connect(self._on_send_text)
        input_row.addWidget(self._text_input, 1)

        self._send_btn = QPushButton("SEND  ▶")
        self._send_btn.setFixedWidth(100)
        self._send_btn.clicked.connect(self._on_send_text)
        input_row.addWidget(self._send_btn)

        lay.addLayout(input_row)

        # Keyboard shortcut hint
        hint = QLabel("  Space = mic  ·  Enter = send  ·  Esc = cancel")
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px;")
        lay.addWidget(hint)

        return panel

    # ── Signal wiring ──────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._update_status.connect(self._on_status_change)
        self._append_history.connect(self._on_append_history)
        self._update_reply.connect(self._on_update_reply)
        self._set_mic_anim.connect(self._mic_btn.set_listening)
        self._set_wave_anim.connect(self._waveform.set_active)

    # ── Startup greeting ───────────────────────────────────────────────────────

    def _greet(self):
        from core.commands import get_greeting
        greeting = get_greeting()
        self._append_history.emit(greeting, "system")
        self._update_reply.emit(greeting)
        # Speak asynchronously
        self._speak(greeting)

    # ── Mic button ─────────────────────────────────────────────────────────────

    def _on_mic_clicked(self):
        if self._busy:
            return
        if self._listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        self._listening = True
        self._busy      = True
        self._set_status("LISTENING")
        self._set_mic_anim.emit(True)
        self._mic_label.setText("LISTENING…")
        self._set_wave_anim.emit(True)

        self._listen_thread = ListenThread(self)
        self._listen_thread.result.connect(self._on_listen_result)
        self._listen_thread.start()

    def _stop_listening(self):
        """Cancel active listening (best-effort)."""
        self._listening = False
        self._busy      = False
        self._set_status("STANDBY")
        self._set_mic_anim.emit(False)
        self._set_wave_anim.emit(False)
        self._mic_label.setText("TAP TO SPEAK")

    def _on_listen_result(self, text):
        """Called on the main thread when STT finishes."""
        self._listening = False
        self._set_mic_anim.emit(False)
        self._set_wave_anim.emit(False)
        self._mic_label.setText("TAP TO SPEAK")

        if text:
            self._append_history.emit(text, "user")
            self._run_command(text)
        else:
            self._set_status("STANDBY")
            self._busy = False
            self._update_reply.emit("I didn't catch that — please try again.")

    # ── Text input ─────────────────────────────────────────────────────────────

    def _on_send_text(self):
        text = self._text_input.text().strip()
        if not text or self._busy:
            return
        self._text_input.clear()
        self._append_history.emit(text, "user")
        self._run_command(text)

    # ── Command processing ────────────────────────────────────────────────────

    def _run_command(self, query: str):
        self._busy = True
        self._set_status("PROCESSING")

        self._process_thread = ProcessThread(query, self)
        self._process_thread.result.connect(self._on_process_result)
        self._process_thread.start()

    def _on_process_result(self, reply: str, keep_running: bool):
        # Handle rename sentinel
        if reply == "__RENAME__":
            self._do_rename_flow()
            return

        self._set_status("EXECUTING")
        self._append_history.emit(reply, "assistant")
        self._update_reply.emit(reply)
        self._speak(reply)

        if not keep_running:
            QTimer.singleShot(3000, self.close)

    # ── Rename flow ────────────────────────────────────────────────────────────

    def _do_rename_flow(self):
        prompt = "What would you like to call me?"
        self._update_reply.emit(prompt)
        self._speak(prompt)
        # After speaking, listen for the new name
        QTimer.singleShot(2500, self._listen_for_new_name)

    def _listen_for_new_name(self):
        self._set_status("LISTENING")
        self._set_mic_anim.emit(True)
        rename_thread = RenameThread(self)
        rename_thread.result.connect(self._apply_new_name)
        rename_thread.start()

    def _apply_new_name(self, text):
        self._set_mic_anim.emit(False)
        if text:
            name = text.strip().title()
            from core.assistant import set_runtime_name
            set_runtime_name(name)
            self._assistant_name = name
            reply = f"Alright! I'll be called {name} from now on."
        else:
            reply = "I didn't catch a name. Keeping my current name."
        self._update_reply.emit(reply)
        self._append_history.emit(reply, "assistant")
        self._speak(reply)

    # ── Speaking ──────────────────────────────────────────────────────────────

    def _speak(self, text: str):
        self._busy = True   # Block mic clicks while speaking
        self._set_status("SPEAKING")
        self._set_wave_anim.emit(True)
        self._speak_thread = SpeakThread(text, self)
        self._speak_thread.finished.connect(self._on_speak_done)
        self._speak_thread.start()

    def _on_speak_done(self):
        self._set_wave_anim.emit(False)
        self._set_status("STANDBY")
        self._busy = False

    # ── UI helpers ─────────────────────────────────────────────────────────────

    def _set_status(self, status: str):
        self._update_status.emit(status)

    def _on_status_change(self, status: str):
        self._status_badge.set_status(status)
        colors = {
            "STANDBY":    TEXT_DIM,
            "LISTENING":  ACCENT_CYAN,
            "PROCESSING": "#ffaa00",
            "EXECUTING":  ACCENT_PURPLE,
            "SPEAKING":   "#00ff99",
            "ERROR":      "#ff2d78",
        }
        self._status_dot.setStyleSheet(
            f"color: {colors.get(status, TEXT_DIM)}; font-size: 14px;"
        )

    def _on_append_history(self, text: str, role: str):
        item = make_history_item(
            text[:120] + ("…" if len(text) > 120 else ""),
            role,
        )
        self._history_list.addItem(item)
        # Keep history bounded
        while self._history_list.count() > MAX_HISTORY:
            self._history_list.takeItem(0)
        self._history_list.scrollToBottom()

    def _on_update_reply(self, text: str):
        self._response_box.setPlainText(text)

    def _clear_ui_history(self):
        self._history_list.clear()

    # ── About ─────────────────────────────────────────────────────────────────

    def _show_about(self):
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("About HonneyAI")
        msg.setText(
            f"<b style='color:{ACCENT_CYAN}'>{self._assistant_name} AI</b><br><br>"
            "A modern voice assistant.<br>"
            "Built with PyQt5, SpeechRecognition, Perplexity AI.<br><br>"
            "<small>Press <b>Space</b> to toggle microphone.<br>"
            "Type in the bottom bar and press <b>Enter</b> to send.</small>"
        )
        msg.setStyleSheet(MAIN_STYLE + f"QMessageBox {{ background: {BG_CARD}; }}")
        msg.exec_()

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space and not self._text_input.hasFocus():
            self._on_mic_clicked()
        elif key == Qt.Key_Escape:
            if self._listening:
                self._stop_listening()
        else:
            super().keyPressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# Entry-point helper
# ─────────────────────────────────────────────────────────────────────────────

def launch_app() -> int:
    """Create the QApplication and show the main window. Returns exit code."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setStyle("Fusion")

    # Set dark palette so native widgets also look dark
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BG_DEEP))
    palette.setColor(QPalette.WindowText, QColor("#e0e0ff"))
    palette.setColor(QPalette.Base, QColor(BG_CARD))
    palette.setColor(QPalette.Text, QColor("#e0e0ff"))
    palette.setColor(QPalette.Button, QColor(BG_ELEVATED))
    palette.setColor(QPalette.ButtonText, QColor(ACCENT_CYAN))
    palette.setColor(QPalette.Highlight, QColor(ACCENT_CYAN))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    return app.exec_()
