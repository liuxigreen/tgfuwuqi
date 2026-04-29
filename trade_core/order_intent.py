from __future__ import annotations

from typing import Optional

from .config import load_config
from .exit_policy import select_exit_policy
from .models import Direction, OrderIntent, TradeAction, TradeDecision


def build_order_intent(decision: TradeDecision, config: Optional[dict] = None) -> OrderIntent:
    cfg = config or load_config()
    risk = cfg["risk_limits"]

    executable = decision.action in {TradeAction.SMALL_PROBE, TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT} and decision.direction in {Direction.LONG, Direction.SHORT}
    if not executable:
        return OrderIntent(
            symbol=decision.symbol,
            side="none",
            market_type=decision.market_type,
            size_mode="percent_equity",
            size=0.0,
            entry_type="none",
            stop_loss_pct=None,
            take_profit_pct=None,
            use_oco=False,
            use_trailing_stop=False,
            dry_run=True,
            reason_codes=decision.reason_codes,
            risk_summary={"risk_status": decision.risk_status, "blocked_reasons": decision.blocked_reasons},
            nuwa_version=decision.nuwa_version,
            decision_id=decision.decision_id,
            exit_reason_plan=["non_executable_direction_or_action"],
        )

    side = "buy" if decision.direction == Direction.LONG else "sell"
    size = min(1.0, decision.recommended_size_pct) if decision.action == TradeAction.SMALL_PROBE else max(0.5, decision.recommended_size_pct)
    policy = select_exit_policy(decision, type("N", (), {"signal_archetype": "trend", "confidence": decision.confidence, "manipulation_risk": 0.5})(), config=cfg)
    stop = float(policy.stop_loss_pct)
    if stop <= 0:
        return OrderIntent(
            symbol=decision.symbol,
            side="none",
            market_type=decision.market_type,
            size_mode="percent_equity",
            size=0.0,
            entry_type="none",
            stop_loss_pct=None,
            take_profit_pct=None,
            use_oco=False,
            use_trailing_stop=False,
            dry_run=True,
            reason_codes=sorted(set(list(decision.reason_codes) + ["missing_stop_loss"])),
            risk_summary={"risk_status": "blocked", "blocked_reasons": ["missing_stop_loss"]},
            nuwa_version=decision.nuwa_version,
            decision_id=decision.decision_id,
        )

    return OrderIntent(
        symbol=decision.symbol,
        side=side,
        market_type=decision.market_type,
        size_mode="percent_equity",
        size=round(size, 4),
        entry_type="limit",
        stop_loss_pct=stop,
        take_profit_pct=float(policy.final_take_profit_pct),
        use_oco=True,
        use_trailing_stop=True,
        dry_run=True,
        reason_codes=decision.reason_codes,
        risk_summary={"risk_status": decision.risk_status, "blocked_reasons": decision.blocked_reasons},
        nuwa_version=decision.nuwa_version,
        decision_id=decision.decision_id,
        exit_policy_id=policy.policy_id,
        first_take_profit_pct=float(policy.first_take_profit_pct),
        final_take_profit_pct=float(policy.final_take_profit_pct),
        partial_take_profit_pct=float(policy.partial_take_profit_pct),
        trailing_stop={"enabled": bool(policy.trailing_stop_enabled)},
        time_stop_minutes=int(policy.max_hold_minutes),
        exit_reason_plan=["stop_loss", "take_profit", "time_stop", "thesis_invalidation"],
    )
