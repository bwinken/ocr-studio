"""Floating popup showing OCR result after screen capture."""

from PySide6.QtCore import Qt, Signal
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


class CaptureResultWidget(QWidget):
    translate_requested = Signal(str, str)  # (text, target_language)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )
        self.setWindowTitle("截圖辨識結果")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Image preview
        self._image_label = QLabel()
        self._image_label.setFixedHeight(150)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("background-color: #F0F0F5; border-radius: 8px;")
        layout.addWidget(self._image_label)

        # OCR text
        ocr_label = QLabel("辨識文字：")
        ocr_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(ocr_label)

        self._ocr_text = QTextEdit()
        self._ocr_text.setReadOnly(True)
        layout.addWidget(self._ocr_text, 1)

        # Translated text
        trans_label = QLabel("翻譯結果：")
        trans_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(trans_label)

        self._translated_text = QTextEdit()
        self._translated_text.setReadOnly(True)
        layout.addWidget(self._translated_text, 1)

        # Buttons
        btn_row = QHBoxLayout()

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(TARGET_LANGUAGES)
        default_lang = str(config.get("general/target_language", "English"))
        idx = self._lang_combo.findText(default_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        btn_row.addWidget(self._lang_combo)

        self._translate_btn = QPushButton("翻譯")
        self._translate_btn.clicked.connect(self._on_translate)
        btn_row.addWidget(self._translate_btn)

        copy_ocr_btn = QPushButton("複製原文")
        copy_ocr_btn.setProperty("secondary", True)
        copy_ocr_btn.clicked.connect(self._copy_ocr)
        btn_row.addWidget(copy_ocr_btn)

        copy_trans_btn = QPushButton("複製翻譯")
        copy_trans_btn.setProperty("secondary", True)
        copy_trans_btn.clicked.connect(self._copy_translation)
        btn_row.addWidget(copy_trans_btn)

        close_btn = QPushButton("關閉")
        close_btn.setProperty("secondary", True)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

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
        self.show()
        self.raise_()
        self.activateWindow()

    def set_translation(self, translated_text: str):
        self._translated_text.setPlainText(translated_text)
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("翻譯")

    def set_translation_error(self, error: str):
        self._translated_text.setPlainText(f"Error: {error}")
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("翻譯")

    def _on_translate(self):
        text = self._ocr_text.toPlainText().strip()
        if not text:
            return
        lang = self._lang_combo.currentText()
        self._translate_btn.setEnabled(False)
        self._translate_btn.setText("翻譯中...")
        self.translate_requested.emit(text, lang)

    def _copy_ocr(self):
        text = self._ocr_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _copy_translation(self):
        text = self._translated_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
