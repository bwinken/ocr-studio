import asyncio
import logging
import shutil
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import STATIC_DIR, STORAGE_DIR, STORAGE_TTL_MINUTES, TEMPLATES_DIR
from app.routers import documents, translate

logger = logging.getLogger(__name__)


async def _cleanup_loop():
    """Periodically remove expired documents from memory and disk."""
    ttl_seconds = STORAGE_TTL_MINUTES * 60
    while True:
        await asyncio.sleep(60)  # check every minute
        now = time.time()
        expired = [
            doc_id
            for doc_id, doc in list(documents.documents.items())
            if now - doc["created"] > ttl_seconds
        ]
        for doc_id in expired:
            documents.documents.pop(doc_id, None)
            doc_dir = STORAGE_DIR / doc_id
            if doc_dir.exists():
                shutil.rmtree(doc_dir)
            logger.info("Cleaned up expired document %s", doc_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    STORAGE_DIR.mkdir(exist_ok=True)
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


load_dotenv()

app = FastAPI(
    title="Image Doc Translator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(documents.router)
app.include_router(translate.router)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")
