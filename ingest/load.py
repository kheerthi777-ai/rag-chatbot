"""Fetch the five catalog pages, or read the saved snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from ingest.catalog import SCHEMES, Scheme

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
TIMEOUT_SECONDS = 20.0

FACT_MARKERS = (
    "expense ratio",
    "exit load",
    "sip",
    "lock-in",
    "risk",
    "benchmark",
)


class LoadError(Exception):
    """The live page was empty or blocked and no snapshot exists."""


@dataclass(frozen=True)
class RawPage:
    scheme_id: str
    scheme_name: str
    category: str
    source_url: str
    fetched_at: str
    text: str


def snapshot_path(scheme: Scheme) -> Path:
    return RAW_DIR / f"{scheme.scheme_id}.md"


def load(scheme: Scheme, refresh: bool = False) -> RawPage:
    path = snapshot_path(scheme)
    if path.exists() and not refresh:
        return _from_file(scheme, path)
    try:
        text = _fetch_markdown(scheme)
    except LoadError:
        if path.exists():
            return _from_file(scheme, path)
        raise
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return _from_file(scheme, path)


def markdown_from_fields(scheme: Scheme, fields: dict) -> str:
    """Turn scheme JSON into labeled markdown. Omits returns and peer funds."""
    lines = [
        f"# {scheme.scheme_name}",
        "",
        f"Direct-Growth. Category: {scheme.category}.",
        f"Source: {scheme.source_url}",
        "",
    ]

    expense = fields.get("expense_ratio")
    if expense is not None and expense != "":
        body = f"Expense ratio: {_percent(expense)}."
        base = fields.get("base_expense_ratio")
        if base is not None and base != "":
            body += f" Base expense ratio: {_percent(base)}."
        lines.extend(["## Expense ratio", body, ""])

    exit_load = fields.get("exit_load")
    if isinstance(exit_load, str) and exit_load.strip():
        lines.extend(["## Exit load", _sentence("Exit load", exit_load), ""])

    sip = fields.get("min_sip_investment")
    if sip is not None and sip != "":
        body = f"Minimum SIP: {sip}."
        lump = fields.get("min_investment_amount")
        if lump is not None and lump != "":
            body += f" Minimum lump-sum investment: {lump}."
        lines.extend(["## Minimum SIP", body, ""])

    lock = _format_lock(fields.get("lock_in"))
    if lock is not None:
        lines.extend(["## Lock-in", f"Lock-in: {lock}.", ""])

    risk = _riskometer(fields)
    if risk:
        lines.extend(["## Riskometer", f"Riskometer: {risk}.", ""])

    benchmark = _benchmark(fields)
    if benchmark:
        lines.extend(["## Benchmark", f"Benchmark: {benchmark}.", ""])

    tax = _tax(fields)
    if tax:
        lines.extend(["## Tax", f"Tax: {tax}", ""])

    description = fields.get("description")
    if isinstance(description, str) and description.strip():
        lines.extend(["## Overview", description.strip(), ""])

    text = "\n".join(lines).strip() + "\n"
    _require_facts(scheme, text)
    return text


def _fetch_markdown(scheme: Scheme) -> str:
    try:
        response = httpx.get(
            scheme.source_url,
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
    except httpx.HTTPError as exc:
        raise LoadError(scheme.source_url) from exc
    fields = _fields_from_html(response.status_code, response.text)
    return markdown_from_fields(scheme, fields)


def _fields_from_html(status_code: int, html: str) -> dict:
    if status_code >= 400 or not html or len(html) < 500:
        raise LoadError("empty or blocked")
    lowered = html.lower()
    if "access denied" in lowered or ("cloudflare" in lowered and "just a moment" in lowered):
        raise LoadError("blocked")
    soup = BeautifulSoup(html, "html.parser")
    node = soup.find("script", id="__NEXT_DATA__")
    if node is None or not node.string:
        raise LoadError("no scheme data")
    try:
        payload = json.loads(node.string)
        fields = payload["props"]["pageProps"]["mfServerSideData"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise LoadError("no scheme data") from exc
    if not isinstance(fields, dict):
        raise LoadError("no scheme data")
    return fields


def _from_file(scheme: Scheme, path: Path) -> RawPage:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise LoadError(scheme.source_url)
    fetched_at = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    return RawPage(
        scheme_id=scheme.scheme_id,
        scheme_name=scheme.scheme_name,
        category=scheme.category,
        source_url=scheme.source_url,
        fetched_at=fetched_at,
        text=text,
    )


def _require_facts(scheme: Scheme, text: str) -> None:
    title = text.splitlines()[0] if text else ""
    if scheme.scheme_name not in title:
        raise LoadError(scheme.source_url)
    lowered = text.lower()
    if not any(marker in lowered for marker in FACT_MARKERS):
        raise LoadError(scheme.source_url)


def _percent(value: object) -> str:
    text = str(value).strip()
    if text.endswith("%"):
        return text
    return f"{text}%"


def _sentence(label: str, value: str) -> str:
    text = value.strip()
    if not text.lower().startswith(label.lower()):
        text = f"{label}: {text}"
    if not text.endswith("."):
        text += "."
    return text


def _format_lock(lock: object) -> str | None:
    if not isinstance(lock, dict):
        return None
    parts: list[str] = []
    for unit in ("years", "months", "days"):
        count = lock.get(unit)
        if isinstance(count, int) and count > 0:
            name = unit[:-1] if count == 1 else unit
            parts.append(f"{count} {name}")
    if not parts:
        return "No lock-in is stated on this page"
    return " ".join(parts)


def _riskometer(fields: dict) -> str | None:
    stats = fields.get("return_stats")
    if isinstance(stats, list) and stats and isinstance(stats[0], dict):
        risk = stats[0].get("risk")
        if isinstance(risk, str) and risk.strip():
            return risk.strip()
    nfo = fields.get("nfo_risk")
    if isinstance(nfo, str) and nfo.strip():
        return nfo.replace("Riskometer", "").strip(" -")
    return None


def _benchmark(fields: dict) -> str | None:
    name = fields.get("benchmark_name")
    code = fields.get("benchmark")
    name = name.strip() if isinstance(name, str) else ""
    code = code.strip() if isinstance(code, str) else ""
    if name and code and code not in name:
        return f"{name} ({code})"
    return name or code or None


def _tax(fields: dict) -> str | None:
    info = fields.get("category_info")
    if not isinstance(info, dict):
        return None
    tax = info.get("tax_impact")
    if isinstance(tax, str) and tax.strip():
        text = tax.strip()
        if not text.endswith("."):
            text += "."
        return text
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Save cleaned scheme snapshots.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refetch catalog pages even when a snapshot exists.",
    )
    args = parser.parse_args(argv)
    for scheme in SCHEMES:
        try:
            page = load(scheme, refresh=args.refresh)
        except LoadError:
            print(scheme.source_url)
            continue
        print(f"{page.scheme_id} {page.fetched_at}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
