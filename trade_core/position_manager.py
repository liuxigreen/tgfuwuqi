from __future__ import annotations

from typing import Optional

from .config import load_config
from .models import Direction, ExitDecision, MarketSnapshot, NuwaEval, PositionState, SentimentSnapshot, SmartMoneySnapshot


def evaluate_exit(
    position_state: PositionState,
    market_snapshot: Optional[MarketSnapshot] = None,
    sentiment_snapshot: Optional[SentimentSnapshot] = None,
    smartmoney_snapshot: Optional[SmartMoneySnapshot] = None,
    nuwa_eval: Optional[NuwaEval] = None,
    config: Optional[dict] = None,
) -> ExitDecision:
    cfg = (config or load_config())["risk_limits"]
    reasons = []
    action = "HOLD"
    urgency = "low"
    tighten = False
    reduce_pct = 0.0

    if position_state.unrealized_pnl_pct <= -abs(position_state.stop_loss_pct):
        return ExitDecision("CLOSE", "high", ["hard_stop_loss_hit"], "invalid", 100.0, True)
    if position_state.unrealized_pnl_pct >= abs(position_state.take_profit_pct):
        return ExitDecision("REDUCE", "medium", ["take_profit_hit"], "valid", 50.0, True)

    if "invalid" in position_state.thesis.lower() or "break" in position_state.thesis.lower():
        reasons.append("thesis_invalidated")
    if nuwa_eval:
        if nuwa_eval.continuation_probability < 0.4:
            reasons.append("nuwa_continuation_drop")
        if nuwa_eval.manipulation_risk > 0.7:
            reasons.append("nuwa_manipulation_risk_up")
        if nuwa_eval.market_regime in {"chop", "panic"}:
            reasons.append("market_regime_deterioration")
    if smartmoney_snapshot:
        if position_state.side == Direction.LONG and smartmoney_snapshot.weighted_direction == Direction.SHORT:
            reasons.append("smartmoney_reversal")
        if position_state.side == Direction.SHORT and smartmoney_snapshot.weighted_direction == Direction.LONG:
            reasons.append("smartmoney_reversal")
    if sentiment_snapshot and sentiment_snapshot.sentiment_trend in {"down", "bearish", "reversal"}:
        reasons.append("sentiment_reversal")
    if position_state.age_minutes >= int(cfg.get("max_hold_minutes", 720)):
        reasons.append("time_stop_hit")

    if reasons:
        action = "CLOSE" if "thesis_invalidated" in reasons or "smartmoney_reversal" in reasons else "REDUCE"
        urgency = "high" if action == "CLOSE" else "medium"
        reduce_pct = 100.0 if action == "CLOSE" else 50.0
        tighten = True

    return ExitDecision(action, urgency, reasons, "invalid" if reasons else "valid", reduce_pct, tighten)
