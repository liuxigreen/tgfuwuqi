from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..journal import write_journal_event
from .snapshot import list_snapshots


def _parse_horizon(h):
    h = (h or "24h").lower()
    if h.endswith("h"):
        return int(h[:-1]) * 60
    return int(h)


def _bucket(conf: float) -> str:
    for lo in [0.5, 0.6, 0.7, 0.8, 0.9]:
        hi = lo + 0.1
        if lo <= conf < hi or (lo == 0.9 and conf <= 1.0):
            return f"{lo:.1f}-{hi:.1f}"
    return "unknown"


def evaluate_outcomes(horizon="24h", date=None, snapshots=None, outcomes_dir="data/outcomes"):
    horizon_m = _parse_horizon(horizon)
    snaps = snapshots if snapshots is not None else list_snapshots(date=date)
    if not snaps:
        return {"ok": False, "warning": "data_unavailable", "outcomes": []}
    out = []
    for s in snaps:
        entry = s.get("entry_price")
        current = s.get("market_snapshot", {}).get("price") if isinstance(s.get("market_snapshot"), dict) else None
        conf = float(s.get("confidence", 0.5) or 0.5)
        if entry is None or current is None:
            row = {
                "outcome_id": f"out_{uuid.uuid4().hex[:12]}",
                "snapshot_id": s.get("snapshot_id"),
                "decision_id": s.get("decision_id"),
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "horizon_minutes": horizon_m,
                "entry_price": entry,
                "price_at_horizon": None,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
                "target_hit": None,
                "stop_hit": None,
                "direction_correct": None,
                "pnl_pct": None,
                "pnl_usdt": None,
                "R_multiple": None,
                "thesis_status": "inconclusive",
                "exit_reason": "data_unavailable",
                "correctness_label": "data_unavailable",
                "error_type": "unknown",
                "missing_data": ["price_at_horizon"],
                "confidence_at_entry": conf,
                "calibration_bucket": _bucket(conf),
            }
        else:
            pnl = (float(current) - float(entry)) / float(entry) if entry else 0.0
            direction = s.get("direction")
            correct = (pnl > 0 and direction == "long") or (pnl < 0 and direction == "short")
            row = {
                "outcome_id": f"out_{uuid.uuid4().hex[:12]}",
                "snapshot_id": s.get("snapshot_id"),
                "decision_id": s.get("decision_id"),
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "horizon_minutes": horizon_m,
                "entry_price": entry,
                "price_at_horizon": current,
                "max_favorable_excursion_pct": None,
                "max_adverse_excursion_pct": None,
                "target_hit": None,
                "stop_hit": None,
                "direction_correct": bool(correct),
                "pnl_pct": pnl,
                "pnl_usdt": None,
                "R_multiple": None,
                "thesis_status": "valid" if correct else "invalidated",
                "exit_reason": "horizon_reached",
                "correctness_label": "correct" if correct else "wrong",
                "error_type": "unknown" if correct else "thesis_invalidated",
                "missing_data": [],
                "confidence_at_entry": conf,
                "calibration_bucket": _bucket(conf),
            }
        out.append(row)
        write_journal_event("outcome_evaluation", s.get("pipeline_id", "unknown"), s.get("symbol", "unknown"), row, s.get("nuwa_version", "unknown"))

    d = date or datetime.now(timezone.utc).date().isoformat()
    p = Path(outcomes_dir)
    p.mkdir(parents=True, exist_ok=True)
    file = p / f"{d}.outcomes.jsonl"
    with file.open("a", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, "outcomes": out, "path": str(file)}
