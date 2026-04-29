from __future__ import annotations

import time

from .experience_store import list_experiences


def _score(exp, context):
    s = 0.0
    if exp.get("symbol") == context.get("symbol"):
        s += 0.45
    if exp.get("market_type") == context.get("market_type"):
        s += 0.15
    if exp.get("direction") == context.get("direction"):
        s += 0.2
    ctags = set(context.get("tags", []))
    etags = set(exp.get("tags", []) + exp.get("technical_tags", []))
    if ctags and etags:
        s += min(0.2, len(ctags & etags) / max(1, len(ctags)))
    return round(s, 4)


def retrieve_similar_experiences(context, top_k=5, max_latency_ms=200, min_similarity=0.55):
    t0 = time.perf_counter()
    rows = list_experiences().get("experiences", [])
    scored = []
    for r in rows:
        if (time.perf_counter() - t0) * 1000 > max_latency_ms:
            return {"used": False, "timeout": True, "experiences": [], "experience_adjustments": {"score_adjustment": 0, "risk_adjustment": 0, "exit_policy_adjustment": None}, "low_confidence": True}
        sim = _score(r, context)
        if sim >= min_similarity:
            scored.append({"experience": r, "similarity_score": sim})
    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    top = scored[:top_k]
    adj = 0
    warn = []
    for item in top:
        o = item["experience"].get("outcome_label")
        if o in {"wrong", "risk_rule_allowed_bad_trade"}:
            adj -= 3
            warn.append("similar_failed_setup")
        if o in {"correct", "avoided_bad_trade"}:
            adj += 1
    return {
        "used": True,
        "timeout": False,
        "experiences": top,
        "apply_warning": sorted(set(warn)),
        "experience_adjustments": {"score_adjustment": max(-12, min(5, adj)), "risk_adjustment": -0.05 if adj < 0 else 0.0, "exit_policy_adjustment": "capital_protection" if adj < 0 else None},
        "low_confidence": len(top) < 2,
    }
