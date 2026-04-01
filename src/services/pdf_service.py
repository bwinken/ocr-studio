"""PDF parsing and export service using PyMuPDF."""

import io
import os
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from src.models import BBox, DocumentData, ExportSource, OverlayMode, PageData, TextBlock

# Preview uses 1.0x for fast loading; OCR uses 2.0x for accuracy
PREVIEW_SCALE = 1.0
OCR_SCALE = 2.0


class PdfService:
    def __init__(self, render_scale: float = 2.0):
        self.render_scale = render_scale

    def load_pdf(self, pdf_path: Path, work_dir: Path) -> list[PageData]:
        """Open PDF, render each page as small preview PNG, extract text layers."""
        work_dir.mkdir(parents=True, exist_ok=True)
        pdf_bytes = pdf_path.read_bytes()
        pages = []

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for i, page in enumerate(doc):
                mat = fitz.Matrix(PREVIEW_SCALE, PREVIEW_SCALE)
                pix = page.get_pixmap(matrix=mat)
                img_path = work_dir / f"page_{i}.png"
                pix.save(str(img_path))

                rect = page.rect
                ox, oy = rect.x0, rect.y0

                text_dict = page.get_text("dict")
                text_blocks = []
                text_parts = []

                for block in text_dict.get("blocks", []):
                    if block.get("type") == 0:
                        block_text_parts = []
                        for line in block.get("lines", []):
                            line_text = ""
                            for span in line.get("spans", []):
                                line_text += span.get("text", "")
                            if line_text.strip():
                                block_text_parts.append(line_text.strip())

                        block_text = " ".join(block_text_parts)
                        if block_text.strip():
                            bbox = block["bbox"]
                            text_blocks.append(TextBlock(
                                text=block_text,
                                bbox=BBox(
                                    x0=(bbox[0] - ox) * PREVIEW_SCALE,
                                    y0=(bbox[1] - oy) * PREVIEW_SCALE,
                                    x1=(bbox[2] - ox) * PREVIEW_SCALE,
                                    y1=(bbox[3] - oy) * PREVIEW_SCALE,
                                ),
                            ))
                            text_parts.append(block_text)

                has_text = len(text_blocks) > 0
                pages.append(PageData(
                    index=i,
                    image_path=img_path,
                    width=pix.width,
                    height=pix.height,
                    has_text_layer=has_text,
                    text_blocks=text_blocks if has_text else [],
                    ocr_text="\n".join(text_parts) if has_text else "",
                ))

        return pages

    def render_page_hires(self, pdf_path: Path, page_index: int, work_dir: Path) -> Path:
        """Render a single page at high resolution for OCR."""
        pdf_bytes = pdf_path.read_bytes()
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            page = doc[page_index]
            mat = fitz.Matrix(self.render_scale, self.render_scale)
            pix = page.get_pixmap(matrix=mat)
            out_path = work_dir / f"page_{page_index}_hires.png"
            pix.save(str(out_path))
        return out_path

    def load_image(self, image_path: Path, work_dir: Path, index: int = 0) -> PageData:
        """Convert standalone image to PageData (resize for preview if large)."""
        work_dir.mkdir(parents=True, exist_ok=True)
        img = Image.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize large images for preview (max 1200px wide)
        max_preview_w = 1200
        if img.width > max_preview_w:
            ratio = max_preview_w / img.width
            new_h = int(img.height * ratio)
            preview = img.resize((max_preview_w, new_h), Image.LANCZOS)
        else:
            preview = img

        out_path = work_dir / f"page_{index}.png"
        preview.save(str(out_path))

        page = PageData(
            index=index,
            image_path=out_path,
            width=preview.width,
            height=preview.height,
        )
        img.close()
        if preview is not img:
            preview.close()
        return page

    def make_thumbnail(self, image_path: Path, max_width: int = 200) -> bytes:
        img = Image.open(image_path)
        ratio = max_width / img.width
        thumb = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        thumb.save(buf, format="PNG")
        img.close()
        return buf.getvalue()

    def build_export_pdf(self, document: DocumentData,
                         overlay_mode: OverlayMode,
                         export_source: ExportSource) -> bytes:
        """Build PDF with original images and text overlay at detected positions."""
        out = fitz.open()

        for page_data in document.pages:
            img_path = str(page_data.image_path)
            if not os.path.exists(img_path):
                continue

            # Create page at pixel dimensions so text coordinates match exactly
            pw, ph = float(page_data.width), float(page_data.height)
            page = out.new_page(width=pw, height=ph)

            if overlay_mode != OverlayMode.REPLACE:
                page.insert_image(fitz.Rect(0, 0, pw, ph), filename=img_path)
            else:
                page.draw_rect(fitz.Rect(0, 0, pw, ph), color=(1, 1, 1), fill=(1, 1, 1))

            blocks = page_data.text_blocks
            if not blocks:
                continue

            # No scaling needed - page size matches image pixel size
            scale_x = 1.0
            scale_y = 1.0

            translated_lines = []
            if export_source == ExportSource.TRANSLATED and page_data.translated_text:
                translated_lines = [l for l in page_data.translated_text.split("\n") if l.strip()]

            for i, block in enumerate(blocks):
                bbox = block.bbox
                x0 = bbox.x0 * scale_x
                y0 = bbox.y0 * scale_y
                x1 = bbox.x1 * scale_x
                y1 = bbox.y1 * scale_y

                if x1 <= x0 or y1 <= y0:
                    continue

                text = block.text
                if export_source == ExportSource.TRANSLATED:
                    if block.translated_text:
                        text = block.translated_text
                    elif i < len(translated_lines):
                        text = translated_lines[i]

                text_rect = fitz.Rect(x0, y0, x1, y1)
                line_height = y1 - y0

                # Draw background ONCE (not in retry loop)
                if overlay_mode == OverlayMode.VISIBLE:
                    page.draw_rect(text_rect, color=None, fill=(1, 1, 1), fill_opacity=0.85)

                # Use CJK font if text contains CJK characters
                fontname = "helv"
                if any(ord(c) > 0x2E80 for c in text):
                    fontname = "china-t"

                # Auto-shrink font until text fits (insert_textbox returns >= 0)
                font_size = max(6, min(line_height * 0.55, 20))
                for attempt_fs in [font_size, font_size * 0.8, font_size * 0.6, 6]:
                    fs = max(5, attempt_fs)
                    try:
                        if overlay_mode == OverlayMode.INVISIBLE:
                            rc = page.insert_textbox(
                                text_rect, text,
                                fontname=fontname,
                                fontsize=fs, color=(0, 0, 0),
                                render_mode=3,
                            )
                        else:
                            rc = page.insert_textbox(
                                text_rect, text,
                                fontname=fontname,
                                fontsize=fs, color=(0.1, 0.1, 0.1),
                            )

                        if rc >= 0:
                            break  # text fits
                    except Exception:
                        break

        pdf_bytes = out.tobytes()
        out.close()
        return pdf_bytes
