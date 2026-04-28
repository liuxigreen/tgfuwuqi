from trade_core.okx_gateway import OkxGateway
from trade_core.scout import run_scout


def test_scout_returns_candidates():
    out = run_scout(["BTC-USDT-SWAP"], "propose", OkxGateway())
    assert out["candidates"]


def test_missing_adapter_no_crash():
    out = run_scout(["BTC-USDT-SWAP"], "propose", OkxGateway(backend="mock"))
    assert "warnings" in out


def test_blocked_candidates_allowed_in_report():
    out = run_scout(["BTC-USDT-SWAP"], "observe", OkxGateway())
    assert out["candidates"][0]["suggested_action"] == "observe"
