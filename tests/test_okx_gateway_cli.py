from trade_core.models import OrderIntent, OperatingMode
from trade_core.okx_gateway import OkxGateway


def test_no_okx_cli_structured_error():
    gw = OkxGateway(backend="cli")
    if gw.okx_bin:
        assert True
    else:
        out = gw.get_ticker("BTC-USDT")
        assert out.get("error") == "okx_cli_not_found"


def test_okx_check_safe():
    gw = OkxGateway(backend="cli")
    out = gw.okx_check()
    assert "backend" in out


def test_live_execution_blocked():
    gw = OkxGateway(backend="cli", profile="live", dry_run=False, allow_live=False, allow_trade_execution=True)
    intent = OrderIntent("BTC-USDT", "buy", "spot", "percent_equity", 1.0, "limit", 0.02, 0.05, True, True, False, ["x"], {}, "v1", "d1")
    out = gw.execute_order_intent(intent, OperatingMode.DEMO_AUTO)
    assert out["status"] == "blocked"


def test_demo_execution_default_dry_run():
    gw = OkxGateway(backend="cli", profile="demo", dry_run=True)
    intent = OrderIntent("BTC-USDT", "buy", "spot", "percent_equity", 1.0, "limit", 0.02, 0.05, True, True, True, ["x"], {}, "v1", "d1")
    out = gw.execute_order_intent(intent, OperatingMode.DEMO_AUTO)
    assert out["status"] == "dry_run"
