from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict

from ..learning_loop.proposals import build_learning_proposals


def build_proposal(date: str, review: Dict) -> Dict:
    sample_size = int(review.get("outcome_count", 0) or 0)
    insufficient = sample_size < 10
    learning = build_learning_proposals(
        review,
        {
            "ok": True,
            "overconfidence_rate": float(review.get("overconfidence_rate", 0) or 0),
            "sample_size": sample_size,
        },
    )
    changes = []
    if not insufficient:
        changes.extend(learning.get("proposed_changes", []))

    if not changes:
        changes.append(
            {
                "type": "no_change",
                "target": "scoring_and_risk",
                "old_value": None,
                "new_value": None,
                "reason": "insufficient_sample_size" if insufficient else "no_actionable_signal",
                "evidence": {
                    "snapshot_id": None,
                    "outcome_id": None,
                    "review_id": None,
                    "experience_id": None,
                },
                "sample_size": sample_size,
                "confidence": 0.0,
                "expected_effect": "none",
                "risk": "none",
                "requires_human_approval": True,
                "safe_to_auto_apply": False,
            }
        )

    return {
        "date": date,
        "proposal_id": f"prop_{uuid.uuid4().hex[:12]}",
        "changes": changes,
        "recommended_weight_changes": {},
        "recommended_threshold_changes": {},
        "recommended_disabled_recipes": [],
        "recommended_enabled_recipes_for_propose_only": [],
        "recommended_nuwa_promotions": [],
        "recommended_nuwa_demotions": [],
        "risk_warnings": ["Do not enable live automatically."],
        "forbidden_auto_changes": ["enable_live", "increase_leverage", "increase_max_daily_loss"],
        "requires_human_approval": True,
        "safe_to_auto_apply": False,
        "insufficient_sample_size": insufficient,
    }


def save_proposal(date: str, proposal: Dict, base='data/self_evolution') -> str:
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    out = p / f"{date}.proposed_changes.json"
    out.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(out)
