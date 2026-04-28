from trade_core.learning_loop.outcome import evaluate_outcomes


def test_missing_price_data_unavailable():
    out = evaluate_outcomes(snapshots=[{"snapshot_id": "s1", "decision_id": "d1", "pipeline_id": "p1", "symbol": "BTC-USDT", "direction": "long", "entry_price": None, "confidence": 0.8, "nuwa_version": "n"}], horizon="24h")
    assert out["outcomes"][0]["correctness_label"] == "data_unavailable"
