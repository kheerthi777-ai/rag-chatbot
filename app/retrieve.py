"""Search the local card file. Does not write cards."""

from __future__ import annotations

from ingest.embed import embed_query
from ingest.store import IndexUnavailable, query

DISTANCE_CUTOFF = 0.45
TOP_K = 4


def retrieve(question: str, scheme_id: str | None) -> list[dict]:
    vector = embed_query(question)
    hits = query(vector, scheme_id, k=TOP_K) if scheme_id else []
    if scheme_id and not hits:
        hits = query(vector, None, k=TOP_K)
    if not scheme_id:
        hits = query(vector, None, k=TOP_K)
    if not hits or hits[0]["distance"] > DISTANCE_CUTOFF:
        return []
    return hits


__all__ = ["retrieve", "IndexUnavailable", "DISTANCE_CUTOFF"]
