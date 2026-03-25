"""Document upload, OCR, translation, and export routes."""

import asyncio
import shutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.config import STORAGE_DIR
from app.services.pdf_service import (
    build_export_pdf,
    image_to_page,
    make_thumbnail,
    pdf_to_pages,
)
from app.services.vlm_service import process_image, translate_text

router = APIRouter(prefix="/api/documents", tags=["documents"])

executor = ThreadPoolExecutor(max_workers=4)

# In-memory document store
documents: dict[str, dict] = {}


# ═══════ Upload ═══════

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF or image. Returns document info with page metadata."""
    doc_id = str(uuid.uuid4())[:8]
    content = await file.read()
    filename = file.filename or ""
    doc_dir = STORAGE_DIR / doc_id
    doc_dir.mkdir(exist_ok=True)

    loop = asyncio.get_event_loop()

    if filename.lower().endswith(".pdf") or file.content_type == "application/pdf":
        pages = await loop.run_in_executor(executor, pdf_to_pages, content, doc_dir)
    elif file.content_type and file.content_type.startswith("image/"):
        page = await loop.run_in_executor(executor, image_to_page, content, doc_dir, 0)
        pages = [page]
    else:
        raise HTTPException(400, "Unsupported file type. Use PDF or image.")

    documents[doc_id] = {
        "filename": filename,
        "pages": pages,
        "created": time.time(),
    }

    return {
        "doc_id": doc_id,
        "filename": filename,
        "num_pages": len(pages),
        "pages": [
            {
                "index": p["index"],
                "width": p["width"],
                "height": p["height"],
                "has_text_layer": p["has_text_layer"],
                "ocr_text": p["ocr_text"],
                "lines": p["ocr_result"]["lines"] if p["ocr_result"] else [],
            }
            for p in pages
        ],
    }


# ═══════ Page Images ═══════

@router.get("/{doc_id}/pages/{page_index}/image")
async def get_page_image(doc_id: str, page_index: int):
    page = _get_page(doc_id, page_index)
    with open(page["image_path"], "rb") as f:
        return Response(content=f.read(), media_type="image/png")


@router.get("/{doc_id}/pages/{page_index}/thumbnail")
async def get_page_thumbnail(doc_id: str, page_index: int):
    page = _get_page(doc_id, page_index)
    data = await asyncio.get_event_loop().run_in_executor(
        executor, make_thumbnail, page["image_path"]
    )
    return Response(content=data, media_type="image/png")


# ═══════ OCR (VLM) ═══════

@router.post("/{doc_id}/ocr/{page_index}")
async def ocr_page(doc_id: str, page_index: int):
    """Run VLM OCR on a single page. Skips pages that already have a text layer."""
    page = _get_page(doc_id, page_index)

    if page["has_text_layer"] and page["ocr_result"]:
        return {
            "page_index": page_index,
            "text": page["ocr_text"],
            "lines": page["ocr_result"]["lines"],
            "num_lines": len(page["ocr_result"]["lines"]),
            "source": "text_layer",
        }

    try:
        result = await process_image(page["image_path"])
    except Exception as e:
        raise HTTPException(502, f"VLM OCR error: {str(e)}")

    page["ocr_result"] = result
    page["ocr_text"] = result["text"]

    return {
        "page_index": page_index,
        "text": result["text"],
        "lines": result["lines"],
        "num_lines": len(result["lines"]),
        "source": "vlm",
    }


@router.post("/{doc_id}/ocr-all")
async def ocr_all_pages(doc_id: str):
    """Run VLM OCR on all pages that don't have text layers."""
    doc = _get_doc(doc_id)
    results = []

    for page in doc["pages"]:
        if page["has_text_layer"] and page["ocr_result"]:
            results.append({
                "page_index": page["index"],
                "text": page["ocr_text"],
                "num_lines": len(page["ocr_result"]["lines"]),
                "lines": page["ocr_result"]["lines"],
                "source": "text_layer",
            })
            continue

        try:
            result = await process_image(page["image_path"])
            page["ocr_result"] = result
            page["ocr_text"] = result["text"]
            results.append({
                "page_index": page["index"],
                "text": result["text"],
                "num_lines": len(result["lines"]),
                "lines": result["lines"],
                "source": "vlm",
            })
        except Exception as e:
            results.append({
                "page_index": page["index"],
                "text": "",
                "num_lines": 0,
                "lines": [],
                "source": "error",
                "error": str(e),
            })

    return {"doc_id": doc_id, "pages": results}


# ═══════ Translation ═══════

@router.post("/{doc_id}/translate/{page_index}")
async def translate_page(
    doc_id: str,
    page_index: int,
    target_lang: str = Form("English"),
):
    """Translate OCR text of a single page."""
    page = _get_page(doc_id, page_index)

    text = page.get("ocr_text", "")
    if not text.strip():
        raise HTTPException(400, "No OCR text to translate. Run OCR first.")

    try:
        translated = await translate_text(text, target_lang)
    except Exception as e:
        raise HTTPException(502, f"Translation error: {str(e)}")

    page["translated_text"] = translated

    return {
        "page_index": page_index,
        "translated_text": translated,
    }


# ═══════ Manual Text Updates ═══════

@router.post("/{doc_id}/pages/{page_index}/set-ocr-text")
async def set_ocr_text(doc_id: str, page_index: int, text: str = Form(...)):
    page = _get_page(doc_id, page_index)
    page["ocr_text"] = text
    return {"ok": True}


@router.post("/{doc_id}/pages/{page_index}/set-translation")
async def set_translation(doc_id: str, page_index: int, text: str = Form(...)):
    page = _get_page(doc_id, page_index)
    page["translated_text"] = text
    return {"ok": True}


# ═══════ Export ═══════

@router.post("/{doc_id}/export")
async def export_pdf(
    doc_id: str,
    overlay_mode: str = Form("invisible"),
    export_source: str = Form("ocr"),
):
    doc = _get_doc(doc_id)
    try:
        pdf_bytes = await asyncio.get_event_loop().run_in_executor(
            executor, build_export_pdf, doc, overlay_mode, export_source
        )
    except Exception as e:
        raise HTTPException(500, f"Export error: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="translated_{doc_id}.pdf"'
        },
    )


# ═══════ Cleanup ═══════

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    doc = documents.pop(doc_id, None)
    if not doc:
        raise HTTPException(404, "Document not found")
    doc_dir = STORAGE_DIR / doc_id
    if doc_dir.exists():
        shutil.rmtree(doc_dir)
    return {"ok": True}


# ═══════ Helpers ═══════

def _get_doc(doc_id: str) -> dict:
    doc = documents.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


def _get_page(doc_id: str, page_index: int) -> dict:
    doc = _get_doc(doc_id)
    if page_index < 0 or page_index >= len(doc["pages"]):
        raise HTTPException(404, "Page not found")
    return doc["pages"][page_index]
