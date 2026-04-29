from trade_core.learning_loop.experience_store import add_experience_from_review


def test_review_to_experience_requires_evidence():
    out = add_experience_from_review({"review_id": "r1", "should_update_experience_store": True, "snapshot_id": "s1", "outcome_id": "o1", "lesson": "x", "rule_suggestion": "y"})
    assert out["ok"] is True
    e = out["experience"]
    assert e["evidence"]["snapshot_id"] == "s1"
    assert e["when_to_apply"] and e["when_not_to_apply"]
