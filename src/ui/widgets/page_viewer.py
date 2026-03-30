"""Zoomable page image viewer with bounding box overlay."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from src.models import TextBlock


class PageViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._canvas = _Canvas()
        self._scroll.setWidget(self._canvas)
        layout.addWidget(self._scroll)

        self._zoom = 0.0  # 0 means auto-fit

    def set_image(self, image_path: str, width: int, height: int):
        self._canvas.set_image(image_path, width, height)
        self._zoom = 0.0  # reset to auto-fit
        self._apply_zoom()

    def set_bboxes(self, blocks: list[TextBlock]):
        self._canvas.set_bboxes(blocks)

    def clear(self):
        self._canvas.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._zoom == 0.0:
            self._apply_zoom()

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            # Switch from auto-fit to manual zoom
            if self._zoom == 0.0:
                self._zoom = self._auto_fit_scale()
            if delta > 0:
                self._zoom = min(self._zoom * 1.15, 5.0)
            else:
                self._zoom = max(self._zoom / 1.15, 0.1)
            self._apply_zoom()
            event.accept()
        else:
            super().wheelEvent(event)

    def _auto_fit_scale(self) -> float:
        """Calculate zoom to fit image in viewport width."""
        if not self._canvas._pixmap or self._canvas._orig_width == 0:
            return 1.0
        viewport_w = self._scroll.viewport().width() - 20  # small margin
        return max(0.1, viewport_w / self._canvas._orig_width)

    def _apply_zoom(self):
        if self._zoom == 0.0:
            scale = self._auto_fit_scale()
        else:
            scale = self._zoom
        self._canvas.set_zoom(scale)


class _Canvas(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pixmap: QPixmap | None = None
        self._blocks: list[TextBlock] = []
        self._zoom = 1.0
        self._orig_width = 0
        self._orig_height = 0

    def set_image(self, image_path: str, width: int, height: int):
        self._pixmap = QPixmap(image_path)
        self._orig_width = width
        self._orig_height = height
        self._blocks = []
        self._update_display()

    def set_bboxes(self, blocks: list[TextBlock]):
        self._blocks = blocks
        self._update_display()

    def set_zoom(self, zoom: float):
        self._zoom = zoom
        self._update_display()

    def clear(self):
        self._pixmap = None
        self._blocks = []
        self.setPixmap(QPixmap())

    def _update_display(self):
        if not self._pixmap:
            return

        w = int(self._orig_width * self._zoom)
        h = int(self._orig_height * self._zoom)
        if w < 1 or h < 1:
            return

        scaled = self._pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)

        if self._blocks:
            painter = QPainter(scaled)
            pen = QPen(QColor(249, 115, 22, 180), 2)
            painter.setPen(pen)

            for block in self._blocks:
                bbox = block.bbox
                x0 = int(bbox.x0 * self._zoom)
                y0 = int(bbox.y0 * self._zoom)
                x1 = int(bbox.x1 * self._zoom)
                y1 = int(bbox.y1 * self._zoom)
                painter.drawRect(x0, y0, x1 - x0, y1 - y0)
                painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(249, 115, 22, 25))

            painter.end()

        self.setPixmap(scaled)
        self.setFixedSize(scaled.size())
