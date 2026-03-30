"""Document viewer: load PDF/images, view pages, run OCR, translate, export."""

import tempfile
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.config import ConfigManager
from src.constants import (
    SUPPORTED_EXTENSIONS,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_PDF_EXTENSIONS,
    TARGET_LANGUAGES,
    UI,
)
from src.models import DocumentData, ExportSource, OverlayMode, PageData
from src.services.image_service import ImageService
from src.services.openai_service import OpenAIService
from src.services.pdf_service import PdfService
from src.ui.widgets.drop_zone import DropZone
from src.ui.widgets.page_thumbnail_list import PageThumbnailList
from src.ui.widgets.page_viewer import PageViewer
from src.ui.widgets.text_panel import TextPanel
from src.workers.ocr_worker import OcrWorker
from src.workers.translate_worker import TranslateWorker


class DocumentsTab(QWidget):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self._config = config
        self._document: DocumentData | None = None
        self._current_page_index: int = -1
        self._active_workers: list = []
        self._work_dir: Path | None = None

        self._openai_service: OpenAIService | None = None
        self._pdf_service = PdfService(
            render_scale=float(config.get("general/pdf_render_scale", 2.0))
        )
        self._image_service = ImageService()

        self._build_ui()

    def set_openai_service(self, service: OpenAIService):
        self._openai_service = service

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("docToolbar")
        toolbar1 = QHBoxLayout(toolbar_widget)
        toolbar1.setContentsMargins(14, 8, 14, 8)
        toolbar1.setSpacing(8)

        open_btn = QPushButton(UI["open_file"])
        open_btn.setProperty("secondary", True)
        open_btn.clicked.connect(self._open_file_dialog)
        toolbar1.addWidget(open_btn)

        self._ocr_btn = QPushButton(UI["ocr_all"])
        self._ocr_btn.clicked.connect(self._ocr_all_pages)
        self._ocr_btn.setEnabled(False)
        toolbar1.addWidget(self._ocr_btn)

        self._translate_btn = QPushButton(UI["translate_all"])
        self._translate_btn.clicked.connect(self._translate_all_pages)
        self._translate_btn.setEnabled(False)
        toolbar1.addWidget(self._translate_btn)

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(TARGET_LANGUAGES)
        default_lang = str(self._config.get("general/target_language", "English"))
        idx = self._lang_combo.findText(default_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        toolbar1.addWidget(self._lang_combo)

        toolbar1.addStretch()

        # Status (center)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #8181A5; font-size: 12px;")
        toolbar1.addWidget(self._status_label)

        toolbar1.addStretch()

        # Export controls
        self._overlay_combo = QComboBox()
        self._overlay_combo.addItems([
            UI["overlay_visible"],
            UI["overlay_invisible"],
            UI["overlay_replace"],
        ])
        self._overlay_combo.setEnabled(False)
        toolbar1.addWidget(self._overlay_combo)

        self._export_btn = QPushButton(UI["export_pdf"])
        self._export_btn.setProperty("success", True)
        self._export_btn.clicked.connect(self._export_pdf)
        self._export_btn.setEnabled(False)
        toolbar1.addWidget(self._export_btn)

        layout.addWidget(toolbar_widget)

        # Stacked: drop zone vs document view
        self._stack = QStackedWidget()

        self._drop_zone = DropZone()
        self._drop_zone.files_dropped.connect(self._load_files)
        self._stack.addWidget(self._drop_zone)

        # Document viewer
        viewer_widget = QWidget()
        viewer_layout = QHBoxLayout(viewer_widget)
        viewer_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._thumbnails = PageThumbnailList()
        self._thumbnails.page_selected.connect(self._show_page)
        splitter.addWidget(self._thumbnails)

        self._page_viewer = PageViewer()
        splitter.addWidget(self._page_viewer)

        self._text_panel = TextPanel()
        splitter.addWidget(self._text_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 2)

        viewer_layout.addWidget(splitter)
        self._stack.addWidget(viewer_widget)

        layout.addWidget(self._stack)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                paths.append(p)
        if paths:
            self._load_files(paths)

    def _open_file_dialog(self):
        exts = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTENSIONS))
        path, _ = QFileDialog.getOpenFileName(
            self, UI["open_file"], "", f"支援的檔案 ({exts});;所有檔案 (*)"
        )
        if path:
            self._load_files([Path(path)])

    def _load_files(self, paths: list[Path]):
        if not paths:
            return

        path = paths[0]
        self._status_label.setText(f"{UI['loading']} {path.name}")

        doc_id = uuid.uuid4().hex[:8]
        self._work_dir = Path(tempfile.mkdtemp(prefix="ocrstudio_"))

        pages: list[PageData] = []
        suffix = path.suffix.lower()

        try:
            if suffix in SUPPORTED_PDF_EXTENSIONS:
                pages = self._pdf_service.load_pdf(path, self._work_dir)
            elif suffix in SUPPORTED_IMAGE_EXTENSIONS:
                page = self._pdf_service.load_image(path, self._work_dir, 0)
                pages = [page]
        except Exception as e:
            self._status_label.setText(f"載入失敗：{e}")
            return

        if not pages:
            self._status_label.setText("無法載入檔案")
            return

        self._document = DocumentData(
            doc_id=doc_id,
            filename=path.name,
            source_path=path,
            pages=pages,
        )

        self._thumbnails.set_pages(pages)
        self._stack.setCurrentIndex(1)
        self._ocr_btn.setEnabled(True)
        self._export_btn.setEnabled(True)
        self._overlay_combo.setEnabled(True)

        has_text = any(p.ocr_text for p in pages)
        self._translate_btn.setEnabled(has_text)

        text_count = sum(1 for p in pages if p.has_text_layer)
        self._status_label.setText(
            f"已載入 {path.name}：{len(pages)} 頁"
            + (f"，{text_count} 頁有文字圖層" if text_count else "")
        )

    @Slot(int)
    def _show_page(self, index: int):
        if not self._document or index < 0 or index >= len(self._document.pages):
            return

        self._current_page_index = index
        page = self._document.pages[index]

        self._page_viewer.set_image(str(page.image_path), page.width, page.height)

        if page.text_blocks:
            self._page_viewer.set_bboxes(page.text_blocks)

        self._text_panel.set_ocr_text(page.ocr_text)
        self._text_panel.set_translated_text(page.translated_text)

    def _ocr_all_pages(self):
        if not self._document:
            return
        if not self._openai_service or not self._openai_service.api_key:
            QMessageBox.warning(self, "OCR", UI["no_api_key"])
            return

        self._ocr_btn.setEnabled(False)
        self._status_label.setText(UI["ocr_running"])
        self._ocr_page_chain(0)

    def _ocr_page_chain(self, page_index: int):
        if not self._document or page_index >= len(self._document.pages):
            self._ocr_btn.setEnabled(True)
            self._translate_btn.setEnabled(True)
            self._status_label.setText(UI["ocr_complete"])
            if self._current_page_index >= 0:
                self._show_page(self._current_page_index)
            return

        page = self._document.pages[page_index]

        if page.has_text_layer and page.ocr_text:
            self._ocr_page_chain(page_index + 1)
            return

        total = len(self._document.pages)
        self._status_label.setText(f"OCR 辨識中 {page_index + 1}/{total}...")

        # For PDFs, render at high resolution for better OCR/bbox accuracy
        source = self._document.source_path
        if source.suffix.lower() in SUPPORTED_PDF_EXTENSIONS:
            hires_path = self._pdf_service.render_page_hires(
                source, page_index, self._work_dir)
            image_source = hires_path
            from PIL import Image as PILImage
            with PILImage.open(hires_path) as img:
                ocr_w, ocr_h = img.size
        else:
            image_source = page.image_path
            ocr_w, ocr_h = page.width, page.height

        worker = OcrWorker(
            self._openai_service,
            image_source,
            page_index,
            ocr_w,
            ocr_h,
        )
        worker.finished.connect(lambda pi, blocks, text: self._on_page_ocr_done(pi, blocks, text))
        worker.error.connect(lambda pi, err: self._on_page_ocr_error(pi, err))
        self._active_workers.append(worker)
        worker.start()

    def _on_page_ocr_done(self, page_index: int, blocks: list, text: str):
        if self._document and page_index < len(self._document.pages):
            page = self._document.pages[page_index]

            # Scale bboxes from hires OCR coordinates to preview coordinates
            suffix = self._document.source_path.suffix.lower()
            if suffix in SUPPORTED_PDF_EXTENSIONS and blocks:
                from src.services.pdf_service import PREVIEW_SCALE
                ratio = PREVIEW_SCALE / self._pdf_service.render_scale
                for block in blocks:
                    block.bbox.x0 *= ratio
                    block.bbox.y0 *= ratio
                    block.bbox.x1 *= ratio
                    block.bbox.y1 *= ratio

            page.text_blocks = blocks
            page.ocr_text = text
            self._thumbnails.update_page_status(page_index, True, False)

            if page_index == self._current_page_index:
                self._show_page(page_index)

        self._cleanup_finished_workers()
        self._ocr_page_chain(page_index + 1)

    def _on_page_ocr_error(self, page_index: int, error: str):
        self._status_label.setText(f"OCR 錯誤（第 {page_index + 1} 頁）：{error}")
        self._cleanup_finished_workers()
        self._ocr_page_chain(page_index + 1)

    def _translate_all_pages(self):
        if not self._document or not self._openai_service:
            return

        self._translate_btn.setEnabled(False)
        self._status_label.setText(UI["translate_running"])
        self._translate_page_chain(0)

    def _translate_page_chain(self, page_index: int):
        if not self._document or page_index >= len(self._document.pages):
            self._translate_btn.setEnabled(True)
            self._status_label.setText(UI["translate_complete"])
            if self._current_page_index >= 0:
                self._show_page(self._current_page_index)
            return

        page = self._document.pages[page_index]

        if not page.ocr_text:
            self._translate_page_chain(page_index + 1)
            return

        total = len(self._document.pages)
        self._status_label.setText(f"翻譯中 {page_index + 1}/{total}...")

        lang = self._lang_combo.currentText()

        # Use per-block translation when blocks are available for accurate bbox mapping
        if page.text_blocks:
            worker = TranslateWorker(
                self._openai_service, page.text_blocks, lang, page_index
            )
            worker.blocks_finished.connect(
                lambda pi, blocks: self._on_page_translate_blocks_done(pi, blocks))
        else:
            worker = TranslateWorker(
                self._openai_service, page.ocr_text, lang, page_index
            )
            worker.finished.connect(
                lambda pi, text: self._on_page_translate_done(pi, text))

        worker.error.connect(lambda pi, err: self._on_page_translate_error(pi, err))
        self._active_workers.append(worker)
        worker.start()

    def _on_page_translate_blocks_done(self, page_index: int, blocks: list):
        """Handle per-block translation results (accurate bbox-to-text mapping)."""
        if self._document and page_index < len(self._document.pages):
            page = self._document.pages[page_index]
            page.text_blocks = blocks
            page.translated_text = "\n".join(
                b.translated_text for b in blocks if b.translated_text)
            self._thumbnails.update_page_status(page_index, bool(page.ocr_text), True)

            if page_index == self._current_page_index:
                self._text_panel.set_translated_text(page.translated_text)

        self._cleanup_finished_workers()
        self._translate_page_chain(page_index + 1)

    def _on_page_translate_done(self, page_index: int, translated_text: str):
        if self._document and page_index < len(self._document.pages):
            page = self._document.pages[page_index]
            page.translated_text = translated_text
            self._thumbnails.update_page_status(page_index, bool(page.ocr_text), True)

            if page_index == self._current_page_index:
                self._text_panel.set_translated_text(translated_text)

        self._cleanup_finished_workers()
        self._translate_page_chain(page_index + 1)

    def _on_page_translate_error(self, page_index: int, error: str):
        self._status_label.setText(f"翻譯錯誤（第 {page_index + 1} 頁）：{error}")
        self._cleanup_finished_workers()
        self._translate_page_chain(page_index + 1)

    def _export_pdf(self):
        if not self._document:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, UI["export_pdf"],
            str(self._document.source_path.parent / (self._document.source_path.stem + "_exported.pdf")),
            "PDF 檔案 (*.pdf)",
        )
        if not path:
            return

        has_translation = any(p.translated_text for p in self._document.pages)
        export_source = ExportSource.TRANSLATED if has_translation else ExportSource.OCR
        overlay_modes = [OverlayMode.VISIBLE, OverlayMode.INVISIBLE, OverlayMode.REPLACE]
        overlay_idx = self._overlay_combo.currentIndex()
        overlay_mode = overlay_modes[overlay_idx] if overlay_idx < len(overlay_modes) else OverlayMode.VISIBLE

        self._status_label.setText("匯出中...")
        try:
            pdf_bytes = self._pdf_service.build_export_pdf(
                self._document, overlay_mode, export_source
            )
            Path(path).write_bytes(pdf_bytes)
            self._status_label.setText(UI["export_complete"])
            QMessageBox.information(self, UI["export_pdf"], f"已匯出至：\n{path}")
        except Exception as e:
            self._status_label.setText(f"匯出錯誤：{e}")
            QMessageBox.critical(self, "錯誤", str(e))

    def _cleanup_finished_workers(self):
        self._active_workers = [w for w in self._active_workers if w.isRunning()]
