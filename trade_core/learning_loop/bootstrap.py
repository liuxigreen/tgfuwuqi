from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def bootstrap_experiences(sample_path: str):
    data = json.loads(Path(sample_path).read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    out = []
    for n in nodes:
        out.append({
            "candidate_id": f"hxp_{uuid.uuid4().hex[:12]}",
            "historical_simulation": True,
            "trusted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "symbol": n.get("symbol", "unknown"),
            "market_regime": n.get("market_regime", "unknown"),
            "lesson": n.get("lesson", "historical_observation"),
            "confidence": 0.35,
            "requires_human_approval": True,
        })
    return {"ok": True, "historical_simulation": True, "candidates": out}
