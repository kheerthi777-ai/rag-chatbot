"""Answer from retrieved cards. A chat model is optional."""

from __future__ import annotations

import os
import re
from pathlib import Path

FACT_WORDS = ("expense", "exit", "sip", "lock", "risk", "benchmark", "tax", "statement", "load")
ROOT = Path(__file__).resolve().parents[1]


def generate(question: str, hits: list[dict]) -> str:
    if not hits:
        return "NOT_FOUND"
    backend = os.environ.get("LLM_BACKEND", "").strip()
    if backend:
        return _llm(question, hits, backend)
    return _extract(question, hits)


def _extract(question: str, hits: list[dict]) -> str:
    wanted = [word for word in FACT_WORDS if word in question.lower()]
    facts: list[str] = []
    scheme_id = None
    for hit in hits:
        body = _body(hit)
        if wanted and not any(word in body.lower() for word in wanted):
            continue
        if scheme_id is None:
            scheme_id = hit.get("scheme_id")
        elif hit.get("scheme_id") != scheme_id:
            continue
        fact = _fact_sentences(hit.get("scheme_name") or "", body)
        if fact and fact not in facts:
            facts.append(fact)
        if len(facts) == 2:
            break
    if not facts:
        return "NOT_FOUND"
    text = " ".join(facts)
    overview = _overview(scheme_id, hits)
    if overview and overview not in text:
        text = f"{text} {overview}"
    return _sentences(text, 3)


def _llm(question: str, hits: list[dict], backend: str) -> str:
    raise RuntimeError(f"LLM backend {backend} is not configured")


def _body(hit: dict) -> str:
    document = hit.get("document") or ""
    marker = "Source: "
    if marker in document:
        rest = document.split(marker, 1)[1]
        if "\n" in rest:
            return rest.split("\n", 1)[1].strip()
    return document.strip()


def _fact_sentences(name: str, body: str) -> str:
    text = " ".join(body.split())
    expense = re.search(r"Expense ratio:\s*([0-9.]+%)", text, re.IGNORECASE)
    base = re.search(r"Base expense ratio:\s*([0-9.]+%)", text, re.IGNORECASE)
    if expense:
        sentence = f"The expense ratio of {name} is {expense.group(1)}"
        if base:
            sentence += f", and the base expense ratio is {base.group(1)}"
        return sentence + "."
    sip = re.search(r"Minimum SIP:\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    lump = re.search(r"Minimum lump-sum investment:\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if sip:
        sentence = f"The minimum SIP for {name} is {sip.group(1)}"
        if lump:
            sentence += f", and the minimum lump-sum investment is {lump.group(1)}"
        return sentence + "."
    lock = re.search(r"Lock-in:\s*(.+?)\.", text, re.IGNORECASE)
    if lock:
        value = lock.group(1).strip()
        if value.lower().startswith("no lock-in"):
            return f"No lock-in is stated on the page for {name}."
        return f"The lock-in period for {name} is {value}."
    risk = re.search(r"Riskometer:\s*(.+?)\.", text, re.IGNORECASE)
    if risk:
        return f"The riskometer for {name} is {risk.group(1).strip()}."
    benchmark = re.search(r"Benchmark:\s*(.+?)\.", text, re.IGNORECASE)
    if benchmark:
        return f"The benchmark for {name} is {benchmark.group(1).strip()}."
    exit_of = re.search(r"Exit load of\s+(.+?)\.", text, re.IGNORECASE)
    if exit_of:
        return f"The exit load of {name} is {exit_of.group(1).strip()}."
    exit_label = re.search(r"Exit load:\s*(.+?)\.", text, re.IGNORECASE)
    if exit_label:
        return f"The exit load of {name} is {exit_label.group(1).strip()}."
    if text.lower().startswith("tax:"):
        detail = text[4:].strip()
        if name and name not in detail:
            return f"For {name}, {detail[0].lower()}{detail[1:]}"
        return detail
    if name and name not in text:
        return f"{name}. {text}"
    return text


def _overview(scheme_id: str | None, hits: list[dict]) -> str:
    for hit in hits:
        if hit.get("section") != "Overview":
            continue
        if scheme_id and hit.get("scheme_id") not in (None, scheme_id):
            continue
        text = _sentences(_body(hit), 1)
        if text:
            return text
    if not scheme_id:
        return ""
    path = ROOT / "data" / "raw" / f"{scheme_id}.md"
    if not path.exists():
        return ""
    match = re.search(r"^## Overview\s*\n(.+?)(?:\n## |\Z)", path.read_text(encoding="utf-8"), re.S | re.M)
    if not match:
        return ""
    return _sentences(match.group(1).strip(), 1)


def _sentences(text: str, limit: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [part.strip() for part in parts if part.strip()]
    return " ".join(kept[:limit])
