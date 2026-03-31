import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.constants import UI


class CaptureTab(QWidget):
    """Capture history and results."""

    def __init__(self, config):
        super().__init__()
        self._config = config
        self._captures = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)

        title = QLabel(UI["capture_history"])
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        hotkey = str(config.get_hotkey())
        hint = QLabel(UI["capture_hint"].format(hotkey=hotkey))
        hint.setObjectName("textSecondary")
        toolbar.addWidget(hint)

        layout.addLayout(toolbar)

        # Splitter: history list | detail view
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._list = QListWidget()
        self._list.setMaximumWidth(300)
        self._list.currentRowChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._list)

        # Detail panel
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)

        self._detail_image = QLabel()
        self._detail_image.setFixedHeight(200)
        self._detail_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_image.setObjectName("surfaceAlt")
        detail_layout.addWidget(self._detail_image)

        # Empty state hint
        self._empty_hint = QLabel("\U0001F4F7 使用快捷鍵截取螢幕區域\n辨識結果會顯示在這裡")
        self._empty_hint.setObjectName("textDimmed")
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hint.setStyleSheet("font-size: 13px;")
        detail_layout.addWidget(self._empty_hint)

        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setPlaceholderText(UI["ocr_text"] + "...")
        detail_layout.addWidget(self._detail_text, 1)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton(UI["copy"])
        copy_btn.setProperty("secondary", True)
        copy_btn.clicked.connect(self._copy_text)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        detail_layout.addLayout(btn_row)

        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

    def add_capture_result(self, image_bytes: bytes, ocr_text: str, blocks: list):
        ts = time.time()
        self._captures.insert(0, (ts, image_bytes, ocr_text, blocks))

        label = time.strftime("%H:%M:%S", time.localtime(ts))
        preview = ocr_text[:60].replace("\n", " ") if ocr_text else "(empty)"
        item = QListWidgetItem(f"[{label}] {preview}")
        self._list.insertItem(0, item)
        self._list.setCurrentRow(0)
        self._empty_hint.hide()

    def _on_selection_changed(self, row: int):
        if row < 0 or row >= len(self._captures):
            return
        _, image_bytes, ocr_text, _ = self._captures[row]

        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        scaled = pixmap.scaledToHeight(
            self._detail_image.height(),
            Qt.TransformationMode.SmoothTransformation,
        )
        self._detail_image.setPixmap(scaled)
        self._detail_text.setPlainText(ocr_text)

    def _copy_text(self):
        text = self._detail_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
