from __future__ import annotations


def classify_skill(skill):
    sid = skill.get("skill_id", "")
    if "trade" in sid:
        return "execution"
    if "market" in sid or "smartmoney" in sid:
        return "decision_support"
    return "secondary"
