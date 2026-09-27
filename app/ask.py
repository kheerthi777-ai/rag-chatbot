"""Turn one question into a cited fact or a fixed refusal."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.citation import cite, load_refusals
from app.generate import generate
from app.intent import classify
from app.retrieve import retrieve
from ingest.catalog import url_for
from ingest.store import IndexUnavailable

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.log"

INDEX_MESSAGE = "The index isn’t available. Run ingest, then try again."
GENERATE_MESSAGE = "The answer service failed. Your question was not saved."
EMPTY_MESSAGE = "Ask a factual question about one of the five schemes."


def ask(question: str) -> dict:
    text = (question or "").strip()
    if not text:
        response = _error(EMPTY_MESSAGE)
        _log(response, "")
        return response

    intent = classify(text)
    refusals = load_refusals()

    if intent.kind == "pii":
        response = _with_trace(
            {
                "kind": "refused_pii",
                "text": refusals["pii"],
                "source_url": None,
                "fetched_at": None,
                "scheme_id": None,
            },
            [],
            "refused",
        )
        _log(response, "pii_blocked")
        return response

    if intent.kind == "advice":
        response = _with_trace(_refusal("refused_advice", refusals["advice"], intent.scheme_id), [], "refused")
        _log(response, text)
        return response

    if intent.kind == "returns":
        response = _with_trace(_refusal("refused_returns", refusals["returns"], intent.scheme_id), [], "refused")
        _log(response, text)
        return response

    if "hdfc" in text.lower() and intent.scheme_id is None:
        response = _with_trace(
            {
                "kind": "not_found",
                "text": refusals["not_found"],
                "source_url": None,
                "fetched_at": None,
                "scheme_id": None,
            },
            [],
            "passed",
        )
        _log(response, text)
        return response

    try:
        hits = retrieve(text, intent.scheme_id)
        drafted = generate(text, hits)
        response = _with_trace(cite(drafted, hits), hits, "passed")
    except IndexUnavailable:
        response = _with_trace(_error(INDEX_MESSAGE), [], "error")
    except Exception:
        response = _with_trace(_error(GENERATE_MESSAGE), [], "error")
    _log(response, text)
    return response


def _refusal(kind: str, template: str, scheme_id: str | None) -> dict:
    chosen = scheme_id or "hdfc-large-cap"
    return {
        "kind": kind,
        "text": template.format(url=url_for(chosen)),
        "source_url": url_for(chosen),
        "fetched_at": None,
        "scheme_id": chosen,
    }


def _with_trace(response: dict, hits: list[dict], guardrail: str) -> dict:
    top = hits[:3]
    response["trace"] = {
        "guardrail": guardrail,
        "distance": top[0].get("distance") if top else None,
        "hits": [
            {
                "id": hit.get("id"),
                "section": hit.get("section"),
                "scheme_name": hit.get("scheme_name"),
                "source_url": hit.get("source_url"),
                "distance": hit.get("distance"),
                "excerpt": " ".join((hit.get("document") or "").split())[:320],
            }
            for hit in top
        ],
    }
    return response


def _error(message: str) -> dict:
    return {
        "kind": "error",
        "text": message,
        "source_url": None,
        "fetched_at": None,
        "scheme_id": None,
    }


def _log(response: dict, question: str) -> None:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": _event_name(response["kind"]),
        "scheme_id": response.get("scheme_id"),
        "question_redacted": question if question == "pii_blocked" else _redact(question),
    }
    with EVENTS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _event_name(kind: str) -> str:
    if kind == "answer":
        return "answer_cited"
    return kind


def _redact(question: str) -> str:
    question = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", "[redacted]", question)
    question = re.sub(r"(?:\+91[\s-]?)?[6-9]\d{9}\b", "[redacted]", question)
    question = re.sub(r"\b\d{9,}\b", "[redacted]", question)
    return question
