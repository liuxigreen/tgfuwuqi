from trade_core.models import Direction, OperatingMode, TradeAction, TradeDecision
from trade_core.order_intent import build_order_intent


def test_default_dry_run():
    d = TradeDecision(TradeAction.PROPOSE, "BTC-USDT-SWAP", "swap", Direction.LONG, "d", 70, 0.8, "ok", ["x"], [], [], 1.0, 2.0, "dry_run", "v1", OperatingMode.PROPOSE)
    i = build_order_intent(d)
    assert i.dry_run is True


def test_open_has_sl_tp():
    d = TradeDecision(TradeAction.OPEN_LONG, "BTC-USDT-SWAP", "swap", Direction.LONG, "d", 85, 0.8, "ok", ["x"], [], [], 1.0, 2.0, "dry_run", "v1", OperatingMode.PROPOSE)
    i = build_order_intent(d)
    assert i.stop_loss_pct is not None and i.take_profit_pct is not None
