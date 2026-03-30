"""OCR text + translation display panel."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TextPanel(QWidget):
    translate_requested = Signal()
    text_edited = Signal(str)  # emitted when user manually edits OCR text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # OCR text section
        ocr_header = QHBoxLayout()
        ocr_label = QLabel("辨識文字")
        ocr_label.setStyleSheet("font-weight: bold;")
        ocr_header.addWidget(ocr_label)
        ocr_header.addStretch()

        copy_ocr = QPushButton("複製")
        copy_ocr.setProperty("secondary", True)
        copy_ocr.setFixedWidth(60)
        copy_ocr.clicked.connect(self._copy_ocr)
        ocr_header.addWidget(copy_ocr)
        layout.addLayout(ocr_header)

        self._ocr_text = QTextEdit()
        self._ocr_text.setPlaceholderText("辨識結果將顯示在此...")
        layout.addWidget(self._ocr_text, 1)

        # Translation section
        trans_header = QHBoxLayout()
        trans_label = QLabel("翻譯結果")
        trans_label.setStyleSheet("font-weight: bold;")
        trans_header.addWidget(trans_label)
        trans_header.addStretch()

        copy_trans = QPushButton("複製")
        copy_trans.setProperty("secondary", True)
        copy_trans.setFixedWidth(60)
        copy_trans.clicked.connect(self._copy_translation)
        trans_header.addWidget(copy_trans)
        layout.addLayout(trans_header)

        self._translated_text = QTextEdit()
        self._translated_text.setPlaceholderText("翻譯結果將顯示在此...")
        self._translated_text.setReadOnly(True)
        layout.addWidget(self._translated_text, 1)

    def set_ocr_text(self, text: str):
        self._ocr_text.setPlainText(text)

    def set_translated_text(self, text: str):
        self._translated_text.setPlainText(text)

    def get_ocr_text(self) -> str:
        return self._ocr_text.toPlainText()

    def get_translated_text(self) -> str:
        return self._translated_text.toPlainText()

    def clear(self):
        self._ocr_text.clear()
        self._translated_text.clear()

    def _copy_ocr(self):
        text = self._ocr_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _copy_translation(self):
        text = self._translated_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
