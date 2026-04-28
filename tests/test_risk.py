from trade_core.models import AccountSnapshot, NuwaEval, OperatingMode, TradeAction
from trade_core.risk import apply_risk_rules

RISK = {"max_daily_loss_pct": 3.0, "max_open_positions": 3, "max_total_exposure_pct": 50.0, "max_leverage": 3.0, "allowed_market_types": ["swap", "spot"]}


def test_nuwa_blocked():
    nuwa = NuwaEval("v1", "trend", "cont", 0.6, 0.6, 0.2, "propose", True, 0.7, "")
    acct = AccountSnapshot(10000, 9000, -0.5, 1, False, 20, 10, "2026-04-28T00:00:00Z")
    r = apply_risk_rules(nuwa_eval=nuwa, account_snapshot=acct, mode=OperatingMode.PROPOSE, market_type="swap", action=TradeAction.OPEN_LONG, recommended_size_pct=1, recommended_leverage=2, allow_live_execution=False, risk_limits=RISK)
    assert r.risk_status == "blocked"
