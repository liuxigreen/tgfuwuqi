from __future__ import annotations


def validate_proposal(proposal: dict) -> dict:
    forbidden = ['enable_live', 'increase_leverage', 'increase_max_daily_loss']
    payload = str(proposal).lower()
    violated = [k for k in forbidden if k in payload]
    return {"ok": not violated, "violations": violated, "requires_human_approval": True}
