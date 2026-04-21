"""
ui/styles.py
────────────
All PyQt5 stylesheets and colour constants for the HonneyAI dark theme.
"""

# ── Colour palette ────────────────────────────────────────────────────────────
BG_DEEP       = "#080818"   # darkest background
BG_CARD       = "#0f0f28"   # panel / card background
BG_ELEVATED   = "#14143a"   # slightly lighter surface
ACCENT_CYAN   = "#00d4ff"   # primary interactive colour
ACCENT_PURPLE = "#7b2fff"   # secondary accent
ACCENT_PINK   = "#ff2d78"   # warning / error accent
TEXT_BRIGHT   = "#e8e8ff"   # primary text
TEXT_DIM      = "#6e7090"   # secondary / placeholder text
SUCCESS       = "#00ff99"   # positive feedback
WARNING       = "#ffaa00"   # caution
BORDER        = "#1e1e4a"   # subtle border

# ── Main stylesheet ───────────────────────────────────────────────────────────
MAIN_STYLE = f"""
/* ── Base ──────────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {BG_DEEP};
    color: {TEXT_BRIGHT};
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
}}

/* ── Labels ─────────────────────────────────────────────────────────────────── */
QLabel {{
    color: {TEXT_BRIGHT};
    background: transparent;
}}

/* ── Scrollable list (command history) ──────────────────────────────────────── */
QListWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 6px;
    color: {TEXT_BRIGHT};
    outline: 0;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-radius: 6px;
    margin: 2px 0;
}}
QListWidget::item:hover {{
    background-color: {BG_ELEVATED};
}}
QListWidget::item:selected {{
    background-color: rgba(0, 212, 255, 0.15);
    color: {ACCENT_CYAN};
}}

/* ── Text areas ─────────────────────────────────────────────────────────────── */
QTextEdit, QPlainTextEdit {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 10px;
    color: {TEXT_BRIGHT};
    selection-background-color: rgba(0, 212, 255, 0.3);
    font-size: 13px;
    line-height: 1.5;
}}

/* ── Scroll bars ────────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BG_DEEP};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_CYAN};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ── Push buttons ────────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {BG_ELEVATED};
    color: {ACCENT_CYAN};
    border: 1px solid {ACCENT_CYAN};
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background-color: rgba(0, 212, 255, 0.15);
}}
QPushButton:pressed {{
    background-color: rgba(0, 212, 255, 0.30);
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
    border-color: {BORDER};
}}

/* ── Line input ─────────────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT_BRIGHT};
    selection-background-color: rgba(0, 212, 255, 0.3);
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {ACCENT_CYAN};
}}
QLineEdit::placeholder {{
    color: {TEXT_DIM};
}}

/* ── Separator ───────────────────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
}}

/* ── Tooltip ─────────────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {BG_ELEVATED};
    color: {TEXT_BRIGHT};
    border: 1px solid {ACCENT_CYAN};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""

# ── Status colour mapping ─────────────────────────────────────────────────────
STATUS_COLORS = {
    "STANDBY":    TEXT_DIM,
    "LISTENING":  ACCENT_CYAN,
    "PROCESSING": WARNING,
    "EXECUTING":  ACCENT_PURPLE,
    "SPEAKING":   SUCCESS,
    "ERROR":      ACCENT_PINK,
}
