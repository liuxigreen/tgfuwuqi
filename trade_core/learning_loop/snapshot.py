from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ..journal import _sanitize, write_journal_event


def _unavailable(v):
    return v if v is not None else {"status": "unavailable"}


def create_decision_snapshot(pipeline_result: Dict[str, Any], sample: Dict[str, Any], pipeline_id: str | None = None) -> Dict[str, Any]:
    decision = pipeline_result.get("decision", pipeline_result)
    order_intent = pipeline_result.get("order_intent", {})
    radar = sample.get("radar_signal", {})
    snapshot = {
        "snapshot_id": f"snap_{uuid.uuid4().hex[:12]}",
        "decision_id": decision.get("decision_id", "unknown"),
        "pipeline_id": pipeline_id or pipeline_result.get("pipeline_id", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": decision.get("symbol", radar.get("symbol", "unknown")),
        "market_type": decision.get("market_type", radar.get("market_type", "swap")),
        "direction": decision.get("direction", radar.get("direction", "unknown")),
        "action": decision.get("action", pipeline_result.get("action", "observe")),
        "mode": pipeline_result.get("mode", decision.get("mode", "propose")),
        "horizon_minutes": 1440,
        "prediction_direction": decision.get("direction", radar.get("direction", "unknown")),
        "target_price": None,
        "stop_price": None,
        "entry_price": sample.get("market_snapshot", {}).get("price") if isinstance(sample.get("market_snapshot"), dict) else None,
        "confidence": float(decision.get("confidence", 0.5) or 0.5),
        "conviction_score": float(decision.get("final_score", 0.0) or 0.0),
        "score_breakdown": decision.get("score_breakdown", {}),
        "nuwa_version": decision.get("nuwa_version", "unknown"),
        "selected_recipe": pipeline_result.get("selected_recipe", "signal_confirmation_v1"),
        "selected_skills": pipeline_result.get("selected_skills", []),
        "exit_policy_id": order_intent.get("exit_policy_id") if isinstance(order_intent, dict) else None,
        "reason_codes": decision.get("reason_codes", []),
        "blocked_reasons": decision.get("blocked_reasons", []),
        "warnings": decision.get("warnings", []),
        "market_snapshot": _unavailable(sample.get("market_snapshot")),
        "oi_snapshot": _unavailable(sample.get("oi_snapshot")),
        "funding_snapshot": _unavailable(sample.get("funding_snapshot")),
        "account_snapshot": _unavailable(sample.get("account_snapshot")),
        "sentiment_snapshot": _unavailable(sample.get("sentiment_snapshot")),
        "smartmoney_snapshot": _unavailable(sample.get("smartmoney_snapshot")),
        "orderbook_snapshot": _unavailable(sample.get("orderbook_snapshot")),
        "technical_snapshot": _unavailable(sample.get("technical_snapshot")),
        "macro_snapshot": _unavailable(sample.get("macro_snapshot")),
        "fear_greed_snapshot": _unavailable(sample.get("fear_greed_snapshot")),
        "vix_snapshot": _unavailable(sample.get("vix_snapshot")),
        "polymarket_snapshot": _unavailable(sample.get("polymarket_snapshot")),
    }
    return _sanitize(snapshot)


def append_snapshot(snapshot: Dict[str, Any], date: str | None = None, base_dir: str = "data/decision_snapshots") -> str:
    d = date or datetime.now(timezone.utc).date().isoformat()
    p = Path(base_dir)
    p.mkdir(parents=True, exist_ok=True)
    out = p / f"{d}.snapshots.jsonl"
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    write_journal_event("decision_snapshot", snapshot.get("pipeline_id", "unknown"), snapshot.get("symbol", "unknown"), snapshot, snapshot.get("nuwa_version", "unknown"))
    return str(out)


def list_snapshots(date: str | None = None, base_dir: str = "data/decision_snapshots") -> List[Dict[str, Any]]:
    if date:
        files = [Path(base_dir) / f"{date}.snapshots.jsonl"]
    else:
        files = sorted(Path(base_dir).glob("*.snapshots.jsonl"))
    out: List[Dict[str, Any]] = []
    for f in files:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out
