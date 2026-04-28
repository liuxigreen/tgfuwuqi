from trade_core.models import OrderIntent, OperatingMode
from trade_core.okx_gateway import OkxGateway


def test_mock_backend_works():
    gw = OkxGateway(backend="mock")
    assert gw.get_ticker("BTC-USDT")["source"] == "mock"


def test_dry_run_never_executes():
    gw = OkxGateway(backend="mock", dry_run=True)
    intent = OrderIntent("BTC-USDT", "buy", "spot", "percent_equity", 1.0, "limit", 0.02, 0.05, True, True, True, ["x"], {}, "v1", "d1")
    out = gw.execute_order_intent(intent, OperatingMode.DEMO_AUTO)
    assert out["executed"] is False
