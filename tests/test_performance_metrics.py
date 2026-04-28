from trade_core.self_evolution.performance_metrics import compute_performance_metrics


def test_performance_metrics_data_unavailable():
    out = compute_performance_metrics([])
    assert out["data_unavailable"] is True
