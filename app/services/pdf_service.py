"""PDF parsing and export service using PyMuPDF."""

import io
import os
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from app.config import PDF_RENDER_SCALE


def pdf_to_pages(pdf_bytes: bytes, doc_dir: Path) -> list[dict]:
    """Extract pages from PDF as PNG images. Also checks for embedded text."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        # Render page as image
        mat = fitz.Matrix(PDF_RENDER_SCALE, PDF_RENDER_SCALE)
        pix = page.get_pixmap(matrix=mat)
        img_path = doc_dir / f"page_{i}.png"
        pix.save(str(img_path))

        # Try to extract existing text layer
        text_dict = page.get_text("dict")
        embedded_blocks = []
        embedded_text_parts = []

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # text block
                block_text_parts = []
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    if line_text.strip():
                        block_text_parts.append(line_text.strip())

                block_text = " ".join(block_text_parts)
                if block_text.strip():
                    bbox = block["bbox"]  # (x0, y0, x1, y1) in PDF coords
                    # Scale bbox to match rendered image coords
                    embedded_blocks.append({
                        "text": block_text,
                        "bbox": {
                            "x0": bbox[0] * PDF_RENDER_SCALE,
                            "y0": bbox[1] * PDF_RENDER_SCALE,
                            "x1": bbox[2] * PDF_RENDER_SCALE,
                            "y1": bbox[3] * PDF_RENDER_SCALE,
                        },
                    })
                    embedded_text_parts.append(block_text)

        has_text_layer = len(embedded_blocks) > 0

        pages.append({
            "index": i,
            "image_path": str(img_path),
            "width": pix.width,
            "height": pix.height,
            "has_text_layer": has_text_layer,
            "ocr_result": {
                "lines": embedded_blocks,
                "text": "\n".join(embedded_text_parts),
            } if has_text_layer else None,
            "ocr_text": "\n".join(embedded_text_parts) if has_text_layer else "",
            "translated_text": "",
        })

    doc.close()
    return pages


def image_to_page(image_bytes: bytes, doc_dir: Path, index: int) -> dict:
    """Convert an uploaded image to a page entry."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    img_path = doc_dir / f"page_{index}.png"
    img.save(str(img_path))

    return {
        "index": index,
        "image_path": str(img_path),
        "width": img.width,
        "height": img.height,
        "has_text_layer": False,
        "ocr_result": None,
        "ocr_text": "",
        "translated_text": "",
    }


def make_thumbnail(image_path: str, max_width: int = 200) -> bytes:
    img = Image.open(image_path)
    ratio = max_width / img.width
    thumb = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    thumb.save(buf, format="PNG")
    return buf.getvalue()


def build_export_pdf(doc_data: dict, overlay_mode: str, export_source: str) -> bytes:
    """Build PDF with original images and text overlay at detected positions."""
    out = fitz.open()

    for page_data in doc_data["pages"]:
        img_path = page_data["image_path"]
        if not os.path.exists(img_path):
            continue

        img_doc = fitz.open(img_path)
        rect = img_doc[0].rect
        page = out.new_page(width=rect.width, height=rect.height)

        if overlay_mode != "replace":
            page.insert_image(page.rect, filename=img_path)
        else:
            page.draw_rect(page.rect, color=(1, 1, 1), fill=(1, 1, 1))

        img_doc.close()

        ocr_result = page_data.get("ocr_result")
        if not ocr_result or not ocr_result.get("lines"):
            continue

        # Scale: image coords → PDF page coords
        # Image was rendered at PDF_RENDER_SCALE, page size = image size
        scale_x = page.rect.width / page_data["width"]
        scale_y = page.rect.height / page_data["height"]

        # Prepare translated lines if needed
        translated_text = page_data.get("translated_text", "")
        translated_lines = [l for l in translated_text.split("\n") if l.strip()] if translated_text else []
        use_translated = export_source == "translated" and len(translated_lines) > 0

        for i, line in enumerate(ocr_result["lines"]):
            bbox = line["bbox"]
            x0 = bbox["x0"] * scale_x
            y0 = bbox["y0"] * scale_y
            x1 = bbox["x1"] * scale_x
            y1 = bbox["y1"] * scale_y

            # Skip zero-size boxes
            if x1 <= x0 or y1 <= y0:
                continue

            text = line["text"]
            if use_translated and i < len(translated_lines):
                text = translated_lines[i]

            line_height = y1 - y0
            font_size = max(6, min(line_height * 0.7, 24))
            text_rect = fitz.Rect(x0, y0, x1, y1)

            try:
                if overlay_mode == "invisible":
                    page.insert_textbox(
                        text_rect, text,
                        fontsize=font_size, color=(0, 0, 0), opacity=0.01,
                    )
                elif overlay_mode == "visible":
                    page.draw_rect(text_rect, color=None, fill=(1, 1, 1), opacity=0.85)
                    page.insert_textbox(
                        text_rect, text,
                        fontsize=font_size, color=(0.1, 0.1, 0.1),
                    )
                else:  # replace
                    page.insert_textbox(
                        text_rect, text,
                        fontsize=font_size, color=(0.1, 0.1, 0.1),
                    )
            except Exception:
                pass  # Skip lines with encoding issues

    pdf_bytes = out.tobytes()
    out.close()
    return pdf_bytes
