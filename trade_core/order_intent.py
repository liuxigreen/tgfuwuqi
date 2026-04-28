from __future__ import annotations

from typing import Optional

from .config import load_config
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
        )

    side = "buy" if decision.direction == Direction.LONG else "sell"
    size = min(1.0, decision.recommended_size_pct) if decision.action == TradeAction.SMALL_PROBE else max(0.5, decision.recommended_size_pct)

    return OrderIntent(
        symbol=decision.symbol,
        side=side,
        market_type=decision.market_type,
        size_mode="percent_equity",
        size=round(size, 4),
        entry_type="limit",
        stop_loss_pct=float(risk.get("default_stop_loss_pct", 1.8)),
        take_profit_pct=float(risk.get("default_take_profit_pct", 3.5)),
        use_oco=True,
        use_trailing_stop=True,
        dry_run=True,
        reason_codes=decision.reason_codes,
        risk_summary={"risk_status": decision.risk_status, "blocked_reasons": decision.blocked_reasons},
        nuwa_version=decision.nuwa_version,
        decision_id=decision.decision_id,
    )
