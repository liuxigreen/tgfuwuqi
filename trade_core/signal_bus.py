from __future__ import annotations

from dataclasses import fields
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


def _pick(cls, data: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in allowed}


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
        "nuwa_eval": NuwaEval(**_pick(NuwaEval, nuwa)),
    }
    if payload.get("market_snapshot"):
        ms = dict(payload["market_snapshot"])
        ms.setdefault("symbol", radar["symbol"])
        ms.setdefault("price", ms.get("last", 0) or 0)
        ms.setdefault("price_change_24h_pct", 0.0)
        ms.setdefault("volume_change_pct", 0.0)
        ms.setdefault("funding_rate", 0.0)
        ms.setdefault("open_interest_change_pct", 0.0)
        ms.setdefault("volatility_score", 0.5)
        ms.setdefault("liquidity_score", 0.5)
        ms.setdefault("timestamp", radar["timestamp"])
        out["market_snapshot"] = MarketSnapshot(**_pick(MarketSnapshot, ms))
    if payload.get("sentiment_snapshot"):
        ss = dict(payload["sentiment_snapshot"])
        ss.setdefault("symbol", radar["symbol"])
        ss.setdefault("sentiment_score", 0.5)
        ss.setdefault("sentiment_trend", "neutral")
        ss.setdefault("abnormal_sentiment_shift", False)
        ss.setdefault("news_risk", 0.5)
        ss.setdefault("timestamp", radar["timestamp"])
        out["sentiment_snapshot"] = SentimentSnapshot(**_pick(SentimentSnapshot, ss))
    if payload.get("smartmoney_snapshot"):
        sm = dict(payload["smartmoney_snapshot"])
        sm.setdefault("symbol", radar["symbol"])
        sm["consensus_direction"] = enum_from_value(Direction, sm.get("consensus_direction", sm.get("capital_weighted_direction")), Direction.UNKNOWN)
        sm["weighted_direction"] = enum_from_value(Direction, sm.get("weighted_direction", sm.get("capital_weighted_direction")), Direction.UNKNOWN)
        sm.setdefault("avg_win_rate", sm.get("average_win_rate", 0.5))
        sm.setdefault("long_short_ratio", sm.get("long_short_ratio", 1.0))
        sm.setdefault("smart_money_trend", sm.get("trend", "flat"))
        sm.setdefault("entry_vwap", sm.get("average_entry_price", 0.0))
        sm.setdefault("current_price", sm.get("current_price", 0.0))
        sm.setdefault("premium_discount_pct", 0.0)
        sm.setdefault("timestamp", radar["timestamp"])
        out["smartmoney_snapshot"] = SmartMoneySnapshot(**_pick(SmartMoneySnapshot, sm))
    if payload.get("account_snapshot"):
        ac = dict(payload["account_snapshot"])
        ac.setdefault("equity_usdt", 0.0)
        ac.setdefault("available_usdt", 0.0)
        ac.setdefault("daily_pnl_pct", 0.0)
        ac.setdefault("open_positions_count", 0)
        ac.setdefault("same_symbol_existing_position", False)
        ac.setdefault("total_exposure_pct", 0.0)
        ac.setdefault("max_position_exposure_pct", 0.0)
        ac.setdefault("timestamp", radar["timestamp"])
        ac["equity_usdt"] = ac.get("equity_usdt") if ac.get("equity_usdt") is not None else float(ac.get("total_equity") or 0.0)
        ac["available_usdt"] = ac.get("available_usdt") if ac.get("available_usdt") is not None else float(ac.get("available_equity") or 0.0)
        ac["daily_pnl_pct"] = float(ac.get("daily_pnl_pct") or 0.0)
        ac["open_positions_count"] = int(ac.get("open_positions_count") or 0)
        ac["same_symbol_existing_position"] = bool(ac.get("same_symbol_existing_position") or False)
        ac["total_exposure_pct"] = float(ac.get("total_exposure_pct") or 0.0)
        ac["max_position_exposure_pct"] = float(ac.get("max_position_exposure_pct") or 0.0)
        out["account_snapshot"] = AccountSnapshot(**_pick(AccountSnapshot, ac))
    out["mode"] = payload.get("mode", "propose")
    return out
