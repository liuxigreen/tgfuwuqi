from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .models import Direction
from .okx_gateway import OkxGateway


def run_scout(symbols: List[str], mode: str, gateway: OkxGateway) -> Dict[str, Any]:
    candidates = []
    warnings = []
    for symbol in symbols:
        ticker = gateway.get_ticker(symbol)
        sentiment = gateway.get_coin_sentiment(symbol)
        smart = gateway.get_smartmoney_overview(symbol)
        missing = []
        if sentiment.get("error"):
            missing.append("sentiment")
            warnings.append(f"sentiment_adapter_missing:{symbol}")
        if smart.get("error"):
            missing.append("smartmoney")
            warnings.append(f"smartmoney_adapter_missing:{symbol}")
        is_mock = bool(ticker.get("is_mock", gateway.backend != "cli"))
        candidate = {
            "symbol": symbol,
            "market_type": "swap" if symbol.endswith("SWAP") else "spot",
            "direction": Direction.LONG.value,
            "market_score": 65,
            "oi_score": 68,
            "funding_score": 55,
            "sentiment_score": 60,
            "smart_money_score": 62,
            "nuwa_score": 58,
            "risk_penalty": 12,
            "total_score": 63,
            "suggested_action": "observe" if mode == "observe" or mode == "demo_auto" else "small_probe",
            "reason_codes": ["scout_mock_scores"],
            "data_quality": "low" if is_mock else "medium",
            "adapter_status": {"market": "mock" if is_mock else "cli", "sentiment": sentiment.get("error", "ok"), "smartmoney": smart.get("error", "ok")},
            "is_mock": is_mock,
            "missing_adapters": missing,
        }
        candidates.append(candidate)
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "mode": mode, "is_mock": gateway.backend != "cli", "candidates": candidates, "warnings": warnings}
