from trade_core.models import AccountSnapshot, NuwaEval, OperatingMode, TradeAction
from trade_core.risk import apply_risk_rules


RISK = {
    "max_daily_loss_pct": 3.0,
    "max_open_positions": 3,
    "max_total_exposure_pct": 50.0,
    "max_leverage": 3.0,
    "allowed_market_types": ["swap", "spot"],
}


def nuwa(block=False):
    return NuwaEval("v1", "trend", "cont", 0.6, 0.6, 0.2, "propose", block, 0.7, "")


def acct(loss=-0.5):
    return AccountSnapshot(10000, 9000, loss, 1, False, 20, 10, "2026-04-28T00:00:00Z")


def test_nuwa_blocked():
    r = apply_risk_rules(
        nuwa_eval=nuwa(True),
        account_snapshot=acct(),
        mode=OperatingMode.PROPOSE,
        market_type="swap",
        action=TradeAction.OPEN_LONG,
        recommended_size_pct=1,
        recommended_leverage=2,
        allow_live_execution=False,
        risk_limits=RISK,
    )
    assert r.risk_status == "blocked"


def test_daily_loss_blocked():
    r = apply_risk_rules(
        nuwa_eval=nuwa(False),
        account_snapshot=acct(-3.5),
        mode=OperatingMode.PROPOSE,
        market_type="swap",
        action=TradeAction.OPEN_LONG,
        recommended_size_pct=1,
        recommended_leverage=2,
        allow_live_execution=False,
        risk_limits=RISK,
    )
    assert "daily_loss_limit_hit" in r.blocked_reasons


def test_missing_account_block_demo_auto():
    r = apply_risk_rules(
        nuwa_eval=nuwa(False),
        account_snapshot=None,
        mode=OperatingMode.DEMO_AUTO,
        market_type="swap",
        action=TradeAction.OPEN_LONG,
        recommended_size_pct=1,
        recommended_leverage=2,
        allow_live_execution=False,
        risk_limits=RISK,
    )
    assert "missing_account_snapshot" in r.blocked_reasons
