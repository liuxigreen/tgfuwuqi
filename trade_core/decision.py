from __future__ import annotations

import uuid
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
from .utils import is_stale


def _to_mode(mode: str | OperatingMode) -> OperatingMode:
    try:
        return mode if isinstance(mode, OperatingMode) else OperatingMode(mode)
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
    warnings = []
    blocked_reasons = []

    snapshots = [market_snapshot, sentiment_snapshot, smartmoney_snapshot]
    if any(s is not None and s.symbol != radar_signal.symbol for s in snapshots):
        blocked_reasons.append("symbol_mismatch")

    max_age = int(cfg["operating_modes"].get("max_snapshot_age_minutes", 15))
    for name, ts in [
        ("radar", radar_signal.timestamp),
        ("market", getattr(market_snapshot, "timestamp", "")),
        ("sentiment", getattr(sentiment_snapshot, "timestamp", "")),
        ("smartmoney", getattr(smartmoney_snapshot, "timestamp", "")),
    ]:
        if not ts:
            continue
        stale, err = is_stale(ts, max_age)
        if err:
            if run_mode in {OperatingMode.DEMO_AUTO, OperatingMode.LIVE_GUARDED}:
                blocked_reasons.append(f"{name}_timestamp_invalid")
            else:
                warnings.append(f"{name}_timestamp_invalid")
        elif stale:
            if run_mode in {OperatingMode.DEMO_AUTO, OperatingMode.LIVE_GUARDED}:
                blocked_reasons.append(f"{name}_snapshot_stale")
            else:
                warnings.append(f"{name}_snapshot_stale")

    if account_snapshot is not None:
        stale, err = is_stale(account_snapshot.timestamp, max_age)
        if err and run_mode in {OperatingMode.DEMO_AUTO, OperatingMode.LIVE_GUARDED}:
            blocked_reasons.append("account_timestamp_invalid")
        elif stale and run_mode in {OperatingMode.DEMO_AUTO, OperatingMode.LIVE_GUARDED}:
            blocked_reasons.append("account_snapshot_stale")

    if nuwa_eval.block_trade:
        blocked_reasons.append("nuwa_block_trade")

    breakdown = compute_score(
        radar_signal,
        nuwa_eval,
        market_snapshot=market_snapshot,
        sentiment_snapshot=sentiment_snapshot,
        smartmoney_snapshot=smartmoney_snapshot,
        weights=cfg["scoring_weights"],
    )
    warnings.extend(breakdown.warnings)

    action = _score_to_action(breakdown.total_score, radar_signal.direction)
    if any("snapshot_stale" in w or "timestamp_invalid" in w for w in warnings):
        action = TradeAction.OBSERVE

    size_pct = 2.0 if action in {TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT} else 1.0
    if action == TradeAction.SMALL_PROBE:
        size_pct = 0.8
    leverage = 2.0

    pref = (nuwa_eval.preferred_action or "").lower()
    reason_codes = list(breakdown.reason_codes)
    if pref == "wait_pullback" and action in {TradeAction.OPEN_LONG, TradeAction.OPEN_SHORT, TradeAction.SMALL_PROBE}:
        action = TradeAction.PROPOSE
        size_pct = min(size_pct, 0.8)
        reason_codes.append("nuwa_wait_pullback")
    if pref == "observe":
        action = TradeAction.OBSERVE
    if pref == "block":
        blocked_reasons.append("nuwa_block_preferred")

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
    blocked_reasons.extend(risk.blocked_reasons)
    if blocked_reasons:
        action = TradeAction.BLOCKED

    preferred_execution = "demo_dry_run" if run_mode == OperatingMode.DEMO_AUTO else "dry_run"
    return TradeDecision(
        action=action,
        symbol=radar_signal.symbol,
        market_type=radar_signal.market_type,
        direction=radar_signal.direction,
        decision_id=f"dec_{uuid.uuid4().hex[:12]}",
        final_score=breakdown.total_score,
        confidence=round((nuwa_eval.confidence + radar_signal.score / 100) / 2, 4),
        risk_status="blocked" if blocked_reasons else risk.risk_status,
        reason_codes=sorted(set(reason_codes)),
        blocked_reasons=sorted(set(blocked_reasons)),
        warnings=sorted(set(warnings)),
        recommended_size_pct=risk.risk_adjusted_size_pct,
        recommended_leverage=min(leverage, float(cfg["risk_limits"].get("max_leverage", 3))),
        preferred_execution=preferred_execution,
        nuwa_version=nuwa_eval.version,
        mode=run_mode,
    )
