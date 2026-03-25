"""
Configuration via environment variables.
Three independent VLM services: detection (bbox), OCR (text), translation.
All prompts and endpoints are separately configurable.
"""

import os
from pathlib import Path

# ── Paths ──
APP_DIR = Path(__file__).parent
PROJECT_DIR = APP_DIR.parent
STORAGE_DIR = APP_DIR / "storage"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"

STORAGE_DIR.mkdir(exist_ok=True)

# ── PDF rendering scale (higher = better OCR quality but larger images) ──
PDF_RENDER_SCALE = float(os.getenv("PDF_RENDER_SCALE", "2.0"))


# ── VLM: Text Block Detection (returns bounding boxes) ──
VLM_DET_ENDPOINT = os.getenv("VLM_DET_ENDPOINT", "http://localhost:8000/v1/chat/completions")
VLM_DET_MODEL = os.getenv("VLM_DET_MODEL", "glm-ocr")
VLM_DET_API_KEY = os.getenv("VLM_DET_API_KEY", "")
VLM_DET_MAX_TOKENS = int(os.getenv("VLM_DET_MAX_TOKENS", "4096"))
VLM_DET_TEMPERATURE = float(os.getenv("VLM_DET_TEMPERATURE", "0.1"))
VLM_DET_PROMPT = os.getenv("VLM_DET_PROMPT", """请识别图片中所有文字区块的位置。返回JSON数组：
[{"bbox": [x0, y0, x1, y1], "label": "text"}, ...]
坐标为像素值，(x0,y0)左上角，(x1,y1)右下角。
只返回JSON，不要其他内容。""")


# ── VLM: OCR Text Recognition ──
VLM_OCR_ENDPOINT = os.getenv("VLM_OCR_ENDPOINT", "http://localhost:8000/v1/chat/completions")
VLM_OCR_MODEL = os.getenv("VLM_OCR_MODEL", "glm-ocr")
VLM_OCR_API_KEY = os.getenv("VLM_OCR_API_KEY", "")
VLM_OCR_MAX_TOKENS = int(os.getenv("VLM_OCR_MAX_TOKENS", "4096"))
VLM_OCR_TEMPERATURE = float(os.getenv("VLM_OCR_TEMPERATURE", "0.1"))
VLM_OCR_PROMPT = os.getenv("VLM_OCR_PROMPT", """请精确识别图片中的所有文字，保持原始排版格式。
只返回识别出的文字内容，不要添加任何说明。""")


# ── VLM: Combined Detection + OCR (single pass, returns bbox + text) ──
# If your model supports returning both bbox and text in one call, use this mode.
VLM_COMBINED_MODE = os.getenv("VLM_COMBINED_MODE", "true").lower() in ("true", "1", "yes")
VLM_COMBINED_PROMPT = os.getenv("VLM_COMBINED_PROMPT", """请识别图片中所有文字区块，返回JSON数组格式：
[{"text": "识别的文字", "bbox": [x0, y0, x1, y1]}, ...]
坐标为像素值，(x0,y0)左上角，(x1,y1)右下角。
只返回JSON，不要其他内容。""")


# ── VLM: Translation ──
VLM_TRANSLATE_ENDPOINT = os.getenv("VLM_TRANSLATE_ENDPOINT", "http://localhost:8000/v1/chat/completions")
VLM_TRANSLATE_MODEL = os.getenv("VLM_TRANSLATE_MODEL", "gptoss-20b")
VLM_TRANSLATE_API_KEY = os.getenv("VLM_TRANSLATE_API_KEY", "")
VLM_TRANSLATE_MAX_TOKENS = int(os.getenv("VLM_TRANSLATE_MAX_TOKENS", "4096"))
VLM_TRANSLATE_TEMPERATURE = float(os.getenv("VLM_TRANSLATE_TEMPERATURE", "0.3"))
VLM_TRANSLATE_PROMPT = os.getenv("VLM_TRANSLATE_PROMPT", """You are a professional translator. Translate the text accurately while preserving the original formatting and structure. Output ONLY the translated text, nothing else.""")


# ── Cleanup ──
STORAGE_TTL_MINUTES = int(os.getenv("STORAGE_TTL_MINUTES", "30"))
