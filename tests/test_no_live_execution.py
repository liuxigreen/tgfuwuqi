from trade_core.models import OperatingMode, OrderIntent
from trade_core.okx_gateway import OkxGateway


def test_live_profile_always_blocked():
    gw = OkxGateway(backend="mock", profile="live", dry_run=False, allow_live=False, allow_trade_execution=True)
    intent = OrderIntent(
        symbol="BTC-USDT",
        side="buy",
        market_type="spot",
        size_mode="percent_equity",
        size=0.1,
        entry_type="limit",
        stop_loss_pct=0.01,
        take_profit_pct=0.02,
        use_oco=True,
        use_trailing_stop=True,
        dry_run=False,
        reason_codes=[],
        risk_summary={},
        nuwa_version="n",
        decision_id="d",
        exit_policy_id="capital_protection",
    )
    out = gw.execute_order_intent(intent, OperatingMode.DEMO_AUTO, risk_result={"passed": True}, demo_execute=True)
    assert out["blocked"] is True
    assert out["error_code"] == "live_profile_blocked"


def test_default_dry_run_true_path():
    gw = OkxGateway(backend="mock", profile="demo", dry_run=True, allow_live=False, allow_trade_execution=False)
    intent = OrderIntent(
        symbol="BTC-USDT",
        side="buy",
        market_type="spot",
        size_mode="percent_equity",
        size=0.1,
        entry_type="limit",
        stop_loss_pct=0.01,
        take_profit_pct=0.02,
        use_oco=True,
        use_trailing_stop=True,
        dry_run=True,
        reason_codes=[],
        risk_summary={},
        nuwa_version="n",
        decision_id="d",
        exit_policy_id="capital_protection",
    )
    out = gw.execute_order_intent(intent, OperatingMode.DEMO_AUTO, risk_result={"passed": True}, demo_execute=False)
    assert out["dry_run"] is True
