"""OpenAI-compatible API client for OCR and translation.

Supports:
- Separate OCR and translation endpoints (different base_url/model)
- Structured output (response_format) for reliable JSON
- Generic VLM: API returns both text + bbox in one call
- PaddleOCR-VL: auto-detected by model name, uses "Spotting:" prompt
"""

import base64
import io
import json
import re
from pathlib import Path

import httpx

from src.models import BBox, TextBlock


class OpenAIService:
    ENDPOINT_PATH = "/chat/completions"

    # Prompt for combined OCR (text + bbox) via API
    OCR_COMBINED_PROMPT = (
        "Analyze this image ({width}x{height} pixels) and extract all text blocks. "
        "For each text block, return the text content and a TIGHT bounding box "
        "as integer pixel coordinates [x0, y0, x1, y1] where (x0,y0) is the "
        "top-left corner and (x1,y1) is the bottom-right corner of the text. "
        "The bbox must tightly enclose the visible text with minimal padding. "
        "Coordinates must be within 0-{width} for x and 0-{height} for y. "
        "Group nearby lines into a single block only if they belong together semantically."
    )

    # Prompt for plain text OCR (no bbox)
    OCR_PLAIN_PROMPT = (
        "Extract all text from this image. Preserve the original formatting "
        "and layout as much as possible. Return ONLY the extracted text."
    )

    TRANSLATE_SYSTEM_PROMPT = (
        "You are a professional translator. Translate accurately while "
        "preserving the original formatting and structure. "
        "Output ONLY the translated text, nothing else."
    )

    # JSON schema for structured output
    OCR_RESPONSE_SCHEMA = {
        "type": "json_schema",
        "json_schema": {
            "name": "ocr_result",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "blocks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "bbox": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                },
                            },
                            "required": ["text", "bbox"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["blocks"],
                "additionalProperties": False,
            },
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        ocr_model: str = "gpt-4o",
        translate_model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature_ocr: float = 0.1,
        temperature_translate: float = 0.3,
        # Separate OCR endpoint (optional - falls back to base_url)
        ocr_base_url: str = "",
        ocr_api_key: str = "",
        use_structured_output: bool = True,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.ocr_model = ocr_model
        self.translate_model = translate_model
        self.max_tokens = max_tokens
        self.temperature_ocr = temperature_ocr
        self.temperature_translate = temperature_translate

        # OCR endpoint: use separate if provided, otherwise same as base
        self.ocr_base_url = (ocr_base_url.rstrip("/") if ocr_base_url else self.base_url)
        self.ocr_api_key = ocr_api_key or api_key

        self.use_structured_output = use_structured_output

    @property
    def _is_paddle_ocr(self) -> bool:
        """Auto-detect PaddleOCR-VL model by name."""
        return "paddle" in self.ocr_model.lower()

    @property
    def _translate_endpoint(self) -> str:
        return f"{self.base_url}{self.ENDPOINT_PATH}"

    @property
    def _ocr_endpoint(self) -> str:
        return f"{self.ocr_base_url}{self.ENDPOINT_PATH}"

    def _ocr_headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.ocr_api_key:
            h["Authorization"] = f"Bearer {self.ocr_api_key}"
        return h

    def _translate_headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    @staticmethod
    def _check_response(resp: httpx.Response):
        """Raise with the actual API error message, not just status code."""
        if resp.status_code >= 400:
            try:
                body = resp.json()
                err_msg = body.get("error", {}).get("message", resp.text)
            except Exception:
                err_msg = resp.text
            raise RuntimeError(f"API {resp.status_code}: {err_msg}")

    def _call_ocr_vision(self, prompt: str, image_b64: str,
                         use_structured: bool = False) -> str:
        """Call OCR endpoint with vision."""
        if not image_b64.startswith("data:"):
            image_b64 = f"data:image/png;base64,{image_b64}"

        payload = {
            "model": self.ocr_model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
            "max_completion_tokens": self.max_tokens,
            "temperature": 0.0 if self._is_paddle_ocr else self.temperature_ocr,
        }

        # PaddleOCR-VL: never use structured output
        if self._is_paddle_ocr:
            use_structured = False

        with httpx.Client(timeout=180) as client:
            if use_structured and self.use_structured_output:
                payload["response_format"] = self.OCR_RESPONSE_SCHEMA
                resp = client.post(self._ocr_endpoint, headers=self._ocr_headers(), json=payload)
                if resp.status_code == 400:
                    # Structured output failed — retry without it
                    payload.pop("response_format", None)
                    msg = payload["messages"][0]["content"]
                    for part in msg:
                        if part.get("type") == "text":
                            part["text"] += (
                                '\nReturn a JSON array: '
                                '[{"text": "...", "bbox": [x0, y0, x1, y1]}, ...] '
                                'Return ONLY the JSON, no other text.'
                            )
                            break
                    resp = client.post(self._ocr_endpoint, headers=self._ocr_headers(), json=payload)

                self._check_response(resp)
                return resp.json()["choices"][0]["message"]["content"]
            else:
                resp = client.post(self._ocr_endpoint, headers=self._ocr_headers(), json=payload)
                self._check_response(resp)
                return resp.json()["choices"][0]["message"]["content"]

    def _call_translate(self, system: str, user: str) -> str:
        """Call translation endpoint."""
        payload = {
            "model": self.translate_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_completion_tokens": self.max_tokens,
            "temperature": self.temperature_translate,
        }
        with httpx.Client(timeout=180) as client:
            resp = client.post(self._translate_endpoint, headers=self._translate_headers(), json=payload)
            self._check_response(resp)
            return resp.json()["choices"][0]["message"]["content"]

    # ── Image helpers ──

    @staticmethod
    def _image_file_to_b64(image_path: Path) -> str:
        with open(image_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

    @staticmethod
    def _bytes_to_b64(image_bytes: bytes) -> str:
        return f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"

    @staticmethod
    def _optimize_image_bytes(image_bytes: bytes, max_dim: int = 1600) -> tuple[bytes, int, int]:
        """Resize if too large for faster API calls."""
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            w, h = int(w * ratio), int(h * ratio)
            img = img.resize((w, h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), w, h

    # ── JSON parsing ──

    @staticmethod
    def _parse_json_response(text: str) -> list[dict]:
        """Extract JSON array from response."""
        text = text.strip()

        # Structured output: response is a JSON object with "blocks" array
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and "blocks" in obj:
                return obj["blocks"]
            if isinstance(obj, list):
                return obj
            return []
        except json.JSONDecodeError:
            pass

        # Markdown code block
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                if isinstance(result, dict) and "blocks" in result:
                    return result["blocks"]
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # Bare [...] array
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        return []

    def _parse_blocks(self, raw: str) -> list[TextBlock]:
        """Parse API response into TextBlock list."""
        items = self._parse_json_response(raw)
        blocks = []
        for item in items:
            text = item.get("text", "")
            bbox = item.get("bbox")
            if bbox and len(bbox) == 4 and text:
                blocks.append(TextBlock(
                    text=text,
                    bbox=BBox(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]),
                ))
        return blocks

    # ── PaddleOCR-VL spotting parser ──

    @staticmethod
    def _parse_paddle_spotting(raw: str, img_w: int, img_h: int) -> list[TextBlock]:
        """Parse PaddleOCR-VL 'Spotting:' response.

        PaddleOCR spotting output format (one line per text region):
            text_content <poly> x1,y1 x2,y2 x3,y3 x4,y4 </poly>
        The 4 points are a quadrilateral (may be rotated).
        We convert to axis-aligned bbox [min_x, min_y, max_x, max_y].
        """
        blocks = []
        for line in raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Extract polygon coordinates
            poly_match = re.search(r"<poly>\s*(.+?)\s*</poly>", line)
            if poly_match:
                text = line[:poly_match.start()].strip()
                coords_str = poly_match.group(1)
            else:
                # No polygon — plain text line, skip bbox
                continue

            if not text:
                continue

            # Parse "x1,y1 x2,y2 x3,y3 x4,y4"
            try:
                points = []
                for pair in coords_str.split():
                    parts = pair.split(",")
                    if len(parts) == 2:
                        points.append((float(parts[0]), float(parts[1])))

                if len(points) < 3:
                    continue

                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                x0 = max(0, min(xs))
                y0 = max(0, min(ys))
                x1 = min(img_w, max(xs))
                y1 = min(img_h, max(ys))

                if x1 > x0 and y1 > y0:
                    blocks.append(TextBlock(
                        text=text,
                        bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1),
                    ))
            except (ValueError, IndexError):
                continue

        return blocks

    @staticmethod
    def _parse_paddle_ocr(raw: str) -> str:
        """Parse PaddleOCR-VL 'OCR:' response — just plain text."""
        # PaddleOCR OCR mode returns markdown-formatted text
        return raw.strip()

    # ── Public OCR methods ──

    def ocr_with_bboxes(self, image_path: Path, width: int = 0, height: int = 0) -> list[TextBlock]:
        """OCR image file, return text blocks with bounding boxes."""
        from PIL import Image as PILImage

        if width == 0 or height == 0:
            with PILImage.open(image_path) as img:
                width, height = img.size

        b64 = self._image_file_to_b64(image_path)

        if self._is_paddle_ocr:
            raw = self._call_ocr_vision("Spotting:", b64)
            return self._parse_paddle_spotting(raw, width, height)
        else:
            prompt = self.OCR_COMBINED_PROMPT.format(width=width, height=height)
            raw = self._call_ocr_vision(prompt, b64, use_structured=True)
            return self._parse_blocks(raw)

    def ocr_bytes_with_bboxes(self, image_bytes: bytes, width: int = 0, height: int = 0) -> list[TextBlock]:
        """OCR from in-memory image bytes."""
        optimized, width, height = self._optimize_image_bytes(image_bytes)
        b64 = self._bytes_to_b64(optimized)

        if self._is_paddle_ocr:
            raw = self._call_ocr_vision("Spotting:", b64)
            return self._parse_paddle_spotting(raw, width, height)
        else:
            prompt = self.OCR_COMBINED_PROMPT.format(width=width, height=height)
            raw = self._call_ocr_vision(prompt, b64, use_structured=True)
            return self._parse_blocks(raw)

    def ocr_plain(self, image_path: Path) -> str:
        """OCR image, return plain text."""
        b64 = self._image_file_to_b64(image_path)
        prompt = "OCR:" if self._is_paddle_ocr else self.OCR_PLAIN_PROMPT
        return self._call_ocr_vision(prompt, b64)

    def ocr_bytes_plain(self, image_bytes: bytes) -> str:
        """OCR from in-memory bytes, plain text."""
        optimized, _, _ = self._optimize_image_bytes(image_bytes)
        b64 = self._bytes_to_b64(optimized)
        prompt = "OCR:" if self._is_paddle_ocr else self.OCR_PLAIN_PROMPT
        return self._call_ocr_vision(prompt, b64)

    # ── Translation ──

    def translate(self, text: str, target_lang: str) -> str:
        user_msg = f"Translate the following text to {target_lang}. Output ONLY the translated text:\n\n{text}"
        return self._call_translate(self.TRANSLATE_SYSTEM_PROMPT, user_msg)

    def translate_blocks(self, blocks: list[TextBlock], target_lang: str) -> list[TextBlock]:
        """Translate text blocks, preserving bbox mapping."""
        if not blocks:
            return blocks

        numbered = "\n".join(f"{i+1}. {b.text}" for i, b in enumerate(blocks))
        user_msg = (
            f"Translate each numbered line below to {target_lang}. "
            f"Return the same numbered format. Output ONLY the translated lines:\n\n{numbered}"
        )
        raw = self._call_translate(self.TRANSLATE_SYSTEM_PROMPT, user_msg)

        lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
        translated = []
        for line in lines:
            match = re.match(r"^\d+[\.\):\s]+(.+)", line)
            translated.append(match.group(1) if match else line)

        for i, block in enumerate(blocks):
            if i < len(translated):
                block.translated_text = translated[i]

        return blocks
