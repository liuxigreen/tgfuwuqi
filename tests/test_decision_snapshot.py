from trade_core.learning_loop.snapshot import create_decision_snapshot


def test_decision_snapshot_contains_core_fields():
    snap = create_decision_snapshot(
        {"pipeline_id": "p1", "decision": {"decision_id": "d1", "symbol": "BTC-USDT", "market_type": "swap", "direction": "long", "action": "propose", "confidence": 0.7, "final_score": 72, "score_breakdown": {"total_score": 72}, "nuwa_version": "n1", "reason_codes": [], "blocked_reasons": [], "warnings": []}, "order_intent": {"exit_policy_id": "trend_following_default"}},
        {"radar_signal": {"symbol": "BTC-USDT"}, "market_snapshot": {"price": 1}},
    )
    assert snap["score_breakdown"]["total_score"] == 72
    assert snap["smartmoney_snapshot"]["status"] == "unavailable"
