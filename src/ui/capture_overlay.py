"""Transparent fullscreen overlay for screen region selection."""

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class CaptureOverlay(QWidget):
    """Fullscreen overlay for rectangle selection.

    Strategy: take a screenshot, show it as background with dark overlay,
    let user draw a bright rectangle. This is how ShareX/Snipping Tool work.
    """

    region_selected = Signal(QRect)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self._background: QPixmap | None = None
        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._selecting = False

    def start_capture(self):
        """Take background screenshot and show overlay."""
        from src.services.screen_capture import ScreenCaptureService
        svc = ScreenCaptureService()
        geo = svc.get_monitor_geometry()
        png_bytes = svc.capture_full_screen()

        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes)
        self._background = pixmap

        self._origin = None
        self._current = None
        self._selecting = False

        # Position overlay to cover the monitor
        self.setGeometry(geo["left"], geo["top"], geo["width"], geo["height"])
        self.showFullScreen()
        self.activateWindow()
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw the background screenshot
        if self._background:
            painter.drawPixmap(0, 0, self._background)

        # Dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # If selecting, draw the clear region and border
        if self._origin and self._current:
            selection = QRect(self._origin, self._current).normalized()

            # Restore original brightness in selection area
            painter.setClipRect(selection)
            if self._background:
                painter.drawPixmap(0, 0, self._background)
            painter.setClipping(False)

            # Selection border
            pen = QPen(QColor(249, 115, 22), 2)
            painter.setPen(pen)
            painter.drawRect(selection)

            # Size label
            label = f"{selection.width()} x {selection.height()}"
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(selection.x() + 4, selection.y() - 6, label)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            self._current = event.pos()
            selection = QRect(self._origin, self._current).normalized()
            self.hide()
            if selection.width() > 10 and selection.height() > 10:
                # Adjust coordinates to screen position
                geo_left = self.geometry().x()
                geo_top = self.geometry().y()
                adjusted = QRect(
                    selection.x() + geo_left,
                    selection.y() + geo_top,
                    selection.width(),
                    selection.height(),
                )
                self.region_selected.emit(adjusted)
            else:
                self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
