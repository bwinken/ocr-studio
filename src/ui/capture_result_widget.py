"""Floating popup for capture OCR results — frameless, theme-consistent."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.constants import TARGET_LANGUAGES
from src.ui.widgets.spinner import Spinner


class CaptureResultWidget(QWidget):
    translate_requested = Signal(str, str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setMinimumSize(520, 460)
        self.resize(580, 520)
        self._drag_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Custom title bar ──
        header = QWidget()
        header.setObjectName("titleBar")
        header.setFixedHeight(36)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 4, 0)
        hl.setSpacing(0)

        title_label = QLabel("截圖辨識結果")
        title_label.setObjectName("appName")
        title_label.setStyleSheet("font-size: 13px;")
        hl.addWidget(title_label)
        hl.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setObjectName("winClose")
        close_btn.setFixedSize(36, 36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        hl.addWidget(close_btn)

        layout.addWidget(header)

        # ── Body ──
        body = QVBoxLayout()
        body.setContentsMargins(20, 12, 20, 16)
        body.setSpacing(10)

        # Image preview
        self._image_label = QLabel()
        self._image_label.setFixedHeight(130)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setObjectName("surfaceAlt")
        body.addWidget(self._image_label)

        # Processing row
        self._processing_row = QWidget()
        pr = QHBoxLayout(self._processing_row)
        pr.setContentsMargins(0, 0, 0, 0)
        pr.setSpacing(8)
        pr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner = Spinner(20)
        pr.addWidget(self._spinner)
        self._processing_label = QLabel("辨識中，請稍候...")
        self._processing_label.setObjectName("textSecondary")
        self._processing_label.setStyleSheet("font-size: 13px;")
        pr.addWidget(self._processing_label)
        body.addWidget(self._processing_row)

        # OCR
        ocr_header = QHBoxLayout()
        ocr_label = QLabel("\U0001F50D 辨識文字")
        ocr_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        ocr_header.addWidget(ocr_label)
        ocr_header.addStretch()
        self._copy_ocr_btn = QPushButton("\U0001F4CB 複製原文")
        self._copy_ocr_btn.setProperty("secondary", True)
        self._copy_ocr_btn.setToolTip("複製辨識結果到剪貼簿")
        self._copy_ocr_btn.clicked.connect(self._copy_ocr)
        ocr_header.addWidget(self._copy_ocr_btn)
        body.addLayout(ocr_header)

        self._ocr_text = QTextEdit()
        self._ocr_text.setReadOnly(True)
        self._ocr_text.setPlaceholderText("辨識結果將顯示在此...")
        self._ocr_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body.addWidget(self._ocr_text, 1)

        # Translation section (hideable)
        self._trans_section = QWidget()
        ts_layout = QVBoxLayout(self._trans_section)
        ts_layout.setContentsMargins(0, 0, 0, 0)
        ts_layout.setSpacing(6)

        trans_header = QHBoxLayout()
        trans_label = QLabel("\U0001F310 翻譯結果")
        trans_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        trans_header.addWidget(trans_label)
        trans_header.addStretch()
        self._copy_trans_btn = QPushButton("\U0001F4CB 複製翻譯")
        self._copy_trans_btn.setProperty("secondary", True)
        self._copy_trans_btn.setToolTip("複製翻譯結果到剪貼簿")
        self._copy_trans_btn.clicked.connect(self._copy_translation)
        trans_header.addWidget(self._copy_trans_btn)
        ts_layout.addLayout(trans_header)

        self._translated_text = QTextEdit()
        self._translated_text.setReadOnly(True)
        self._translated_text.setPlaceholderText("翻譯中...")
        self._translated_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ts_layout.addWidget(self._translated_text, 1)

        body.addWidget(self._trans_section, 1)

        # Action bar (also hideable with translate)
        self._trans_actions = QWidget()
        actions = QHBoxLayout(self._trans_actions)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)

        self._lang_combo = QComboBox()
        self._lang_combo.setToolTip("翻譯目標語言")
        self._lang_combo.addItems(TARGET_LANGUAGES)
        default_lang = str(config.get("general/target_language", "English"))
        idx = self._lang_combo.findText(default_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        actions.addWidget(self._lang_combo)

        self._translate_btn = QPushButton("\U0001F310 翻譯")
        self._translate_btn.setToolTip("將辨識文字翻譯成目標語言")
        self._translate_btn.clicked.connect(self._on_translate)
        actions.addWidget(self._translate_btn)

        actions.addStretch()

        close_btn2 = QPushButton("關閉")
        close_btn2.setProperty("secondary", True)
        close_btn2.clicked.connect(self.close)
        actions.addWidget(close_btn2)

        body.addWidget(self._trans_actions)

        body.addLayout(actions)
        layout.addLayout(body, 1)

    # ── Draggable title bar ──

    def mousePressEvent(self, event):
        if event.position().y() < 36:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ── Public API ──

    def _set_translate_visible(self, visible: bool):
        self._trans_section.setVisible(visible)
        self._trans_actions.setVisible(visible)
        # Resize window based on mode
        if visible:
            self.resize(580, 520)
        else:
            self.resize(580, 360)

    def show_processing(self, image_bytes: bytes, show_translate: bool = False):
        self._set_translate_visible(show_translate)
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        scaled = pixmap.scaledToHeight(
            self._image_label.height(),
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._ocr_text.clear()
        self._translated_text.clear()
        self._processing_row.show()
        self._spinner.start()
        self._processing_label.setText("辨識中，請稍候...")
        self._translate_btn.setEnabled(False)
        self.show()
        self.raise_()
        self.activateWindow()

    def set_capture(self, image_bytes: bytes, ocr_text: str):
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        scaled = pixmap.scaledToHeight(
            self._image_label.height(),
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._ocr_text.setPlainText(ocr_text)
        self._translated_text.clear()
        self._processing_row.hide()
        self._spinner.stop()
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("\U0001F310 翻譯")
        self.show()
        self.raise_()
        self.activateWindow()

    def set_translation(self, translated_text: str):
        self._translated_text.setPlainText(translated_text)
        self._processing_row.hide()
        self._spinner.stop()
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("\U0001F310 翻譯")

    def set_translation_error(self, error: str):
        self._translated_text.setPlainText(f"翻譯失敗：{error}")
        self._processing_row.hide()
        self._spinner.stop()
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("\U0001F310 翻譯")

    def _on_translate(self):
        text = self._ocr_text.toPlainText().strip()
        if not text:
            return
        lang = self._lang_combo.currentText()
        self._translate_btn.setEnabled(False)
        self._translate_btn.setText("翻譯中...")
        self._processing_row.show()
        self._spinner.start()
        self._processing_label.setText("翻譯中...")
        self.translate_requested.emit(text, lang)

    def _copy_ocr(self):
        text = self._ocr_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self._flash_btn(self._copy_ocr_btn, "\u2705 已複製", "\U0001F4CB 複製原文")

    def _copy_translation(self):
        text = self._translated_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self._flash_btn(self._copy_trans_btn, "\u2705 已複製", "\U0001F4CB 複製翻譯")

    @staticmethod
    def _flash_btn(btn: QPushButton, flash_text: str, original_text: str):
        btn.setText(flash_text)
        QTimer.singleShot(1200, lambda: btn.setText(original_text))
