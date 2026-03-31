"""Animated spinner and step progress indicator."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class Spinner(QWidget):
    """Rotating arc spinner."""

    def __init__(self, size: int = 24, color: str = "#0B28D3", parent=None):
        super().__init__(parent)
        self._size = size
        self._color = QColor(color)
        self._angle = 0
        self.setFixedSize(size, size)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start(self):
        self._timer.start(16)  # ~60fps
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        if not self._timer.isActive():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        m = 4
        p.drawArc(m, m, self._size - 2 * m, self._size - 2 * m,
                   self._angle * 16, 270 * 16)
        p.end()


class StepIndicator(QWidget):
    """Horizontal step indicator: ① 載入 → ② OCR → ③ 翻譯 → ④ 匯出"""

    STEPS = ["載入", "OCR 辨識", "翻譯", "匯出"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self._current = -1  # no step active

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addStretch()

        self._step_labels: list[QLabel] = []
        self._arrow_labels: list[QLabel] = []

        for i, name in enumerate(self.STEPS):
            label = QLabel(f" {i + 1}. {name} ")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(self._inactive_style())
            self._step_labels.append(label)
            h.addWidget(label)

            if i < len(self.STEPS) - 1:
                arrow = QLabel("  \u203A  ")  # ›
                arrow.setStyleSheet("color: #DDDDE5; font-size: 14px; background: transparent;")
                self._arrow_labels.append(arrow)
                h.addWidget(arrow)

        h.addStretch()

    def set_step(self, index: int):
        """Set active step (0-3). -1 = none."""
        self._current = index
        for i, label in enumerate(self._step_labels):
            if i < index:
                label.setStyleSheet(self._done_style())
            elif i == index:
                label.setStyleSheet(self._active_style())
            else:
                label.setStyleSheet(self._inactive_style())
        for i, arrow in enumerate(self._arrow_labels):
            if i < index:
                arrow.setStyleSheet("color: #0B28D3; font-size: 14px; background: transparent;")
            else:
                arrow.setStyleSheet("color: #DDDDE5; font-size: 14px; background: transparent;")

    def reset(self):
        self.set_step(-1)

    @staticmethod
    def _inactive_style() -> str:
        return (
            "color: palette(mid); font-size: 12px; font-weight: 400; "
            "background: transparent; border: none; padding: 4px 6px;"
        )

    @staticmethod
    def _active_style() -> str:
        return (
            "color: #0B28D3; font-size: 12px; font-weight: 600; "
            "background-color: #E8ECFB; border: none; border-radius: 10px; "
            "padding: 4px 10px;"
        )

    @staticmethod
    def _done_style() -> str:
        return (
            "color: #006F0C; font-size: 12px; font-weight: 500; "
            "background: transparent; border: none; padding: 4px 6px;"
        )


class ProcessingOverlay(QWidget):
    """Semi-transparent overlay with spinner and message, shown during long ops."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 200);")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        self._spinner = Spinner(32)
        layout.addWidget(self._spinner, 0, Qt.AlignmentFlag.AlignCenter)

        self._msg = QLabel("")
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg.setStyleSheet("color: #1F1F1F; font-size: 14px; font-weight: 500;")
        layout.addWidget(self._msg)

        self._detail = QLabel("")
        self._detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail.setStyleSheet("color: #8181A5; font-size: 12px;")
        layout.addWidget(self._detail)

    def show_processing(self, msg: str, detail: str = ""):
        self._msg.setText(msg)
        self._detail.setText(detail)
        self._spinner.start()
        self.show()
        self.raise_()

    def hide_processing(self):
        self._spinner.stop()
        self.hide()

    def update_detail(self, detail: str):
        self._detail.setText(detail)
