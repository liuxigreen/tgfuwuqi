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
        if ticker.get("error"):
            warnings.append(f"ticker_unavailable:{symbol}")
        sentiment = gateway.get_coin_sentiment(symbol)
        smart = gateway.get_smartmoney_overview(symbol)
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
            "suggested_action": "small_probe" if mode != "observe" else "observe",
            "reason_codes": ["scout_v1"],
            "adapter_status": {
                "sentiment": sentiment.get("adapter_status", "ok"),
                "smartmoney": smart.get("adapter_status", "ok"),
            },
        }
        candidates.append(candidate)
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "mode": mode, "candidates": candidates, "warnings": warnings}
