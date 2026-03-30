from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.services.openai_service import OpenAIService


class OcrWorker(QThread):
    """Runs OCR on a single image/page in background."""

    finished = Signal(int, list, str)    # (page_index, text_blocks, full_text)
    error = Signal(int, str)             # (page_index, error_message)
    progress = Signal(str)

    def __init__(self, openai_service: OpenAIService,
                 image_source, page_index: int = 0,
                 width: int = 0, height: int = 0):
        super().__init__()
        self.openai_service = openai_service
        self.image_source = image_source  # Path or bytes
        self.page_index = page_index
        self.width = width
        self.height = height

    def run(self):
        try:
            self.progress.emit(f"Running OCR on page {self.page_index + 1}...")
            if isinstance(self.image_source, bytes):
                blocks = self.openai_service.ocr_bytes_with_bboxes(
                    self.image_source, self.width, self.height)
            elif isinstance(self.image_source, (str, Path)):
                blocks = self.openai_service.ocr_with_bboxes(
                    Path(self.image_source), self.width, self.height)
            else:
                self.error.emit(self.page_index, "Invalid image source type")
                return

            text = "\n".join(b.text for b in blocks)
            self.finished.emit(self.page_index, blocks, text)
        except Exception as e:
            self.error.emit(self.page_index, str(e))
