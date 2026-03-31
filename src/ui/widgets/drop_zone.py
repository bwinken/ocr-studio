"""Large drag-and-drop upload zone — theme-aware via objectName."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.constants import SUPPORTED_EXTENSIONS


class DropZone(QWidget):
    files_dropped = Signal(list)  # list[Path]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        self._inner = QWidget()
        self._inner.setObjectName("dropInner")
        inner_layout = QVBoxLayout(self._inner)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.setSpacing(10)

        icon = QLabel("\U0001F4C4")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setObjectName("textDimmed")
        icon.setStyleSheet("font-size: 56px; background: transparent; border: none;")
        inner_layout.addWidget(icon)

        inner_layout.addSpacing(4)

        title = QLabel("將檔案拖放到此處")
        title.setObjectName("textPrimary")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600; background: transparent; border: none;")
        inner_layout.addWidget(title)

        sub = QLabel("或使用上方的「開啟檔案」按鈕")
        sub.setObjectName("textSecondary")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        inner_layout.addWidget(sub)

        inner_layout.addSpacing(8)

        badges = QLabel("PDF  \u00B7  PNG  \u00B7  JPG  \u00B7  BMP  \u00B7  TIFF  \u00B7  WebP")
        badges.setObjectName("textDimmed")
        badges.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badges.setStyleSheet("font-size: 11px; background: transparent; border: none; letter-spacing: 1px;")
        inner_layout.addWidget(badges)

        layout.addWidget(self._inner, 1)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._inner.setObjectName("dropInnerHover")
            self._inner.setStyleSheet("")  # force re-apply
            self._inner.style().unpolish(self._inner)
            self._inner.style().polish(self._inner)

    def dragLeaveEvent(self, event):
        self._inner.setObjectName("dropInner")
        self._inner.setStyleSheet("")
        self._inner.style().unpolish(self._inner)
        self._inner.style().polish(self._inner)

    def dropEvent(self, event):
        self._inner.setObjectName("dropInner")
        self._inner.setStyleSheet("")
        self._inner.style().unpolish(self._inner)
        self._inner.style().polish(self._inner)
        paths = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                paths.append(path)
        if paths:
            self.files_dropped.emit(paths)
