from trade_core.models import Direction, OperatingMode, TradeAction, TradeDecision
from trade_core.order_intent import build_order_intent


def _decision(direction):
    return TradeDecision(
        action=TradeAction.OPEN_LONG if direction == Direction.LONG else TradeAction.OPEN_SHORT,
        symbol="BTC-USDT",
        market_type="swap",
        direction=direction,
        decision_id="d1",
        final_score=80,
        confidence=0.9,
        risk_status="pass",
        reason_codes=[],
        blocked_reasons=[],
        warnings=[],
        score_breakdown={},
        recommended_size_pct=1,
        recommended_leverage=1,
        preferred_execution="demo_dry_run",
        nuwa_version="n1",
        mode=OperatingMode.DEMO_AUTO,
    )


def test_open_intent_has_exit_policy():
    intent = build_order_intent(_decision(Direction.LONG))
    assert intent.exit_policy_id
    assert intent.stop_loss_pct and intent.stop_loss_pct > 0
