from __future__ import annotations

from typing import Any, Dict

from .decision import build_trade_decision
from .models import model_to_dict
from .order_intent import build_order_intent
from .signal_bus import parse_case_payload


def replay_case(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    parsed = parse_case_payload(payload)
    decision = build_trade_decision(
        radar_signal=parsed["radar_signal"],
        nuwa_eval=parsed["nuwa_eval"],
        market_snapshot=parsed.get("market_snapshot"),
        sentiment_snapshot=parsed.get("sentiment_snapshot"),
        smartmoney_snapshot=parsed.get("smartmoney_snapshot"),
        account_snapshot=parsed.get("account_snapshot"),
        mode=parsed.get("mode", "propose"),
        config=config,
    )
    intent = build_order_intent(decision, config=config)
    return {"decision": model_to_dict(decision), "order_intent": model_to_dict(intent)}
