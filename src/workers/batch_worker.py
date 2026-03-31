"""Batch folder processing worker thread."""

import tempfile
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.constants import SUPPORTED_IMAGE_EXTENSIONS, SUPPORTED_PDF_EXTENSIONS
from src.models import DocumentData, ExportSource, OverlayMode
from src.services.image_service import ImageService
from src.services.openai_service import OpenAIService
from src.services.pdf_service import PdfService


class _Cancelled(Exception):
    pass


class BatchWorker(QThread):
    file_started = Signal(str, int, int)
    file_completed = Signal(str)
    file_failed = Signal(str, str)
    all_completed = Signal(int, int)
    progress_detail = Signal(str)

    def __init__(
        self,
        openai_service: OpenAIService,
        pdf_service: PdfService,
        image_service: ImageService,
        input_folder: Path,
        output_folder: Path,
        target_lang: str,
        overlay_mode: OverlayMode,
        export_source: ExportSource,
        do_translate: bool = True,
        output_txt: bool = False,
    ):
        super().__init__()
        self._openai = openai_service
        self._pdf = pdf_service
        self._img = image_service
        self._input = input_folder
        self._output = output_folder
        self._target_lang = target_lang
        self._overlay_mode = overlay_mode
        self._export_source = export_source
        self._do_translate = do_translate
        self._output_txt = output_txt

    def _check_cancel(self):
        if self.isInterruptionRequested():
            raise _Cancelled()

    def run(self):
        files = self._collect_files()
        if not files:
            self.all_completed.emit(0, 0)
            return

        self._output.mkdir(parents=True, exist_ok=True)
        success = 0
        failed = 0

        for i, filepath in enumerate(files):
            if self.isInterruptionRequested():
                break

            self.file_started.emit(filepath.name, i + 1, len(files))

            try:
                self._process_file(filepath)
                self.file_completed.emit(filepath.name)
                success += 1
            except _Cancelled:
                self.file_failed.emit(filepath.name, "已取消")
                failed += 1
                break
            except Exception as e:
                self.file_failed.emit(filepath.name, str(e))
                failed += 1

        self.all_completed.emit(success, failed)

    def _collect_files(self) -> list[Path]:
        all_exts = SUPPORTED_PDF_EXTENSIONS | SUPPORTED_IMAGE_EXTENSIONS
        return sorted(
            p for p in self._input.rglob("*")
            if p.is_file() and p.suffix.lower() in all_exts
        )

    def _process_file(self, filepath: Path):
        suffix = filepath.suffix.lower()
        work_dir = Path(tempfile.mkdtemp(prefix="ocrbatch_"))

        if suffix in SUPPORTED_PDF_EXTENSIONS:
            self._process_pdf(filepath, work_dir)
        elif suffix in SUPPORTED_IMAGE_EXTENSIONS:
            self._process_image(filepath, work_dir)

    def _process_pdf(self, filepath: Path, work_dir: Path):
        self.progress_detail.emit(f"{filepath.name}: 載入 PDF...")
        pages = self._pdf.load_pdf(filepath, work_dir)
        self._check_cancel()

        doc = DocumentData(
            doc_id="batch",
            filename=filepath.name,
            source_path=filepath,
            pages=pages,
        )

        # OCR
        for page in pages:
            self._check_cancel()
            if page.has_text_layer and page.ocr_text:
                continue
            self.progress_detail.emit(
                f"{filepath.name}: OCR 第 {page.index + 1}/{len(pages)} 頁"
            )
            blocks = self._openai.ocr_with_bboxes(
                page.image_path, page.width, page.height
            )
            self._check_cancel()
            page.text_blocks = blocks
            page.ocr_text = "\n".join(b.text for b in blocks)

        # Translate
        if self._do_translate:
            for page in pages:
                self._check_cancel()
                if not page.ocr_text:
                    continue
                self.progress_detail.emit(
                    f"{filepath.name}: 翻譯第 {page.index + 1}/{len(pages)} 頁"
                )
                translated = self._openai.translate(page.ocr_text, self._target_lang)
                self._check_cancel()
                page.translated_text = translated
                if page.text_blocks:
                    self._openai.translate_blocks(page.text_blocks, self._target_lang)
                    self._check_cancel()

        # Export
        self._check_cancel()
        rel = filepath.relative_to(self._input)

        if self._output_txt:
            self._export_pdf_as_txt(doc, rel)
        else:
            self.progress_detail.emit(f"{filepath.name}: 匯出 PDF...")
            out_path = self._output / rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_bytes = self._pdf.build_export_pdf(doc, self._overlay_mode, self._export_source)
            out_path.write_bytes(pdf_bytes)

    def _export_pdf_as_txt(self, doc: DocumentData, rel: Path):
        """Export PDF pages as txt. Multi-page: name_1.txt, name_2.txt, ..."""
        stem = rel.with_suffix("").as_posix().replace("/", "_")

        if len(doc.pages) == 1:
            # Single page → one file
            out_path = self._output / f"{stem}.txt"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            text = self._get_page_text(doc.pages[0])
            self.progress_detail.emit(f"{doc.filename}: 匯出 TXT...")
            out_path.write_text(text, encoding="utf-8")
        else:
            # Multi-page → name_1.txt, name_2.txt, ...
            for page in doc.pages:
                out_path = self._output / f"{stem}_{page.index + 1}.txt"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                text = self._get_page_text(page)
                self.progress_detail.emit(
                    f"{doc.filename}: 匯出 TXT 第 {page.index + 1}/{len(doc.pages)} 頁"
                )
                out_path.write_text(text, encoding="utf-8")

    def _process_image(self, filepath: Path, work_dir: Path):
        self.progress_detail.emit(f"{filepath.name}: OCR 辨識中...")
        blocks = self._openai.ocr_with_bboxes(filepath)
        self._check_cancel()

        if self._do_translate and blocks:
            self.progress_detail.emit(f"{filepath.name}: 翻譯中...")
            self._openai.translate_blocks(blocks, self._target_lang)
            self._check_cancel()

        rel = filepath.relative_to(self._input)

        if self._output_txt:
            # Image → single txt
            out_path = self._output / rel.with_suffix(".txt")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if self._do_translate:
                text = "\n".join(b.translated_text or b.text for b in blocks)
            else:
                text = "\n".join(b.text for b in blocks)
            self.progress_detail.emit(f"{filepath.name}: 匯出 TXT...")
            out_path.write_text(text, encoding="utf-8")
        else:
            self.progress_detail.emit(f"{filepath.name}: 匯出圖片...")
            out_path = self._output / rel.with_suffix(".png")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            use_translated = self._do_translate and self._export_source == ExportSource.TRANSLATED
            self._img.save_with_overlay(filepath, out_path, blocks, self._overlay_mode, use_translated)

    def _get_page_text(self, page) -> str:
        """Get the best text for a page: translated > ocr."""
        if self._do_translate and page.translated_text:
            return page.translated_text
        return page.ocr_text or ""
