"""Persistent Chroma collection for scheme cards."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from ingest.chunk import Chunk

ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = ROOT / "data" / "chroma"
COLLECTION = "hdfc_schemes"


class IndexUnavailable(Exception):
    """The local card file is missing or empty."""


def chroma_client():
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(create: bool = False):
    client = chroma_client()
    if create:
        return client.get_or_create_collection(name=COLLECTION, metadata={"hnsw:space": "cosine"})
    try:
        collection = client.get_collection(name=COLLECTION)
    except Exception as exc:
        raise IndexUnavailable("missing collection") from exc
    if collection.count() == 0:
        raise IndexUnavailable("empty collection")
    return collection


def replace_scheme(chunks: list[Chunk], vectors: list[list[float]]) -> None:
    if not chunks:
        return
    collection = get_collection(create=True)
    scheme_ids = sorted({card.scheme_id for card in chunks})
    for scheme_id in scheme_ids:
        existing = collection.get(where={"scheme_id": scheme_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    collection.upsert(
        ids=[card.id for card in chunks],
        documents=[card.document for card in chunks],
        embeddings=vectors,
        metadatas=[
            {
                "scheme_id": card.scheme_id,
                "scheme_name": card.scheme_name,
                "category": card.category,
                "source_url": card.source_url,
                "fetched_at": card.fetched_at,
                "section": card.section,
            }
            for card in chunks
        ],
    )


def query(vector: list[float], scheme_id: str | None, k: int = 4) -> list[dict]:
    collection = get_collection(create=False)
    where = {"scheme_id": scheme_id} if scheme_id else None
    result = collection.query(query_embeddings=[vector], n_results=k, where=where)
    return _hits(result)


def _hits(result: dict) -> list[dict]:
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    hits = []
    for card_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        meta = metadata or {}
        hits.append(
            {
                "id": card_id,
                "document": document,
                "scheme_id": meta.get("scheme_id"),
                "scheme_name": meta.get("scheme_name"),
                "category": meta.get("category"),
                "source_url": meta.get("source_url"),
                "fetched_at": meta.get("fetched_at"),
                "section": meta.get("section"),
                "distance": distance,
            }
        )
    return hits
