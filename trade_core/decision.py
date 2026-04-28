from __future__ import annotations

from typing import Optional

from .config import load_config
from .models import (
    AccountSnapshot,
    Direction,
    MarketSnapshot,
    NuwaEval,
    OperatingMode,
    RadarSignal,
    SentimentSnapshot,
    SmartMoneySnapshot,
    TradeAction,
    TradeDecision,
)
from .risk import apply_risk_rules
from .scoring import compute_score


def _to_mode(mode: str | OperatingMode) -> OperatingMode:
    if isinstance(mode, OperatingMode):
        return mode
    try:
        return OperatingMode(mode)
    except Exception:
        return OperatingMode.PROPOSE


def _score_to_action(score: float, direction: Direction) -> TradeAction:
    if score < 50:
        return TradeAction.OBSERVE
    if score < 65:
        return TradeAction.PROPOSE
    if score < 80:
        return TradeAction.SMALL_PROBE
    return TradeAction.OPEN_LONG if direction == Direction.LONG else TradeAction.OPEN_SHORT


def build_trade_decision(
    radar_signal: RadarSignal,
    nuwa_eval: NuwaEval,
    market_snapshot: Optional[MarketSnapshot] = None,
    sentiment_snapshot: Optional[SentimentSnapshot] = None,
    smartmoney_snapshot: Optional[SmartMoneySnapshot] = None,
    account_snapshot: Optional[AccountSnapshot] = None,
    mode: str | OperatingMode = "propose",
    config: Optional[dict] = None,
) -> TradeDecision:
    cfg = config or load_config()
    run_mode = _to_mode(mode)

    if nuwa_eval.block_trade:
        return TradeDecision(
            action=TradeAction.BLOCKED,
            symbol=radar_signal.symbol,
            final_score=0.0,
            confidence=nuwa_eval.confidence,
            risk_status="blocked",
            reason_codes=["nuwa_block_trade"],
            blocked_reasons=["nuwa_block_trade"],
            recommended_size_pct=0.0,
            recommended_leverage=1.0,
            preferred_execution="none",
            nuwa_version=nuwa_eval.version,
            mode=run_mode,
        )

    breakdown = compute_score(
        radar_signal,
        nuwa_eval,
        market_snapshot=market_snapshot,
        sentiment_snapshot=sentiment_snapshot,
        smartmoney_snapshot=smartmoney_snapshot,
        weights=cfg["scoring_weights"],
    )

    action = _score_to_action(breakdown.total_score, radar_signal.direction)
    size_pct = 2.0 if action in {TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT} else 1.0
    if action == TradeAction.SMALL_PROBE:
        size_pct = 0.8
    leverage = 2.0

    pa = (nuwa_eval.preferred_action or "").lower()
    reason_codes = list(breakdown.reason_codes)
    if pa == "wait_pullback" and action in {TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT, TradeAction.SMALL_PROBE}:
        action = TradeAction.PROPOSE
        reason_codes.append("nuwa_wait_pullback")
        size_pct = min(size_pct, 0.8)
    elif pa == "small_probe":
        if action in {TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT}:
            action = TradeAction.SMALL_PROBE
        size_pct = min(size_pct, 1.0)
        reason_codes.append("nuwa_small_probe")
    elif pa == "observe":
        action = TradeAction.OBSERVE
        size_pct = 0.0
        reason_codes.append("nuwa_observe")
    elif pa == "block":
        action = TradeAction.BLOCKED
        size_pct = 0.0
        reason_codes.append("nuwa_block_preferred")

    risk = apply_risk_rules(
        nuwa_eval=nuwa_eval,
        account_snapshot=account_snapshot,
        mode=run_mode,
        market_type=radar_signal.market_type,
        action=action,
        recommended_size_pct=size_pct,
        recommended_leverage=leverage,
        allow_live_execution=bool(cfg["operating_modes"].get("allow_live_execution", False)),
        risk_limits=cfg["risk_limits"],
    )
    if risk.risk_status == "blocked":
        action = TradeAction.BLOCKED

    preferred_execution = "dry_run"
    if run_mode == OperatingMode.DEMO_AUTO:
        preferred_execution = "demo_dry_run"
    elif run_mode == OperatingMode.LIVE_GUARDED:
        preferred_execution = "guarded_intent_only"

    return TradeDecision(
        action=action,
        symbol=radar_signal.symbol,
        final_score=breakdown.total_score,
        confidence=round((nuwa_eval.confidence + radar_signal.score / 100) / 2, 4),
        risk_status=risk.risk_status,
        reason_codes=sorted(set(reason_codes)),
        blocked_reasons=risk.blocked_reasons,
        recommended_size_pct=risk.risk_adjusted_size_pct,
        recommended_leverage=min(leverage, float(cfg["risk_limits"].get("max_leverage", 3))),
        preferred_execution=preferred_execution,
        nuwa_version=nuwa_eval.version,
        mode=run_mode,
    )
