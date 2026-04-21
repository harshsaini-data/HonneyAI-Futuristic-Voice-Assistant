"""
ui/widgets.py
─────────────
Custom PyQt5 widgets used by the main window:

  • MicButton       — animated circular mic button with ripple rings
  • WaveformWidget  — animated sine-wave bar that plays while speaking
  • StatusBadge     — colour-coded pill label showing the current state
  • HistoryItem     — styled list-widget item (user vs assistant)
"""

import math

from PyQt5.QtCore import (
    QPoint,
    QRectF,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PyQt5.QtWidgets import QLabel, QListWidgetItem, QPushButton, QSizePolicy, QWidget

from ui.styles import (
    ACCENT_CYAN,
    ACCENT_PINK,
    ACCENT_PURPLE,
    BG_CARD,
    STATUS_COLORS,
    SUCCESS,
    TEXT_DIM,
    WARNING,
)


# ─────────────────────────────────────────────────────────────────────────────
# MicButton — pulsing circle mic button
# ─────────────────────────────────────────────────────────────────────────────

class MicButton(QWidget):
    """
    Circular button with animated ripple rings.
    Emits `clicked` when pressed.
    Call `set_listening(True/False)` to start/stop animation.
    """

    clicked = pyqtSignal()

    _INNER_RADIUS = 52
    _OUTER_BASE   = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click to start/stop listening")

        self._listening   = False
        self._ring_scales = [1.0, 1.0, 1.0]   # Three ripple rings
        self._glow_alpha  = 0
        self._timer       = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._tick_count  = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def set_listening(self, on: bool) -> None:
        self._listening = on
        if on:
            self._ring_scales = [1.0, 1.0, 1.0]
            self._tick_count  = 0
            self._timer.start(30)          # ~33 fps
        else:
            self._timer.stop()
            self._glow_alpha = 0
            self.update()

    # ── Animation tick ────────────────────────────────────────────────────────

    def _tick(self) -> None:
        self._tick_count += 1
        t = self._tick_count
        # Three rings offset by 20 ticks each
        self._ring_scales = [
            1.0 + 0.45 * (math.sin(t * 0.07) * 0.5 + 0.5),
            1.0 + 0.45 * (math.sin((t - 20) * 0.07) * 0.5 + 0.5),
            1.0 + 0.45 * (math.sin((t - 40) * 0.07) * 0.5 + 0.5),
        ]
        self._glow_alpha = int(60 + 60 * math.sin(t * 0.12))
        self.update()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2

        # ── Ripple rings (only while listening) ───────────────────────────────
        if self._listening:
            ring_color = QColor(ACCENT_CYAN)
            for i, scale in enumerate(self._ring_scales):
                alpha = max(0, 120 - i * 35 - int((scale - 1.0) / 0.45 * 80))
                ring_color.setAlpha(alpha)
                pen = QPen(ring_color, 1.5)
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                r = self._OUTER_BASE * scale
                p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # ── Outer glow circle ─────────────────────────────────────────────────
        glow = QRadialGradient(cx, cy, self._OUTER_BASE)
        a = self._glow_alpha if self._listening else 20
        glow.setColorAt(0, QColor(0, 212, 255, a))
        glow.setColorAt(1, QColor(0, 212, 255, 0))
        p.setBrush(glow)
        p.setPen(Qt.NoPen)
        r = self._OUTER_BASE + 8
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # ── Inner filled circle ────────────────────────────────────────────────
        grad = QRadialGradient(cx, cy - 10, self._INNER_RADIUS)
        if self._listening:
            grad.setColorAt(0, QColor("#1a6080"))
            grad.setColorAt(1, QColor("#003050"))
        else:
            grad.setColorAt(0, QColor("#1a1a3a"))
            grad.setColorAt(1, QColor("#0a0a20"))
        p.setBrush(grad)

        border_col = QColor(ACCENT_CYAN) if self._listening else QColor(ACCENT_PURPLE)
        border_col.setAlpha(200)
        p.setPen(QPen(border_col, 2))
        r = self._INNER_RADIUS
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # ── Mic icon (simple geometric) ────────────────────────────────────────
        icon_color = QColor(ACCENT_CYAN) if self._listening else QColor("#8888cc")
        p.setPen(Qt.NoPen)
        p.setBrush(icon_color)

        # Capsule body
        body_w, body_h = 18, 26
        path = QPainterPath()
        path.addRoundedRect(QRectF(cx - body_w / 2, cy - body_h / 2 - 6,
                                   body_w, body_h), body_w / 2, body_w / 2)
        p.drawPath(path)

        # Stand arc
        pen = QPen(icon_color, 2.5)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        arc_r = 14
        p.drawArc(QRectF(cx - arc_r, cy + 2, arc_r * 2, arc_r * 2),
                  0, 180 * 16)   # lower semi-circle
        # Stand pole
        p.drawLine(QPoint(int(cx), int(cy + 2 + arc_r)),
                   QPoint(int(cx), int(cy + 2 + arc_r + 6)))

        p.end()

    # ── Mouse handling ────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


# ─────────────────────────────────────────────────────────────────────────────
# WaveformWidget — animated bar visualiser
# ─────────────────────────────────────────────────────────────────────────────

class WaveformWidget(QWidget):
    """Animated waveform bar that pulses while speaking/processing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._active    = False
        self._phase     = 0.0
        self._timer     = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._bars      = 28
        self._heights   = [0.0] * self._bars

    def set_active(self, on: bool) -> None:
        self._active = on
        if on:
            self._timer.start(40)
        else:
            self._timer.stop()
            self._heights = [0.0] * self._bars
            self.update()

    def _tick(self) -> None:
        self._phase += 0.18
        for i in range(self._bars):
            offset = i * (2 * math.pi / self._bars)
            val = (math.sin(self._phase + offset) * 0.5 + 0.5)
            # Add a second harmonic for more organic look
            val += 0.25 * (math.sin(self._phase * 1.7 + offset * 1.3) * 0.5 + 0.5)
            val = val / 1.25
            self._heights[i] = val
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        bar_w = max(2, (w - self._bars * 2) // self._bars)
        max_h = h - 4

        for i, frac in enumerate(self._heights):
            bar_h = max(3, int(frac * max_h))
            x = i * (bar_w + 2) + 1
            y = (h - bar_h) // 2

            # Gradient from cyan → purple along width
            t = i / max(1, self._bars - 1)
            r = int(0   + t * 123)
            g = int(212 - t * 173)
            b = int(255 - t * 128)
            color = QColor(r, g, b, 200)
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(x, y, bar_w, bar_h, bar_w / 2, bar_w / 2)

        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# StatusBadge — pill label
# ─────────────────────────────────────────────────────────────────────────────

class StatusBadge(QLabel):
    """Pill-shaped label whose colour changes with the assistant's state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(28)
        self.setMinimumWidth(120)
        font = QFont("Segoe UI", 10, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        self.setFont(font)
        self.set_status("STANDBY")

    def set_status(self, status: str) -> None:
        color = STATUS_COLORS.get(status.upper(), TEXT_DIM)
        self.setText(status.upper())
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                border: 1px solid {color};
                border-radius: 13px;
                padding: 2px 16px;
                background-color: rgba(0,0,0,0.4);
                letter-spacing: 2px;
            }}
        """)


# ─────────────────────────────────────────────────────────────────────────────
# History item helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_history_item(text: str, role: str = "user") -> QListWidgetItem:
    """
    Create a styled QListWidgetItem for the history panel.
    role = "user" | "assistant" | "system"
    """
    if role == "user":
        prefix = "👤 You"
        color  = QColor("#c0d8ff")
    elif role == "assistant":
        prefix = "🤖 Honney"
        color  = QColor(ACCENT_CYAN)
    else:
        prefix = "⚙  System"
        color  = QColor(TEXT_DIM)

    item = QListWidgetItem(f"{prefix}: {text}")
    item.setForeground(color)
    return item
