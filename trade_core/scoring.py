from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .models import Direction, MarketSnapshot, NuwaEval, RadarSignal, SentimentSnapshot, SmartMoneySnapshot


@dataclass
class ScoreBreakdown:
    total_score: float
    radar_score: float
    market_confirmation_score: float
    sentiment_score: float
    smart_money_score: float
    nuwa_score: float
    risk_penalty: float
    reason_codes: List[str] = field(default_factory=list)


def _dir_match(lhs: Direction, rhs: Direction) -> bool:
    return lhs != Direction.UNKNOWN and lhs == rhs


def compute_score(
    radar_signal: RadarSignal,
    nuwa_eval: NuwaEval,
    market_snapshot: Optional[MarketSnapshot] = None,
    sentiment_snapshot: Optional[SentimentSnapshot] = None,
    smartmoney_snapshot: Optional[SmartMoneySnapshot] = None,
    weights: Optional[dict] = None,
) -> ScoreBreakdown:
    if nuwa_eval.block_trade:
        return ScoreBreakdown(0, 0, 0, 0, 0, 0, 100, ["nuwa_block_trade"])

    w = weights or {"radar": 0.25, "market": 0.20, "sentiment": 0.15, "smartmoney": 0.20, "nuwa": 0.20}
    reasons: List[str] = []

    radar_base = max(0.0, min(100.0, radar_signal.score))

    market = 50.0
    risk_penalty = 0.0
    if market_snapshot:
        if market_snapshot.open_interest_change_pct > 0 and market_snapshot.price_change_24h_pct > 0:
            market += 25
            reasons.append("market_oi_price_resonance")
        elif market_snapshot.open_interest_change_pct > 0 and abs(market_snapshot.price_change_24h_pct) < 1.0:
            market += 10
            reasons.append("market_oi_building_wait")
        if abs(market_snapshot.funding_rate) >= 0.0008:
            risk_penalty += 8
            reasons.append("funding_extreme_crowding")
        market = max(0.0, min(100.0, market))

    sentiment = 50.0
    if sentiment_snapshot:
        if radar_signal.direction == Direction.LONG and sentiment_snapshot.sentiment_trend in {"up", "bullish"}:
            sentiment += 25
            reasons.append("sentiment_direction_match")
        elif radar_signal.direction == Direction.SHORT and sentiment_snapshot.sentiment_trend in {"down", "bearish"}:
            sentiment += 25
            reasons.append("sentiment_direction_match")
        else:
            sentiment -= 20
            reasons.append("sentiment_direction_diverge")
        if sentiment_snapshot.abnormal_sentiment_shift:
            sentiment -= 10
            reasons.append("sentiment_abnormal_shift")
        sentiment -= sentiment_snapshot.news_risk * 20
        sentiment = max(0.0, min(100.0, sentiment))

    smart = 50.0
    if smartmoney_snapshot:
        if _dir_match(smartmoney_snapshot.weighted_direction, radar_signal.direction):
            smart += 25
            reasons.append("smartmoney_direction_match")
        elif smartmoney_snapshot.weighted_direction != Direction.UNKNOWN:
            smart -= 25
            reasons.append("smartmoney_direction_diverge")
        if smartmoney_snapshot.premium_discount_pct > 1.0:
            smart -= 18
            reasons.append("smartmoney_premium_too_high")
        if smartmoney_snapshot.smart_money_trend in {"distribute", "reversal"}:
            smart -= 10
            reasons.append("smartmoney_reversal_risk")
        smart = max(0.0, min(100.0, smart))

    nuwa = 50.0
    nuwa += nuwa_eval.continuation_probability * 35
    nuwa -= nuwa_eval.manipulation_risk * 40
    nuwa += nuwa_eval.signal_quality * 10
    nuwa = max(0.0, min(100.0, nuwa))
    if nuwa_eval.manipulation_risk > 0.6:
        reasons.append("nuwa_high_manipulation_risk")
    if nuwa_eval.continuation_probability >= 0.7:
        reasons.append("nuwa_high_continuation")

    total = (
        radar_base * w["radar"]
        + market * w["market"]
        + sentiment * w["sentiment"]
        + smart * w["smartmoney"]
        + nuwa * w["nuwa"]
        - risk_penalty
    )
    total = max(0.0, min(100.0, total))

    return ScoreBreakdown(
        total_score=round(total, 2),
        radar_score=round(radar_base, 2),
        market_confirmation_score=round(market, 2),
        sentiment_score=round(sentiment, 2),
        smart_money_score=round(smart, 2),
        nuwa_score=round(nuwa, 2),
        risk_penalty=round(risk_penalty, 2),
        reason_codes=sorted(set(reasons)),
    )
