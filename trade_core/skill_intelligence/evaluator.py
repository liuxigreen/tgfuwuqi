from __future__ import annotations


def evaluate_skills(registry):
    scored = []
    for s in registry.get("skills", []):
        scored.append({**s, "safety_score": 0.9 if not s.get("can_execute_trade") else 0.5, "execution_risk_score": 0.9 if s.get("can_execute_trade") else 0.2})
    return {"skills": scored, "slow_path_only": True}
