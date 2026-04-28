import json

from trade_core.lifecycle import run_pretrade_pipeline


def test_pipeline_returns_result(tmp_path):
    sample = json.loads(open("examples/full_case.json", "r", encoding="utf-8").read())
    out = run_pretrade_pipeline(sample, mode="propose", journal_dir=str(tmp_path))
    assert "pipeline_id" in out
    assert "decision" in out and "order_intent" in out
    assert out["execution_result"]["executed"] is False
    assert out["journal_path"]
