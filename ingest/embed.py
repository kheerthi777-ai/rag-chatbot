"""Shared MiniLM encoder. Documents are embedded at ingest; questions at ask time."""

from __future__ import annotations

_model = None


def _encoder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def embed_documents(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _encoder().encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


def embed_query(text: str) -> list[float]:
    vector = _encoder().encode([text], normalize_embeddings=True)[0]
    return vector.tolist()
