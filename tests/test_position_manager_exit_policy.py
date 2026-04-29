from trade_core.models import Direction, PositionState


def test_position_state_accepts_exit_policy_fields():
    p = PositionState(position_id="1", symbol="BTC-USDT", side=Direction.LONG, entry_price=1, current_price=1, unrealized_pnl_pct=0, age_minutes=1, entry_reason_codes=[], thesis="x", stop_loss_pct=0.01, take_profit_pct=0.02)
    assert p.stop_loss_pct == 0.01
