"""One-page facts desk."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.ask import GENERATE_MESSAGE, INDEX_MESSAGE, ask
from ingest.catalog import SCHEMES
from ingest.store import IndexUnavailable, get_collection

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="HDFC scheme facts")


class Question(BaseModel):
    question: str = ""


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/status")
def status():
    chunks = 0
    ready = False
    try:
        chunks = get_collection().count()
        ready = chunks > 0
    except IndexUnavailable:
        ready = False
    chroma_version = ""
    try:
        import chromadb

        chroma_version = chromadb.__version__
    except Exception:
        chroma_version = ""
    raw_dir = STATIC.parents[1] / "data" / "raw"
    synced = ""
    if raw_dir.exists():
        stamps = [path.stat().st_mtime for path in raw_dir.glob("hdfc-*.md")]
        if stamps:
            from datetime import datetime

            synced = datetime.fromtimestamp(max(stamps)).date().isoformat()
    return {
        "ready": ready,
        "chunks": chunks,
        "chroma_version": chroma_version,
        "synced": synced,
        "embedding_model": "all-MiniLM-L6-v2",
        "schemes": [
            {"scheme_id": scheme.scheme_id, "scheme_name": scheme.scheme_name, "category": scheme.category, "source_url": scheme.source_url}
            for scheme in SCHEMES
        ],
    }


@app.post("/ask")
def post_ask(body: Question):
    result = ask(body.question)
    status = 200
    if result["kind"] == "error":
        if result["text"] == INDEX_MESSAGE:
            status = 503
        elif result["text"] == GENERATE_MESSAGE:
            status = 502
        else:
            status = 400
    return JSONResponse(result, status_code=status)
