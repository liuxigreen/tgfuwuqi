from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..journal import write_journal_event


def review_outcomes(date: str, outcomes_path: str | None = None):
    path = Path(outcomes_path) if outcomes_path else Path("data/outcomes") / f"{date}.outcomes.jsonl"
    if not path.exists():
        return {"ok": False, "warning": "data_unavailable", "reviews": []}
    reviews = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        if o.get("correctness_label") not in {"wrong", "partially_correct", "missed_good_trade", "avoided_bad_trade"}:
            continue
        r = {
            "review_id": f"rev_{uuid.uuid4().hex[:12]}",
            "snapshot_id": o.get("snapshot_id"),
            "outcome_id": o.get("outcome_id"),
            "root_cause": o.get("error_type", "unknown"),
            "failed_signal": o.get("error_type", "unknown"),
            "ignored_signal": "unavailable",
            "misleading_signal": "unknown",
            "lesson": "Prefer conservative sizing in similar setup",
            "rule_suggestion": "tighten_entry_filter",
            "threshold_suggestion": "raise_min_confidence",
            "exit_policy_suggestion": "capital_protection",
            "tags": [o.get("error_type", "unknown")],
            "confidence": 0.55,
            "should_update_experience_store": True,
            "requires_human_approval": True,
        }
        reviews.append(r)
        write_journal_event("ai_review", "learning_loop", "unknown", r, "nuwa_default_v1")
    return {"ok": True, "date": date, "reviews": reviews, "warning": "mock_structured_reviewer" if not reviews else None}
