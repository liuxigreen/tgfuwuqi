from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .models import AccountSnapshot, NuwaEval, OperatingMode, TradeAction


@dataclass
class RiskResult:
    risk_status: str
    blocked_reasons: List[str]
    risk_adjusted_size_pct: float


def apply_risk_rules(
    *,
    nuwa_eval: NuwaEval,
    account_snapshot: Optional[AccountSnapshot],
    mode: OperatingMode,
    market_type: str,
    action: TradeAction,
    recommended_size_pct: float,
    recommended_leverage: float,
    allow_live_execution: bool,
    risk_limits: dict,
) -> RiskResult:
    blocked: List[str] = []
    size = recommended_size_pct

    if nuwa_eval.block_trade:
        blocked.append("nuwa_block_trade")

    if mode in {OperatingMode.DEMO_AUTO, OperatingMode.LIVE_GUARDED} and account_snapshot is None:
        blocked.append("missing_account_snapshot")

    if market_type not in set(risk_limits.get("allowed_market_types", ["swap", "spot"])):
        blocked.append("market_type_not_allowed")

    if recommended_leverage > float(risk_limits.get("max_leverage", 3.0)):
        blocked.append("leverage_too_high")

    if mode == OperatingMode.LIVE_GUARDED and not allow_live_execution:
        blocked.append("live_execution_not_allowed")

    if account_snapshot is not None:
        if account_snapshot.daily_pnl_pct <= -float(risk_limits.get("max_daily_loss_pct", 3.0)):
            blocked.append("daily_loss_limit_hit")
        if account_snapshot.open_positions_count >= int(risk_limits.get("max_open_positions", 3)):
            blocked.append("too_many_open_positions")
        if account_snapshot.same_symbol_existing_position and action not in {TradeAction.REDUCE, TradeAction.CLOSE}:
            blocked.append("same_symbol_position_exists")
        if account_snapshot.total_exposure_pct >= float(risk_limits.get("max_total_exposure_pct", 50.0)):
            blocked.append("total_exposure_too_high")
        if account_snapshot.max_position_exposure_pct > 30:
            size *= 0.8

    if mode == OperatingMode.OBSERVE:
        size = 0.0

    if blocked:
        return RiskResult("blocked", sorted(set(blocked)), 0.0)
    return RiskResult("ok", [], round(max(0.0, size), 4))
