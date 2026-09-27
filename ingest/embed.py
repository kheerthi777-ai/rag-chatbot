"""Shared MiniLM encoder. Documents are embedded at ingest; questions at ask time."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "fastembed"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def _encoder():
    global _model
    if _model is None:
        os.environ.setdefault("FASTEMBED_CACHE_PATH", str(CACHE))
        from fastembed import TextEmbedding

        _model = TextEmbedding(model_name=MODEL)
    return _model


def embed_documents(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _encoder().embed(texts)
    return [vector.tolist() for vector in vectors]


def embed_query(text: str) -> list[float]:
    vector = next(_encoder().embed([text]))
    return vector.tolist()
