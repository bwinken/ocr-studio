from PySide6.QtCore import QThread, Signal

from src.services.openai_service import OpenAIService


class TranslateWorker(QThread):
    """Translates text in background. Supports page-level or per-block translation."""

    finished = Signal(int, str)          # (page_index, translated_text)
    blocks_finished = Signal(int, list)  # (page_index, translated_blocks)
    error = Signal(int, str)             # (page_index, error_message)
    progress = Signal(str)

    def __init__(self, openai_service: OpenAIService,
                 text_or_blocks, target_lang: str, page_index: int = 0):
        super().__init__()
        self.openai_service = openai_service
        self.target_lang = target_lang
        self.page_index = page_index

        if isinstance(text_or_blocks, list):
            self._blocks = text_or_blocks
            self._text = None
        else:
            self._blocks = None
            self._text = text_or_blocks

    def run(self):
        try:
            self.progress.emit(f"Translating page {self.page_index + 1}...")
            if self._blocks:
                blocks = self.openai_service.translate_blocks(
                    self._blocks, self.target_lang)
                self.blocks_finished.emit(self.page_index, blocks)
            else:
                result = self.openai_service.translate(self._text, self.target_lang)
                self.finished.emit(self.page_index, result)
        except Exception as e:
            self.error.emit(self.page_index, str(e))
