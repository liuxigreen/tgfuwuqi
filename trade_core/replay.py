from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .config import load_config
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


def replay_journal(journal_path: str, nuwa_version: Optional[str] = None, scoring_weights: Optional[Dict[str, float]] = None, dry_run: bool = True) -> Dict[str, Any]:
    p = Path(journal_path)
    if not p.exists():
        return {"ok": False, "warning": "journal_not_found", "path": journal_path}
    events = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    decisions = [e for e in events if e.get("event_type") == "decision"]
    if not decisions:
        return {"ok": True, "warning": "no_decision_events", "changes": []}
    cfg = load_config()
    if scoring_weights:
        cfg["scoring_weights"].update(scoring_weights)
    changes = []
    for d in decisions:
        payload = d.get("payload", {})
        old_action = payload.get("action")
        old_score = payload.get("final_score")
        new_action = old_action
        new_score = old_score
        if nuwa_version:
            new_action = old_action
        changes.append({"old_action": old_action, "new_action": new_action, "old_score": old_score, "new_score": new_score, "changed_reason": "replay_placeholder"})
    return {"ok": True, "dry_run": dry_run, "changes": changes, "warnings": ["limited_replay_context"]}
