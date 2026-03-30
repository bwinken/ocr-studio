from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class TextBlock:
    text: str
    bbox: BBox
    translated_text: str = ""


@dataclass
class PageData:
    index: int
    image_path: Path
    width: int
    height: int
    has_text_layer: bool = False
    text_blocks: list[TextBlock] = field(default_factory=list)
    ocr_text: str = ""
    translated_text: str = ""


@dataclass
class DocumentData:
    doc_id: str
    filename: str
    source_path: Path
    pages: list[PageData] = field(default_factory=list)


class OverlayMode(Enum):
    INVISIBLE = "invisible"
    VISIBLE = "visible"
    REPLACE = "replace"


class ExportSource(Enum):
    OCR = "ocr"
    TRANSLATED = "translated"


@dataclass
class CaptureResult:
    image_bytes: bytes
    ocr_text: str = ""
    translated_text: str = ""
    text_blocks: list[TextBlock] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class BatchJob:
    input_folder: Path
    output_folder: Path
    target_language: str
    overlay_mode: OverlayMode
    export_source: ExportSource
    do_translate: bool = True
    total_files: int = 0
    processed_files: int = 0
    failed_files: list[str] = field(default_factory=list)
