from app.citation import cite


def test_citation_uses_catalog_url_from_hits():
    hits = [
        {
            "document": "Expense ratio: 1.03%.",
            "scheme_id": "hdfc-large-cap",
            "scheme_name": "HDFC Large Cap Fund",
            "source_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            "fetched_at": "2026-09-27",
        }
    ]
    result = cite("HDFC Large Cap Fund. Expense ratio: 1.03%.", hits)
    assert result["kind"] == "answer"
    assert result["source_url"] == hits[0]["source_url"]
    assert result["fetched_at"] == "2026-09-27"


def test_unknown_url_becomes_not_found():
    hits = [
        {
            "document": "Expense ratio: 1%.",
            "scheme_id": "other",
            "scheme_name": "Other Fund",
            "source_url": "https://example.com/fund",
            "fetched_at": "2026-09-27",
        }
    ]
    result = cite("Other Fund. Expense ratio: 1%.", hits)
    assert result["kind"] == "not_found"
    assert result["source_url"] is None


def test_not_found_token():
    result = cite("NOT_FOUND", [])
    assert result["kind"] == "not_found"
    assert result["source_url"] is None
