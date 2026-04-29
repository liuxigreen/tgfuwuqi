from __future__ import annotations

from .models import ProposedExitPolicyChanges


def propose_exit_policy_changes(evaluations, config=None):
    items = evaluations.get("evaluations", [])
    if not items or any(x.get("insufficient_sample_size") for x in items):
        return ProposedExitPolicyChanges(True, True, True, []).__dict__
    changes = []
    for item in items:
        if (item.get("profit_factor") or 0) < 1.2:
            changes.append({"type": "exit_policy_adjustment", "target": item.get("policy_id"), "reason": "low_profit_factor", "requires_human_approval": True, "safe_to_auto_apply": False})
    return ProposedExitPolicyChanges(True, True, False, changes).__dict__
