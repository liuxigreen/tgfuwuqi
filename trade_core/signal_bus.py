from __future__ import annotations

from typing import Any, Dict

from .models import (
    AccountSnapshot,
    Direction,
    MarketSnapshot,
    NuwaEval,
    RadarSignal,
    SentimentSnapshot,
    SmartMoneySnapshot,
    enum_from_value,
)


def parse_case_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    radar = payload["radar_signal"]
    nuwa = payload["nuwa_eval"]
    out = {
        "radar_signal": RadarSignal(
            symbol=radar["symbol"],
            market_type=radar["market_type"],
            direction=enum_from_value(Direction, radar.get("direction"), Direction.UNKNOWN),
            score=float(radar["score"]),
            source=radar.get("source", "unknown"),
            timestamp=radar["timestamp"],
            features=radar.get("features", {}),
        ),
        "nuwa_eval": NuwaEval(**nuwa),
    }
    if payload.get("market_snapshot"):
        out["market_snapshot"] = MarketSnapshot(**payload["market_snapshot"])
    if payload.get("sentiment_snapshot"):
        out["sentiment_snapshot"] = SentimentSnapshot(**payload["sentiment_snapshot"])
    if payload.get("smartmoney_snapshot"):
        sm = dict(payload["smartmoney_snapshot"])
        sm["consensus_direction"] = enum_from_value(Direction, sm.get("consensus_direction"), Direction.UNKNOWN)
        sm["weighted_direction"] = enum_from_value(Direction, sm.get("weighted_direction"), Direction.UNKNOWN)
        out["smartmoney_snapshot"] = SmartMoneySnapshot(**sm)
    if payload.get("account_snapshot"):
        out["account_snapshot"] = AccountSnapshot(**payload["account_snapshot"])
    out["mode"] = payload.get("mode", "propose")
    return out
