"""
Quick test script to check if your VLM can return bounding boxes.
Usage:
    python test_vlm_bbox.py <image_path> [endpoint] [model]

Example:
    python test_vlm_bbox.py test.png http://localhost:8000/v1/chat/completions glm-ocr
"""

import base64
import json
import re
import sys

import httpx

IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else "test.png"
ENDPOINT = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000/v1/chat/completions"
MODEL = sys.argv[3] if len(sys.argv) > 3 else "glm-ocr"

PROMPT = """请识别图片中所有文字区块，返回JSON数组格式：
[{"text": "识别的文字", "bbox": [x0, y0, x1, y1]}, ...]
坐标为像素值，(x0,y0)左上角，(x1,y1)右下角。
只返回JSON，不要其他内容。"""

print(f"Image:    {IMAGE_PATH}")
print(f"Endpoint: {ENDPOINT}")
print(f"Model:    {MODEL}")
print("-" * 50)

with open(IMAGE_PATH, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

resp = httpx.post(
    ENDPOINT,
    json={
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
    },
    timeout=120,
)

print(f"Status: {resp.status_code}")

if resp.status_code != 200:
    print(f"Error: {resp.text}")
    sys.exit(1)

raw = resp.json()["choices"][0]["message"]["content"]
print(f"\n--- Raw Response ---\n{raw}\n")

# Try to parse JSON
text = raw.strip()
blocks = None

for attempt in [
    lambda: json.loads(text),
    lambda: json.loads(re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL).group(1)),
    lambda: json.loads(re.search(r"\[.*\]", text, re.DOTALL).group(0)),
]:
    try:
        blocks = attempt()
        if isinstance(blocks, list):
            break
        blocks = None
    except Exception:
        blocks = None

if blocks:
    print(f"--- Parsed {len(blocks)} text blocks ---")
    for b in blocks:
        bbox = b.get("bbox", "?")
        text = b.get("text", "")[:40]
        print(f"  bbox={bbox}  text={text}")
    print("\n[OK] Model supports bbox output. Use VLM_COMBINED_MODE=true")
else:
    print("[FAIL] Could not parse JSON with bbox.")
    print("Options:")
    print("  1. Try a different prompt (edit VLM_COMBINED_PROMPT in .env)")
    print("  2. Try your larger VLM model")
    print("  3. Use VLM_COMBINED_MODE=false (separate detection + OCR calls)")
