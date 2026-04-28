from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import Direction, MarketSnapshot, NuwaEval, RadarSignal, SentimentSnapshot, SmartMoneySnapshot


@dataclass
class ScoreBreakdown:
    total_score: float
    market_score: float
    oi_score: float
    funding_score: float
    sentiment_score: float
    smart_money_score: float
    nuwa_score: float
    risk_penalty: float
    warnings: List[str] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)


DEFAULT_WEIGHTS = {
    "market_score": 0.15,
    "oi_score": 0.20,
    "funding_score": 0.10,
    "sentiment_score": 0.15,
    "smart_money_score": 0.20,
    "nuwa_score": 0.20,
    "risk_penalty": 0.20,
}


def compute_score(
    radar_signal: RadarSignal,
    nuwa_eval: NuwaEval,
    market_snapshot: Optional[MarketSnapshot] = None,
    sentiment_snapshot: Optional[SentimentSnapshot] = None,
    smartmoney_snapshot: Optional[SmartMoneySnapshot] = None,
    weights: Optional[Dict[str, float]] = None,
) -> ScoreBreakdown:
    if nuwa_eval.block_trade:
        return ScoreBreakdown(0, 0, 0, 0, 0, 0, 0, 100, reason_codes=["nuwa_block_trade"])

    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    reason_codes: List[str] = []
    warnings: List[str] = []

    market_score = 55.0
    oi_score = min(100.0, max(0.0, radar_signal.score))
    funding_score = 55.0
    risk_penalty = 0.0

    if market_snapshot:
        if market_snapshot.price_change_24h_pct > 0:
            market_score += 15
            reason_codes.append("price_trend_positive")
        if market_snapshot.open_interest_change_pct > 0:
            oi_score = min(100.0, oi_score + 12)
            reason_codes.append("oi_growth")
        if market_snapshot.open_interest_change_pct > 0 and abs(market_snapshot.price_change_24h_pct) < 1.0:
            market_score += 5
            reason_codes.append("oi_building_wait")
        if abs(market_snapshot.funding_rate) > 0.0008:
            funding_score -= 20
            risk_penalty += 10
            reason_codes.append("funding_extreme_crowding")
    else:
        warnings.append("market_snapshot_missing")

    sentiment_score = 55.0
    if sentiment_snapshot:
        if radar_signal.direction == Direction.LONG and sentiment_snapshot.sentiment_trend in {"up", "bullish"}:
            sentiment_score += 20
            reason_codes.append("sentiment_aligned")
        elif radar_signal.direction == Direction.SHORT and sentiment_snapshot.sentiment_trend in {"down", "bearish"}:
            sentiment_score += 20
            reason_codes.append("sentiment_aligned")
        else:
            sentiment_score -= 20
            reason_codes.append("sentiment_diverged")
        if sentiment_snapshot.abnormal_sentiment_shift:
            risk_penalty += 8
            reason_codes.append("sentiment_abnormal_shift")
        risk_penalty += sentiment_snapshot.news_risk * 5
    else:
        warnings.append("sentiment_snapshot_missing")

    smart_money_score = 55.0
    if smartmoney_snapshot:
        if smartmoney_snapshot.weighted_direction == radar_signal.direction:
            smart_money_score += 20
            reason_codes.append("smartmoney_aligned")
        elif smartmoney_snapshot.weighted_direction != Direction.UNKNOWN:
            smart_money_score -= 22
            risk_penalty += 10
            reason_codes.append("smartmoney_diverged")
        if smartmoney_snapshot.premium_discount_pct > 1.0:
            smart_money_score -= 15
            risk_penalty += 5
            reason_codes.append("premium_too_high_wait_pullback")
    else:
        warnings.append("smartmoney_snapshot_missing")

    nuwa_score = min(100.0, max(0.0, 50 + nuwa_eval.continuation_probability * 35 - nuwa_eval.manipulation_risk * 30))

    total = (
        market_score * w["market_score"]
        + oi_score * w["oi_score"]
        + funding_score * w["funding_score"]
        + sentiment_score * w["sentiment_score"]
        + smart_money_score * w["smart_money_score"]
        + nuwa_score * w["nuwa_score"]
        - risk_penalty * w["risk_penalty"]
    )
    total = max(0.0, min(100.0, total))

    return ScoreBreakdown(
        total_score=round(total, 2),
        market_score=round(market_score, 2),
        oi_score=round(oi_score, 2),
        funding_score=round(funding_score, 2),
        sentiment_score=round(sentiment_score, 2),
        smart_money_score=round(smart_money_score, 2),
        nuwa_score=round(nuwa_score, 2),
        risk_penalty=round(risk_penalty, 2),
        warnings=warnings,
        reason_codes=sorted(set(reason_codes)),
    )
