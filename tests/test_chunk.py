from pathlib import Path

from ingest.chunk import CHUNK_OVERLAP, CHUNK_SIZE, chunk
from ingest.load import RawPage, load
from ingest.catalog import SCHEMES

PAGE = RawPage(
    scheme_id="hdfc-elss",
    scheme_name="HDFC ELSS Tax Saver Fund",
    category="ELSS",
    source_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    fetched_at="2026-09-27",
    text=(
        "# HDFC ELSS Tax Saver Fund\n\n"
        "Direct-Growth. Category: ELSS.\n\n"
        "## Exit load\n"
        "Exit load: Nil.\n"
    ),
)


def test_short_section_is_one_card_with_scheme_header():
    cards = chunk(PAGE)
    exit_load = [card for card in cards if card.section == "Exit load"]
    assert len(exit_load) == 1
    card = exit_load[0]
    assert card.document.startswith(
        "# HDFC ELSS Tax Saver Fund (ELSS)\n"
        "Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth\n"
    )
    assert card.id == "hdfc-elss:exit-load:0"
    assert "Exit load: Nil." in card.document
    body = card.document.split("\n", 2)[2]
    assert len(body) <= CHUNK_SIZE


def test_long_section_overlaps_and_stays_within_size():
    sentence = "Exit load stays 1 percent if redeemed early. "
    body = sentence * 30
    page = RawPage(
        scheme_id="hdfc-large-cap",
        scheme_name="HDFC Large Cap Fund",
        category="Large Cap",
        source_url="https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        fetched_at="2026-09-27",
        text=f"# HDFC Large Cap Fund\n\n## Exit load\n{body}\n",
    )
    cards = [card for card in chunk(page) if card.section == "Exit load"]
    assert len(cards) > 1
    prefix = cards[0].document.split("\n", 2)[0] + "\n" + cards[0].document.split("\n", 2)[1] + "\n"
    bodies = [card.document[len(prefix) :] for card in cards]
    assert all(len(body) <= CHUNK_SIZE for body in bodies)
    assert bodies[1][:CHUNK_OVERLAP] == bodies[0][-CHUNK_OVERLAP:]


def test_real_snapshots_are_small_and_labeled():
    root = Path(__file__).resolve().parents[1] / "data" / "raw"
    if not any(root.glob("hdfc-*.md")):
        return
    for scheme in SCHEMES:
        if not (root / f"{scheme.scheme_id}.md").exists():
            continue
        cards = chunk(load(scheme))
        assert 1 <= len(cards) <= 30
        for card in cards:
            assert card.document.startswith(f"# {scheme.scheme_name} ({scheme.category})\nSource: {scheme.source_url}\n")
            body = card.document.split("Source: ", 1)[1].split("\n", 1)[1]
            assert len(body) <= CHUNK_SIZE
