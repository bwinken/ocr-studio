"""Batch folder processing worker thread."""

import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.constants import SUPPORTED_IMAGE_EXTENSIONS, SUPPORTED_PDF_EXTENSIONS
from src.models import DocumentData, ExportSource, OverlayMode
from src.services.image_service import ImageService
from src.services.openai_service import OpenAIService
from src.services.pdf_service import PdfService


class BatchWorker(QThread):
    """Process all files in input folder, produce output in output folder."""

    file_started = Signal(str, int, int)       # (filename, current, total)
    file_completed = Signal(str)               # filename
    file_failed = Signal(str, str)             # (filename, error)
    all_completed = Signal(int, int)           # (success_count, fail_count)
    progress_detail = Signal(str)              # Detailed status

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
            except Exception as e:
                self.file_failed.emit(filepath.name, str(e))
                failed += 1

        self.all_completed.emit(success, failed)

    def _collect_files(self) -> list[Path]:
        """Find all supported files in input folder (recursive)."""
        all_exts = SUPPORTED_PDF_EXTENSIONS | SUPPORTED_IMAGE_EXTENSIONS
        files = []
        for p in sorted(self._input.rglob("*")):
            if p.is_file() and p.suffix.lower() in all_exts:
                files.append(p)
        return files

    def _process_file(self, filepath: Path):
        suffix = filepath.suffix.lower()
        work_dir = Path(tempfile.mkdtemp(prefix="ocrbatch_"))

        if suffix in SUPPORTED_PDF_EXTENSIONS:
            self._process_pdf(filepath, work_dir)
        elif suffix in SUPPORTED_IMAGE_EXTENSIONS:
            self._process_image(filepath, work_dir)

    def _process_pdf(self, filepath: Path, work_dir: Path):
        self.progress_detail.emit(f"{filepath.name}: Loading PDF...")
        pages = self._pdf.load_pdf(filepath, work_dir)

        doc = DocumentData(
            doc_id="batch",
            filename=filepath.name,
            source_path=filepath,
            pages=pages,
        )

        # OCR pages without text layer
        for page in pages:
            if self.isInterruptionRequested():
                return
            if page.has_text_layer and page.ocr_text:
                continue
            self.progress_detail.emit(
                f"{filepath.name}: OCR page {page.index + 1}/{len(pages)}"
            )
            blocks = self._openai.ocr_with_bboxes(
                page.image_path, page.width, page.height
            )
            page.text_blocks = blocks
            page.ocr_text = "\n".join(b.text for b in blocks)

        # Translate
        if self._do_translate:
            for page in pages:
                if self.isInterruptionRequested():
                    return
                if not page.ocr_text:
                    continue
                self.progress_detail.emit(
                    f"{filepath.name}: Translating page {page.index + 1}/{len(pages)}"
                )
                translated = self._openai.translate(page.ocr_text, self._target_lang)
                page.translated_text = translated

                # Also translate blocks for overlay
                if page.text_blocks:
                    self._openai.translate_blocks(page.text_blocks, self._target_lang)

        # Export PDF
        self.progress_detail.emit(f"{filepath.name}: Exporting...")
        rel = filepath.relative_to(self._input)
        out_path = self._output / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        pdf_bytes = self._pdf.build_export_pdf(doc, self._overlay_mode, self._export_source)
        out_path.write_bytes(pdf_bytes)

    def _process_image(self, filepath: Path, work_dir: Path):
        self.progress_detail.emit(f"{filepath.name}: Running OCR...")
        blocks = self._openai.ocr_with_bboxes(filepath)

        if self._do_translate and blocks:
            self.progress_detail.emit(f"{filepath.name}: Translating...")
            self._openai.translate_blocks(blocks, self._target_lang)

        # Export with overlay
        self.progress_detail.emit(f"{filepath.name}: Exporting...")
        rel = filepath.relative_to(self._input)
        out_path = self._output / rel.with_suffix(".png")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        use_translated = self._do_translate and self._export_source == ExportSource.TRANSLATED
        self._img.save_with_overlay(filepath, out_path, blocks, self._overlay_mode, use_translated)
