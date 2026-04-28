from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def build_proposal(date: str, review: Dict) -> Dict:
    return {
        "date": date,
        "proposal_id": f"prop_{uuid.uuid4().hex[:12]}",
        "changes": [
            {
                "type": "scoring_weight_adjustment",
                "target": "smart_money_score",
                "old": 0.20,
                "new": 0.22,
                "reason": "demo observations suggest smartmoney useful",
                "confidence": 0.6,
                "safe_to_auto_apply": False,
            }
        ],
        "recommended_weight_changes": {"smart_money_score": 0.22},
        "recommended_threshold_changes": {},
        "recommended_disabled_recipes": [],
        "recommended_enabled_recipes_for_propose_only": [],
        "recommended_nuwa_promotions": [],
        "recommended_nuwa_demotions": [],
        "risk_warnings": ["Do not enable live automatically."],
        "forbidden_auto_changes": ["enable_live", "increase_leverage", "increase_max_daily_loss"],
        "requires_human_approval": True,
    }


def save_proposal(date: str, proposal: Dict, base='data/self_evolution') -> str:
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    out = p / f"{date}.proposed_changes.json"
    out.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(out)
