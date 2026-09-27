import json

from app.ask import ask


def test_pii_log_does_not_store_the_pan(tmp_path, monkeypatch):
    log_path = tmp_path / "events.log"
    monkeypatch.setattr("app.ask.EVENTS", log_path)
    response = ask("Please look up PAN ABCDE1234F")
    assert response["kind"] == "refused_pii"
    assert response["source_url"] is None
    assert "ABCDE1234F" not in response["text"]
    logged = log_path.read_text(encoding="utf-8")
    assert "pii_blocked" in logged
    assert "ABCDE1234F" not in logged


def test_advice_does_not_recommend():
    response = ask("Should I buy HDFC Small Cap?")
    assert response["kind"] == "refused_advice"
    assert response["source_url"].endswith("hdfc-small-cap-fund-direct-growth")
    assert "you should" not in response["text"].lower()
    raw = json.dumps(response)
    assert "buy HDFC" not in response["text"]
