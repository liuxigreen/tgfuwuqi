from __future__ import annotations

from typing import Optional

from .config import load_config
from .models import OrderIntent, TradeAction, TradeDecision


def build_order_intent(decision: TradeDecision, config: Optional[dict] = None) -> OrderIntent:
    cfg = config or load_config()
    risk = cfg["risk_limits"]
    side = "none"
    entry_type = "none"
    size_mode = "percent_equity"
    size_pct = 0.0
    stop_loss_pct = None
    take_profit_pct = None

    if decision.action in {TradeAction.BLOCKED, TradeAction.OBSERVE}:
        pass
    elif decision.action == TradeAction.PROPOSE:
        side = "proposal"
        entry_type = "proposal"
        size_pct = min(1.0, max(0.0, decision.recommended_size_pct))
    elif decision.action == TradeAction.SMALL_PROBE:
        side = "buy" if "long" in decision.action.value else "sell"
        entry_type = "limit"
        size_pct = min(1.0, max(0.2, decision.recommended_size_pct))
        stop_loss_pct = float(risk.get("default_stop_loss_pct", 1.8))
        take_profit_pct = float(risk.get("default_take_profit_pct", 3.5))
    elif decision.action in {TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT}:
        side = "buy" if decision.action == TradeAction.OPEN_LONG else "sell"
        entry_type = "limit"
        size_pct = max(0.5, decision.recommended_size_pct)
        stop_loss_pct = float(risk.get("default_stop_loss_pct", 1.8))
        take_profit_pct = float(risk.get("default_take_profit_pct", 3.5))

    return OrderIntent(
        symbol=decision.symbol,
        side=side,
        market_type="swap",
        size_mode=size_mode,
        size_pct=round(size_pct, 4),
        entry_type=entry_type,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        use_oco=True,
        use_trailing_stop=decision.action in {TradeAction.SMALL_PROBE, TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT},
        dry_run=True,
        reason_codes=decision.reason_codes,
    )
