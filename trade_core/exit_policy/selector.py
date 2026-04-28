from __future__ import annotations

from .templates import get_template


def select_exit_policy(decision, nuwa_eval, market_snapshot=None, smartmoney_snapshot=None, sentiment_snapshot=None, risk_state=None, config=None):
    archetype = (getattr(nuwa_eval, "signal_archetype", "") or "").lower()
    conf = float(getattr(nuwa_eval, "confidence", 0.5) or 0.5)
    manip = float(getattr(nuwa_eval, "manipulation_risk", 0.5) or 0.5)
    if conf < 0.65 or manip > 0.7:
        return get_template("capital_protection", config)
    if "event" in archetype or "news" in archetype:
        return get_template("event_driven_fast", config)
    if "reversal" in archetype or "overcrowd" in archetype:
        return get_template("mean_reversion_probe", config)
    if "accumulation" in archetype or "breakout" in archetype:
        return get_template("accumulation_breakout", config)
    return get_template("trend_following_default", config)
