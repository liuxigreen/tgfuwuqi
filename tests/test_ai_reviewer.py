import json
from pathlib import Path

from trade_core.learning_loop.reviewer import review_outcomes


def test_wrong_outcome_generates_review(tmp_path):
    p = tmp_path / "2026-04-28.outcomes.jsonl"
    p.write_text(json.dumps({"outcome_id": "o1", "snapshot_id": "s1", "correctness_label": "wrong", "error_type": "thesis_invalidated"}) + "\n", encoding="utf-8")
    out = review_outcomes("2026-04-28", outcomes_path=str(p))
    assert out["reviews"] and out["reviews"][0]["requires_human_approval"] is True
