from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

STORE = Path("data/experience_store/experiences.jsonl")


def _load():
    if not STORE.exists():
        return []
    return [json.loads(x) for x in STORE.read_text(encoding="utf-8").splitlines() if x.strip()]


def _save(rec):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def add_experience_from_review(review: dict):
    if not review.get("should_update_experience_store"):
        return {"ok": False, "warning": "review_not_eligible"}
    rec = {
        "experience_id": f"exp_{uuid.uuid4().hex[:12]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_id": review.get("snapshot_id"),
        "source_outcome_id": review.get("outcome_id"),
        "source_review_id": review.get("review_id"),
        "symbol": review.get("symbol", "unknown"),
        "market_type": review.get("market_type", "swap"),
        "direction": review.get("direction", "unknown"),
        "market_regime": review.get("market_regime", "unknown"),
        "signal_archetype": review.get("signal_archetype", "unknown"),
        "technical_tags": review.get("technical_tags", []),
        "macro_tags": review.get("macro_tags", []),
        "sentiment_tags": review.get("sentiment_tags", []),
        "smartmoney_tags": review.get("smartmoney_tags", []),
        "oi_funding_tags": review.get("oi_funding_tags", []),
        "polymarket_tags": review.get("polymarket_tags", []),
        "outcome_label": review.get("outcome_label", "inconclusive"),
        "lesson": review.get("lesson", "no_lesson"),
        "rule_hint": review.get("rule_suggestion", "none"),
        "when_to_apply": review.get("when_to_apply", "similar setup"),
        "when_not_to_apply": review.get("when_not_to_apply", "regime mismatch"),
        "confidence": review.get("confidence", 0.5),
        "sample_count": 1,
        "evidence": {
            "snapshot_id": review.get("snapshot_id"),
            "outcome_id": review.get("outcome_id"),
            "review_id": review.get("review_id"),
        },
        "nuwa_version": review.get("nuwa_version", "unknown"),
        "tags": review.get("tags", []),
        "trusted": False,
        "historical_simulation": bool(review.get("historical_simulation", False)),
    }
    if not rec["evidence"]["snapshot_id"]:
        return {"ok": False, "warning": "min_evidence_required"}
    _save(rec)
    return {"ok": True, "experience": rec}


def list_experiences():
    rows = _load()
    return {"ok": True, "count": len(rows), "experiences": rows}


def search_experiences(symbol=None, tags=None):
    rows = _load()
    tags = [x.strip() for x in (tags or []) if x.strip()]
    out = []
    for r in rows:
        if symbol and r.get("symbol") != symbol:
            continue
        if tags and not any(t in set(r.get("tags", []) + r.get("technical_tags", [])) for t in tags):
            continue
        out.append(r)
    return {"ok": True, "count": len(out), "experiences": out}
