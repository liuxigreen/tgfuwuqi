from trade_core.fast_path import run_fast_signal_pipeline


def test_fast_path_has_experience_fields():
    sample = {"radar_signal": {"symbol": "BTC-USDT", "market_type": "swap", "direction": "long", "score": 80, "source": "x", "timestamp": "2026-04-28T00:00:00Z"}, "nuwa_eval": {"version": "n", "market_regime": "x", "signal_archetype": "x", "signal_quality": 0.5, "continuation_probability": 0.5, "manipulation_risk": 0.5, "preferred_action": "observe", "block_trade": False, "confidence": 0.7, "notes": ""}}
    out = run_fast_signal_pipeline(sample, mode="propose")
    assert "experience_retrieval_used" in out
    assert "experience_adjustments" in out
