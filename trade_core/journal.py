from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SENSITIVE_KEYS = {"api_key", "secret", "passphrase", "private_key", "token", "credential", "password", "auth"}


def _sanitize(value: Any, key_hint: str = "") -> Any:
    key_low = key_hint.lower()
    if any(s in key_low for s in SENSITIVE_KEYS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: _sanitize(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v, key_hint) for v in value]
    return value


def write_journal_event(event_type: str, pipeline_id: str, symbol: str, payload: Dict[str, Any], nuwa_version: str = "unknown", decision_version: str = "trade_core_v1_3", base_dir: str = "data/trade_core_journal") -> str:
    now = datetime.now(timezone.utc)
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    journal = path / f"{now.date().isoformat()}.trade_core.jsonl"
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "timestamp": now.isoformat(),
        "event_type": event_type,
        "pipeline_id": pipeline_id,
        "symbol": symbol,
        "nuwa_version": nuwa_version,
        "decision_version": decision_version,
        "payload": _sanitize(payload),
    }
    with journal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return str(journal)


def _load_events(journal_path: str) -> List[Dict[str, Any]]:
    p = Path(journal_path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def review_journal(journal_path: str) -> Dict[str, Any]:
    events = _load_events(journal_path)
    if not events:
        return {"ok": False, "error": "journal_not_found_or_empty", "path": journal_path}

    decisions = [e for e in events if e.get("event_type") == "decision"]
    blocked = [d for d in decisions if d.get("payload", {}).get("risk_status") == "blocked"]
    actions = Counter([d.get("payload", {}).get("action", "unknown") for d in decisions])
    symbols = Counter([d.get("symbol", "unknown") for d in decisions])
    blocked_reasons = Counter([r for d in decisions for r in d.get("payload", {}).get("blocked_reasons", [])])

    def avg(key: str):
        vals = [float(d.get("payload", {}).get("score_breakdown", {}).get(key, 0)) for d in decisions]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    missing_adapter_count = sum(len(d.get("payload", {}).get("score_breakdown", {}).get("missing_inputs", [])) for d in decisions)
    return {
        "ok": True,
        "path": journal_path,
        "total_decisions": len(decisions),
        "blocked_count": len(blocked),
        "observe_count": actions.get("observe", 0),
        "small_probe_count": actions.get("small_probe", 0),
        "demo_execution_count": len([e for e in events if e.get("event_type") == "execution_result" and e.get("payload", {}).get("executed")]),
        "top_blocked_reasons": blocked_reasons.most_common(5),
        "top_symbols": symbols.most_common(5),
        "avg_total_score": avg("total_score"),
        "avg_nuwa_score": avg("nuwa_score"),
        "avg_smartmoney_score": avg("smart_money_score"),
        "avg_sentiment_score": avg("sentiment_score"),
        "missing_adapter_count": missing_adapter_count,
        "warnings": ["review_generated_from_journal"],
        "recommendations": ["Keep live execution disabled by default."],
    }
