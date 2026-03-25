"""
VLM API client - handles all calls to vision/language models.
Supports detection, OCR, combined mode, and translation.
"""

import base64
import json
import re

import httpx

from app import config


async def _call_vlm(
    endpoint: str,
    model: str,
    api_key: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    image_b64: str | None = None,
) -> str:
    """Send a request to an OpenAI-compatible VLM endpoint."""
    content = []
    content.append({"type": "text", "text": prompt})

    if image_b64:
        # Ensure proper data URI prefix
        if not image_b64.startswith("data:"):
            image_b64 = f"data:image/png;base64,{image_b64}"
        content.append({"type": "image_url", "image_url": {"url": image_b64}})

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_llm(
    endpoint: str,
    model: str,
    api_key: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """Send a text-only request to an OpenAI-compatible LLM endpoint."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _parse_json_response(text: str) -> list[dict]:
    """Try to extract a JSON array from VLM response (handles markdown fences, etc)."""
    text = text.strip()

    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(1).strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Try finding first [ ... ] in text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def _image_to_b64(image_path: str) -> str:
    """Read an image file and return base64 data URI."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"


# ═══════════════════ PUBLIC API ═══════════════════


async def detect_text_blocks(image_path: str) -> list[dict]:
    """
    Detect text block bounding boxes in an image.
    Returns: [{"bbox": [x0, y0, x1, y1], "label": "text"}, ...]
    """
    image_b64 = _image_to_b64(image_path)
    raw = await _call_vlm(
        endpoint=config.VLM_DET_ENDPOINT,
        model=config.VLM_DET_MODEL,
        api_key=config.VLM_DET_API_KEY,
        prompt=config.VLM_DET_PROMPT,
        max_tokens=config.VLM_DET_MAX_TOKENS,
        temperature=config.VLM_DET_TEMPERATURE,
        image_b64=image_b64,
    )
    blocks = _parse_json_response(raw)

    # Normalize: ensure each block has "bbox" as list of 4 numbers
    result = []
    for b in blocks:
        bbox = b.get("bbox")
        if bbox and len(bbox) == 4:
            result.append({
                "bbox": {"x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3]},
                "label": b.get("label", "text"),
            })
    return result


async def ocr_image(image_path: str) -> str:
    """
    Run OCR on full image, returns plain text.
    """
    image_b64 = _image_to_b64(image_path)
    return await _call_vlm(
        endpoint=config.VLM_OCR_ENDPOINT,
        model=config.VLM_OCR_MODEL,
        api_key=config.VLM_OCR_API_KEY,
        prompt=config.VLM_OCR_PROMPT,
        max_tokens=config.VLM_OCR_MAX_TOKENS,
        temperature=config.VLM_OCR_TEMPERATURE,
        image_b64=image_b64,
    )


async def detect_and_ocr(image_path: str) -> dict:
    """
    Combined mode: detect text blocks AND recognize text in one VLM call.
    Returns: {"lines": [{"text": ..., "bbox": {x0,y0,x1,y1}}, ...], "text": "full text"}
    """
    image_b64 = _image_to_b64(image_path)
    raw = await _call_vlm(
        endpoint=config.VLM_OCR_ENDPOINT,
        model=config.VLM_OCR_MODEL,
        api_key=config.VLM_OCR_API_KEY,
        prompt=config.VLM_COMBINED_PROMPT,
        max_tokens=config.VLM_OCR_MAX_TOKENS,
        temperature=config.VLM_OCR_TEMPERATURE,
        image_b64=image_b64,
    )
    blocks = _parse_json_response(raw)

    lines = []
    text_parts = []
    for b in blocks:
        text = b.get("text", "")
        bbox = b.get("bbox")
        if bbox and len(bbox) == 4 and text:
            lines.append({
                "text": text,
                "bbox": {"x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3]},
            })
            text_parts.append(text)

    return {
        "lines": lines,
        "text": "\n".join(text_parts),
        "raw_response": raw,
    }


async def detect_then_ocr(image_path: str) -> dict:
    """
    Two-pass mode: first detect bboxes, then OCR full image, match by line order.
    Use when model can't reliably return both bbox + text in one call.
    """
    # Step 1: detect bboxes
    blocks = await detect_text_blocks(image_path)

    # Step 2: OCR full text
    full_text = await ocr_image(image_path)

    # Step 3: match - simple line-order matching
    text_lines = [l.strip() for l in full_text.strip().split("\n") if l.strip()]

    lines = []
    for i, block in enumerate(blocks):
        text = text_lines[i] if i < len(text_lines) else ""
        lines.append({
            "text": text,
            "bbox": block["bbox"],
        })

    # Append any unmatched OCR lines
    if len(text_lines) > len(blocks):
        for extra in text_lines[len(blocks):]:
            lines.append({
                "text": extra,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            })

    return {
        "lines": lines,
        "text": full_text,
    }


async def process_image(image_path: str) -> dict:
    """
    Main entry point: process an image using the configured mode.
    Returns: {"lines": [...], "text": "..."}
    """
    if config.VLM_COMBINED_MODE:
        return await detect_and_ocr(image_path)
    else:
        return await detect_then_ocr(image_path)


async def translate_text(
    text: str,
    target_lang: str,
    endpoint: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    system_prompt: str | None = None,
) -> str:
    """Translate text using configured LLM."""
    user_msg = f"Translate the following text to {target_lang}. Output ONLY the translated text:\n\n{text}"

    return await _call_llm(
        endpoint=endpoint or config.VLM_TRANSLATE_ENDPOINT,
        model=model or config.VLM_TRANSLATE_MODEL,
        api_key=api_key or config.VLM_TRANSLATE_API_KEY,
        system_prompt=system_prompt or config.VLM_TRANSLATE_PROMPT,
        user_message=user_msg,
        max_tokens=config.VLM_TRANSLATE_MAX_TOKENS,
        temperature=config.VLM_TRANSLATE_TEMPERATURE,
    )
