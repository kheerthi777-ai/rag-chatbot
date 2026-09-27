"""Attach one catalog link, or refuse to invent one."""

from __future__ import annotations

import re
from pathlib import Path

from ingest.catalog import is_catalog_url

ROOT = Path(__file__).resolve().parents[1]
REFUSALS = ROOT / "prompts" / "refusals.txt"


def load_refusals() -> dict[str, str]:
    texts: dict[str, str] = {}
    key = None
    lines: list[str] = []
    for raw in REFUSALS.read_text(encoding="utf-8").splitlines():
        if raw.endswith(":") and raw[:-1].isidentifier():
            if key:
                texts[key] = "\n".join(lines).strip()
            key = raw[:-1]
            lines = []
        else:
            lines.append(raw)
    if key:
        texts[key] = "\n".join(lines).strip()
    return texts


def cite(answer: str, hits: list[dict]) -> dict:
    refusals = load_refusals()
    cleaned = answer.strip()
    if not hits or cleaned == "NOT_FOUND" or not cleaned:
        return {
            "kind": "not_found",
            "text": refusals["not_found"],
            "source_url": None,
            "fetched_at": None,
            "scheme_id": None,
        }
    hit = _supporting_hit(cleaned, hits)
    url = hit.get("source_url")
    retrieved_urls = {item.get("source_url") for item in hits}
    if not url or url not in retrieved_urls or not is_catalog_url(url):
        return {
            "kind": "not_found",
            "text": refusals["not_found"],
            "source_url": None,
            "fetched_at": None,
            "scheme_id": None,
        }
    return {
        "kind": "answer",
        "text": _three_sentences(cleaned),
        "source_url": url,
        "fetched_at": hit.get("fetched_at"),
        "scheme_id": hit.get("scheme_id"),
    }


def _supporting_hit(answer: str, hits: list[dict]) -> dict:
    lowered = answer.lower()
    for hit in hits:
        name = (hit.get("scheme_name") or "").lower()
        if name and name in lowered:
            return hit
    return hits[0]


def _three_sentences(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [part for part in parts if part]
    return " ".join(kept[:3])
