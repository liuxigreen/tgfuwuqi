from trade_core.models import Direction, OperatingMode, TradeAction, TradeDecision
from trade_core.order_intent import build_order_intent


def make_decision(direction: Direction, market_type: str):
    return TradeDecision(
        action=TradeAction.SMALL_PROBE,
        symbol="BTC-USDT" if market_type == "spot" else "BTC-USDT-SWAP",
        market_type=market_type,
        direction=direction,
        decision_id="dec_test",
        final_score=70,
        confidence=0.8,
        risk_status="ok",
        reason_codes=["x"],
        blocked_reasons=[],
        warnings=[],
        recommended_size_pct=0.8,
        recommended_leverage=2.0,
        preferred_execution="dry_run",
        nuwa_version="v1",
        mode=OperatingMode.PROPOSE,
    )


def test_small_probe_long_buy():
    intent = build_order_intent(make_decision(Direction.LONG, "swap"))
    assert intent.side == "buy"


def test_small_probe_short_sell():
    intent = build_order_intent(make_decision(Direction.SHORT, "swap"))
    assert intent.side == "sell"


def test_spot_stays_spot():
    intent = build_order_intent(make_decision(Direction.LONG, "spot"))
    assert intent.market_type == "spot"


def test_swap_stays_swap():
    intent = build_order_intent(make_decision(Direction.LONG, "swap"))
    assert intent.market_type == "swap"
