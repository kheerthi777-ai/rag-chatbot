"""Load, chunk, embed, and store the five scheme pages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ingest.catalog import SCHEMES
from ingest.chunk import chunk
from ingest.embed import embed_documents
from ingest.load import LoadError, RawPage, load
from ingest.store import replace_scheme

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "Docs" / "sources.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index the five HDFC scheme pages.")
    parser.add_argument("--refresh", action="store_true", help="Refetch pages before indexing.")
    args = parser.parse_args(argv)

    pages: list[RawPage] = []
    cards = []
    for scheme in SCHEMES:
        try:
            page = load(scheme, refresh=args.refresh)
        except LoadError:
            print(scheme.source_url)
            continue
        scheme_cards = chunk(page)
        print(f"{scheme.scheme_id} {len(scheme_cards)}")
        pages.append(page)
        cards.extend(scheme_cards)

    if cards:
        vectors = embed_documents([card.document for card in cards])
        replace_scheme(cards, vectors)
    _write_sources(pages)
    return 0


def _write_sources(pages: list[RawPage]) -> None:
    lines = [
        "# Sources",
        "",
        "| Scheme | Category | URL | Fetched |",
        "|---|---|---|---|",
    ]
    for page in pages:
        lines.append(
            f"| {page.scheme_name} | {page.category} | {page.source_url} | {page.fetched_at} |"
        )
    SOURCES.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
