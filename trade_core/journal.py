from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False)
    for token in ["api_key", "secret", "passphrase", "private_key"]:
        text = text.replace(token, f"{token}_redacted")
    return json.loads(text)


def write_journal_event(
    event_type: str,
    pipeline_id: str,
    symbol: str,
    payload: Dict[str, Any],
    nuwa_version: str = "unknown",
    decision_version: str = "trade_core_v1_2",
    base_dir: str = "data/trade_core_journal",
) -> str:
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


def review_journal(journal_path: str) -> Dict[str, Any]:
    p = Path(journal_path)
    events: List[Dict[str, Any]] = []
    if not p.exists():
        return {"ok": False, "error": "journal_not_found", "path": journal_path}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    blocked = [e for e in events if "blocked" in json.dumps(e.get("payload", {})).lower()]
    return {"ok": True, "path": journal_path, "count": len(events), "blocked_count": len(blocked), "event_types": sorted({e["event_type"] for e in events})}
