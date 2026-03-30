"""Drag-and-drop file zone widget."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.constants import SUPPORTED_EXTENSIONS


class DropZone(QWidget):
    files_dropped = Signal(list)  # list[Path]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("拖放 PDF 或圖片檔案到此處\n或點擊「開啟檔案」")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setProperty("subheading", True)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._update_style(False)

    def _update_style(self, hovering: bool):
        border_color = "#0B28D3" if hovering else "#DDDDE5"
        bg = "#E8ECFB" if hovering else "#F5F5FA"
        self.setStyleSheet(
            f"DropZone {{ border: 2px dashed {border_color}; "
            f"border-radius: 12px; background-color: {bg}; }}"
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._update_style(True)

    def dragLeaveEvent(self, event):
        self._update_style(False)

    def dropEvent(self, event):
        self._update_style(False)
        paths = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                paths.append(path)
        if paths:
            self.files_dropped.emit(paths)
