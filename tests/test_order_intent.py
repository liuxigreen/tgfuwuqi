from trade_core.models import OperatingMode, TradeAction, TradeDecision
from trade_core.order_intent import build_order_intent


def base_decision(action: TradeAction):
    return TradeDecision(
        action=action,
        symbol="BTC-USDT-SWAP",
        final_score=82,
        confidence=0.8,
        risk_status="ok",
        reason_codes=["x"],
        blocked_reasons=[],
        recommended_size_pct=1.2,
        recommended_leverage=2,
        preferred_execution="dry_run",
        nuwa_version="v1",
        mode=OperatingMode.PROPOSE,
    )


def test_default_dry_run():
    i = build_order_intent(base_decision(TradeAction.PROPOSE))
    assert i.dry_run is True


def test_open_has_sl_tp():
    i = build_order_intent(base_decision(TradeAction.OPEN_LONG))
    assert i.stop_loss_pct is not None and i.take_profit_pct is not None
