from trade_core.self_evolution import build_proposal


def test_self_evolve_changes_require_human_approval():
    out = build_proposal("2026-04-28", {"outcome_count": 20, "overconfidence_rate": 0.3})
    assert out["requires_human_approval"] is True
    assert all(c.get("safe_to_auto_apply") is False for c in out["changes"])
