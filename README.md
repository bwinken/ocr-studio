# Image Doc Translator

OCR studio for scanned PDFs with translation and searchable PDF export. All AI inference runs via external VLM/LLM APIs (vLLM) — zero local ML dependencies.

## Architecture

```
Browser  ──→  FastAPI  ──→  vLLM (GLM-OCR)     # bbox + text detection
                       ──→  vLLM (gptoss-20b)   # translation
                       ──→  PyMuPDF              # PDF parse / export
```

### Processing Flow

```
Upload PDF/Image
  │
  ├─ PDF with text layer  →  PyMuPDF extracts text + bbox directly (no VLM call)
  │
  └─ Scanned PDF / Image  →  VLM combined mode: one call returns text + bbox
                              or two-pass: VLM_DET → bbox, VLM_OCR → text
                                │
                                ↓
                           Translate → VLM_TRANSLATE → translated text
                                │
                                ↓
                           Export PDF → original image + text overlay at bbox positions
```

## Tech Stack

- **Backend**: Python FastAPI + Jinja2 templates
- **PDF**: PyMuPDF (parsing, rendering, export)
- **OCR**: VLM via vLLM (GLM-OCR or any OpenAI-compatible vision model)
- **Translation**: LLM via vLLM (gptoss-20b or any OpenAI-compatible model)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)

## Setup (Development)

```bash
# 1. Install
uv sync

# 2. Configure
cp .env.example .env
# Edit .env with your vLLM endpoints

# 3. Test VLM bbox support
python test_vlm_bbox.py test.png http://localhost:8000/v1/chat/completions glm-ocr

# 4. Run
make dev
# or: uv run uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080

## Configuration

All VLM/LLM settings via environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `VLM_DET_ENDPOINT` | Text detection (bbox) API | `http://localhost:8000/v1/chat/completions` |
| `VLM_DET_MODEL` | Detection model name | `glm-ocr` |
| `VLM_OCR_ENDPOINT` | OCR recognition API | `http://localhost:8000/v1/chat/completions` |
| `VLM_OCR_MODEL` | OCR model name | `glm-ocr` |
| `VLM_COMBINED_MODE` | Single call for bbox+text | `true` |
| `VLM_TRANSLATE_ENDPOINT` | Translation API | `http://localhost:8000/v1/chat/completions` |
| `VLM_TRANSLATE_MODEL` | Translation model name | `gptoss-20b` |

All prompts are also configurable via `VLM_DET_PROMPT`, `VLM_OCR_PROMPT`, `VLM_COMBINED_PROMPT`, `VLM_TRANSLATE_PROMPT`.

## Deployment

Deploy to `$HOME/opt/image-doc-translator` with systemd user service:

```bash
# First-time install: copy files, create venv, install service
make install

# Edit config on server
vim ~/opt/image-doc-translator/.env

# Start
make start

# After code changes: rsync + restart
make sync

# Other commands
make status    # check service
make logs      # tail logs
make stop      # stop service
make restart   # restart service
make uninstall # remove service
```

The deploy script (`deploy/deploy.sh`) does:
1. `rsync` project to `$HOME/opt/image-doc-translator/` (excludes `.venv`, `.env`, `storage/`)
2. `uv pip install -e .` in the deploy directory
3. Installs/reloads a `systemd --user` service
4. `.env` is preserved across syncs (never overwritten)

### Port & Workers

```bash
IDT_PORT=8080 IDT_WORKERS=2 make install
```

## Project Structure

```
├── pyproject.toml          # Dependencies
├── .env.example            # Environment variable template
├── Makefile                # Dev & deploy shortcuts
├── test_vlm_bbox.py        # Test VLM bbox capability
├── deploy/
│   └── deploy.sh           # Deployment script (rsync + systemd)
├── app/
│   ├── main.py             # FastAPI entry point
│   ├── config.py           # All config from env vars
│   ├── routers/
│   │   ├── documents.py    # Upload, OCR, export API
│   │   └── translate.py    # Translation API
│   ├── services/
│   │   ├── vlm_service.py  # VLM/LLM API client (detect, OCR, translate)
│   │   └── pdf_service.py  # PyMuPDF PDF parse & export
│   ├── templates/
│   │   └── index.html      # Frontend SPA
│   ├── static/
│   └── storage/            # Temp uploaded files (gitignored)
```
