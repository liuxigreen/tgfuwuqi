from trade_core.skill_intelligence.metrics import build_skill_metrics


def test_skill_metrics_data_unavailable():
    out = build_skill_metrics([])
    assert out["data_unavailable"] is True
