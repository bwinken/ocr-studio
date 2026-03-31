"""OCR text + translation display panel."""

from PySide6.QtCore import QTimer, Signal
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
    text_edited = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # OCR text section
        ocr_header = QHBoxLayout()
        ocr_label = QLabel("辨識文字")
        ocr_label.setStyleSheet("font-weight: 600;")
        ocr_header.addWidget(ocr_label)
        ocr_header.addStretch()

        self._copy_ocr_btn = QPushButton("\U0001F4CB 複製")
        self._copy_ocr_btn.setProperty("secondary", True)
        self._copy_ocr_btn.setToolTip("複製辨識結果到剪貼簿")
        self._copy_ocr_btn.clicked.connect(self._copy_ocr)
        ocr_header.addWidget(self._copy_ocr_btn)
        layout.addLayout(ocr_header)

        self._ocr_text = QTextEdit()
        self._ocr_text.setPlaceholderText("辨識結果將顯示在此...")
        layout.addWidget(self._ocr_text, 1)

        # Translation section
        trans_header = QHBoxLayout()
        trans_label = QLabel("翻譯結果")
        trans_label.setStyleSheet("font-weight: 600;")
        trans_header.addWidget(trans_label)
        trans_header.addStretch()

        self._copy_trans_btn = QPushButton("\U0001F4CB 複製")
        self._copy_trans_btn.setProperty("secondary", True)
        self._copy_trans_btn.setToolTip("複製翻譯結果到剪貼簿")
        self._copy_trans_btn.clicked.connect(self._copy_translation)
        trans_header.addWidget(self._copy_trans_btn)
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
            self._flash(self._copy_ocr_btn)

    def _copy_translation(self):
        text = self._translated_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self._flash(self._copy_trans_btn)

    @staticmethod
    def _flash(btn: QPushButton):
        original = btn.text()
        btn.setText("\u2705 已複製")
        QTimer.singleShot(1200, lambda: btn.setText(original))
