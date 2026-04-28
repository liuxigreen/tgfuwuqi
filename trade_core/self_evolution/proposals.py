from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict

from ..learning_loop.proposals import build_learning_proposals


def build_proposal(date: str, review: Dict) -> Dict:
    learning = build_learning_proposals(review, {"ok": True, "overconfidence_rate": float(review.get("overconfidence_rate", 0) or 0), "sample_size": int(review.get("outcome_count", 0) or 0)})
    base_changes = [
        {
            "type": "scoring_weight_adjustment",
            "target": "smart_money_score",
            "old_value": 0.20,
            "new_value": 0.22,
            "reason": "demo observations suggest smartmoney useful",
            "evidence": {"snapshot_id": None, "outcome_id": None, "review_id": None, "experience_id": None},
            "sample_size": int(review.get("outcome_count", 0) or 0),
            "confidence": 0.6,
            "expected_effect": "slightly_better_filtering",
            "risk": "overfit",
            "requires_human_approval": True,
            "safe_to_auto_apply": False,
        }
    ]
    return {
        "date": date,
        "proposal_id": f"prop_{uuid.uuid4().hex[:12]}",
        "changes": base_changes + learning.get("proposed_changes", []),
        "recommended_weight_changes": {"smart_money_score": 0.22},
        "recommended_threshold_changes": {},
        "recommended_disabled_recipes": [],
        "recommended_enabled_recipes_for_propose_only": [],
        "recommended_nuwa_promotions": [],
        "recommended_nuwa_demotions": [],
        "risk_warnings": ["Do not enable live automatically."],
        "forbidden_auto_changes": ["enable_live", "increase_leverage", "increase_max_daily_loss"],
        "requires_human_approval": True,
        "safe_to_auto_apply": False,
    }


def save_proposal(date: str, proposal: Dict, base='data/self_evolution') -> str:
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    out = p / f"{date}.proposed_changes.json"
    out.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(out)
