from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

FB = Path("data/feedback/feedback.jsonl")


def add_feedback(decision_id: str, feedback_type: str, message: str, source: str = "operator", symbol: str = "unknown"):
    rec = {
        "feedback_id": f"fb_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "symbol": symbol,
        "decision_id": decision_id,
        "feedback_type": feedback_type,
        "current_rule": "unknown",
        "complaint": message,
        "proposed_change": None,
        "actual_outcome_later": None,
        "evidence": [],
        "status": "pending_outcome_support",
    }
    FB.parent.mkdir(parents=True, exist_ok=True)
    with FB.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True, "feedback": rec}


def review_feedback(date: str):
    if not FB.exists():
        return {"ok": False, "warning": "data_unavailable", "feedback": []}
    rows = [json.loads(x) for x in FB.read_text(encoding="utf-8").splitlines() if x.strip() and x.find(date) >= 0]
    supported = [r for r in rows if r.get("actual_outcome_later")]
    return {"ok": True, "date": date, "feedback_count": len(rows), "feedback_supported_count": len(supported), "feedback_rejected_count": len(rows) - len(supported), "feedback": rows}
