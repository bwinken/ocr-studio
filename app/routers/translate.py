"""Standalone translation route (not tied to a document)."""

from fastapi import APIRouter, Form, HTTPException

from app.services.vlm_service import translate_text

router = APIRouter(prefix="/api", tags=["translate"])


@router.post("/translate")
async def translate(
    text: str = Form(...),
    target_lang: str = Form("English"),
):
    """Translate text using configured translation LLM."""
    if not text.strip():
        raise HTTPException(400, "Empty text")

    try:
        result = await translate_text(text, target_lang)
        return {"translated_text": result}
    except Exception as e:
        raise HTTPException(502, f"Translation error: {str(e)}")
