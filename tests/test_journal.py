from trade_core.journal import review_journal, write_journal_event


def test_journal_writes_jsonl(tmp_path):
    p = write_journal_event("decision", "pipe1", "BTC-USDT", {"foo": "bar"}, base_dir=str(tmp_path))
    assert p.endswith(".jsonl")


def test_no_secrets_in_journal(tmp_path):
    p = write_journal_event("decision", "pipe1", "BTC-USDT", {"api_key": "abc", "secret": "x"}, base_dir=str(tmp_path))
    text = open(p, "r", encoding="utf-8").read()
    assert "\"api_key\"" not in text


def test_review_summary(tmp_path):
    p = write_journal_event("review", "pipe1", "BTC-USDT", {"status": "blocked"}, base_dir=str(tmp_path))
    out = review_journal(p)
    assert out["ok"] is True
