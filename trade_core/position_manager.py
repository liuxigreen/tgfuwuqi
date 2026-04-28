from __future__ import annotations

from typing import Optional

from .models import Direction, ExitDecision, MarketSnapshot, NuwaEval, PositionExitEvaluation, PositionState, SentimentSnapshot, SmartMoneySnapshot


EXIT_DEFAULT = {
    "first_tp_pct": 0.03,
    "final_tp_pct": 0.08,
    "stop_loss_pct": 0.02,
    "max_hold_minutes": 720,
    "tighten_stop_after_rr": 1.2,
    "partial_take_profit_pct": 0.35,
}


def evaluate_position_exit(
    position_state: PositionState,
    sentiment_snapshot: Optional[SentimentSnapshot] = None,
    smartmoney_snapshot: Optional[SmartMoneySnapshot] = None,
    nuwa_eval: Optional[NuwaEval] = None,
    market_snapshot: Optional[MarketSnapshot] = None,
    rules: Optional[dict] = None,
) -> PositionExitEvaluation:
    r = {**EXIT_DEFAULT, **(rules or {})}
    reasons = []
    pnl = position_state.unrealized_pnl_pct / 100 if abs(position_state.unrealized_pnl_pct) > 1 else position_state.unrealized_pnl_pct
    rr_progress = max(0.0, pnl / max(1e-6, r["first_tp_pct"]))
    recommended = "HOLD"

    if pnl <= -abs(r["stop_loss_pct"]):
        recommended = "EXIT_FULL"
        reasons.append("hard_stop")
    elif pnl >= r["final_tp_pct"]:
        recommended = "TIGHTEN_STOP"
        reasons.append("final_tp")
    elif pnl >= r["first_tp_pct"]:
        recommended = "TAKE_PARTIAL_PROFIT"
        reasons.append("first_tp")

    thesis_status = "valid"
    continuation = nuwa_eval.continuation_probability if nuwa_eval else 0.5
    if nuwa_eval and getattr(nuwa_eval, "notes", ""):
        low = nuwa_eval.notes.lower()
        if "invalidated" in low or "failed" in low:
            thesis_status = "invalidated"
            recommended = "EXIT_FULL"
            reasons.append("thesis_invalidated")
        elif "weakening" in low:
            thesis_status = "weakening"
            recommended = "REDUCE" if recommended == "HOLD" else recommended
            reasons.append("thesis_weakening")

    smart_align = "unknown"
    if smartmoney_snapshot:
        opp = (position_state.side == Direction.LONG and smartmoney_snapshot.weighted_direction == Direction.SHORT) or (
            position_state.side == Direction.SHORT and smartmoney_snapshot.weighted_direction == Direction.LONG
        )
        smart_align = "against" if opp else "aligned"
        if opp:
            recommended = "REDUCE" if recommended == "HOLD" else recommended
            reasons.append("smartmoney_reversal")

    senti_align = "unknown"
    if sentiment_snapshot:
        bad = (position_state.side == Direction.LONG and sentiment_snapshot.sentiment_trend in {"down", "bearish", "reversal"}) or (
            position_state.side == Direction.SHORT and sentiment_snapshot.sentiment_trend in {"up", "bullish", "reversal"}
        )
        senti_align = "against" if bad else "aligned"
        if bad and recommended == "HOLD":
            recommended = "REVIEW_REQUIRED"
            reasons.append("sentiment_reversal")

    oi_confirmation = "unknown"
    if market_snapshot:
        oi_confirmation = "confirmed" if market_snapshot.open_interest_change_pct > 0 else "weak"

    if position_state.age_minutes > r["max_hold_minutes"] and rr_progress < 0.5 and recommended == "HOLD":
        recommended = "REDUCE"
        reasons.append("time_stop")

    if continuation < 0.35 and recommended == "HOLD":
        recommended = "BLOCK_ADD"
        reasons.append("no_add_rule")

    return PositionExitEvaluation(
        position_id=position_state.position_id,
        symbol=position_state.symbol,
        side=position_state.side,
        entry_price=position_state.entry_price,
        current_price=position_state.current_price,
        unrealized_pnl_pct=position_state.unrealized_pnl_pct,
        rr_progress=round(rr_progress, 4),
        thesis_status=thesis_status,
        continuation_probability=continuation,
        smart_money_alignment=smart_align,
        sentiment_alignment=senti_align,
        oi_confirmation=oi_confirmation,
        time_in_position_minutes=position_state.age_minutes,
        recommended_action=recommended,
        reason_codes=sorted(set(reasons)),
    )


def evaluate_exit(
    position_state: PositionState,
    market_snapshot: Optional[MarketSnapshot] = None,
    sentiment_snapshot: Optional[SentimentSnapshot] = None,
    smartmoney_snapshot: Optional[SmartMoneySnapshot] = None,
    nuwa_eval: Optional[NuwaEval] = None,
    config: Optional[dict] = None,
) -> ExitDecision:
    result = evaluate_position_exit(position_state, sentiment_snapshot, smartmoney_snapshot, nuwa_eval, market_snapshot)
    mapper = {
        "HOLD": ("HOLD", "low", 0.0, False),
        "REDUCE": ("REDUCE", "medium", 50.0, True),
        "REVIEW_REQUIRED": ("REDUCE", "medium", 30.0, True),
        "TAKE_PARTIAL_PROFIT": ("REDUCE", "medium", 35.0, True),
        "TIGHTEN_STOP": ("REDUCE", "medium", 20.0, True),
        "EXIT_FULL": ("CLOSE", "high", 100.0, True),
        "BLOCK_ADD": ("REDUCE", "medium", 0.0, True),
    }
    action, urgency, pct, tighten = mapper[result.recommended_action]
    return ExitDecision(action, urgency, result.reason_codes, result.thesis_status, pct, tighten)
