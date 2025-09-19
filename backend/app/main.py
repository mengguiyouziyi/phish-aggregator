from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routers.sources import router as sources_router
from .routers.scan import router as scan_router
from .routers.evaluate import router as eval_router
from .routers.datasets import router as datasets_router

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="phish-aggregator", version="0.1.0")

app.include_router(sources_router)
app.include_router(scan_router)
app.include_router(eval_router)
app.include_router(datasets_router)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))
