from trade_core.self_evolution.analyzer import daily_review
from trade_core.self_evolution.proposals import build_proposal


def test_no_fake_metrics_when_no_outcomes():
    r = daily_review("2026-04-28")
    if r.get("ok"):
        assert r.get("total_pnl_usdt") is None
        assert r.get("avg_R") is None or r.get("avg_R") == "data_unavailable"


def test_proposal_insufficient_sample_size_flag():
    p = build_proposal("2026-04-28", {"outcome_count": 0, "overconfidence_rate": 0.0})
    assert p["insufficient_sample_size"] is True
    assert all(c.get("requires_human_approval") is True for c in p["changes"])
