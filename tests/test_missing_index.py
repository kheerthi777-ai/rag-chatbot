from app.ask import INDEX_MESSAGE, ask


def test_missing_index_tells_you_to_run_ingest(monkeypatch, tmp_path):
    monkeypatch.setattr("ingest.store.CHROMA_DIR", tmp_path / "no-index")
    response = ask("What is the expense ratio of HDFC Large Cap Fund Direct Growth?")
    assert response["kind"] == "error"
    assert response["text"] == INDEX_MESSAGE
    assert response["source_url"] is None
