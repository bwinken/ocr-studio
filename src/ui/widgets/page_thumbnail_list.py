"""Vertical page thumbnail strip."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from src.models import PageData


class PageThumbnailList(QWidget):
    page_selected = Signal(int)  # page index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(180)
        self.setMinimumWidth(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("頁面")
        header.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setIconSize(QSize(140, 180))
        self._list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._list)

    def set_pages(self, pages: list[PageData]):
        self._list.clear()
        for page in pages:
            pixmap = QPixmap(str(page.image_path))
            scaled = pixmap.scaledToWidth(140, Qt.TransformationMode.SmoothTransformation)

            item = QListWidgetItem()
            item.setIcon(QIcon(scaled))
            status = ""
            if page.has_text_layer:
                status = " [文字]"
            elif page.ocr_text:
                status = " [已辨識]"
            item.setText(f"第 {page.index + 1} 頁{status}")
            item.setData(Qt.ItemDataRole.UserRole, page.index)
            self._list.addItem(item)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def update_page_status(self, index: int, has_ocr: bool, has_translation: bool):
        if index < self._list.count():
            item = self._list.item(index)
            status = ""
            if has_ocr:
                status = " [已辨識]"
            if has_translation:
                status = " [已翻譯]"
            item.setText(f"第 {index + 1} 頁{status}")

    def _on_row_changed(self, row: int):
        if row >= 0:
            item = self._list.item(row)
            idx = item.data(Qt.ItemDataRole.UserRole)
            self.page_selected.emit(idx)
