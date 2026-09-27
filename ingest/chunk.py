"""Split a scheme snapshot into short labeled cards."""

from __future__ import annotations

import re
import sys

from ingest.catalog import SCHEMES
from ingest.load import LoadError, RawPage, load

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
SEPARATORS = ("\n## ", "\n# ", "\n\n", "\n", ". ", " ")


class Chunk:
    def __init__(
        self,
        id: str,
        document: str,
        scheme_id: str,
        scheme_name: str,
        category: str,
        source_url: str,
        fetched_at: str,
        section: str,
    ) -> None:
        self.id = id
        self.document = document
        self.scheme_id = scheme_id
        self.scheme_name = scheme_name
        self.category = category
        self.source_url = source_url
        self.fetched_at = fetched_at
        self.section = section

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "document": self.document,
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "category": self.category,
            "source_url": self.source_url,
            "fetched_at": self.fetched_at,
            "section": self.section,
        }


def chunk(page: RawPage) -> list[Chunk]:
    prefix = f"# {page.scheme_name} ({page.category})\nSource: {page.source_url}\n"
    cards: list[Chunk] = []
    for section, body in _sections(page.text):
        pieces = _split_body(body)
        slug = _slug(section)
        for index, piece in enumerate(pieces):
            if not piece.strip():
                continue
            cards.append(
                Chunk(
                    id=f"{page.scheme_id}:{slug}:{index}",
                    document=prefix + piece,
                    scheme_id=page.scheme_id,
                    scheme_name=page.scheme_name,
                    category=page.category,
                    source_url=page.source_url,
                    fetched_at=page.fetched_at,
                    section=section,
                )
            )
    return cards


def _sections(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"\n(?=## )", text.strip())
    sections: list[tuple[str, str]] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith("## "):
            heading, _, body = part.partition("\n")
            name = heading[3:].strip() or "body"
            body = body.strip()
        else:
            lines = part.splitlines()
            body = "\n".join(lines[1:]).strip() if lines and lines[0].startswith("# ") else part
            name = "body"
        if body:
            sections.append((name, body))
    return sections


def _split_body(body: str) -> list[str]:
    body = body.strip()
    if len(body) <= CHUNK_SIZE:
        return [body]
    return _windows(body)


def _windows(text: str) -> list[str]:
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            end = start + _cut(text[start:end])
        piece = text[start:end]
        if piece.strip():
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return pieces


def _cut(window: str) -> int:
    for separator in SEPARATORS:
        index = window.rfind(separator)
        if index >= CHUNK_SIZE // 2:
            return index + len(separator)
    return len(window)


def _slug(section: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-")
    return slug or "body"


def main() -> int:
    for scheme in SCHEMES:
        try:
            page = load(scheme)
        except LoadError:
            print(f"{scheme.scheme_id} missing")
            continue
        cards = chunk(page)
        print(f"{scheme.scheme_id} {len(cards)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
