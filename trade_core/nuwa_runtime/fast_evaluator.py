from __future__ import annotations

from datetime import datetime, timezone


def run_fast_nuwa(sample: dict, timeout_ms: int = 800):
    if sample.get('simulate_nuwa_timeout'):
        return {"signal_quality": 50, "continuation_probability": 0.5, "manipulation_risk": 0.5, "preferred_action": "observe", "confidence": 0.5, "block_trade": False, "reason_codes": ["nuwa_fast_timeout"], "nuwa_mode": "fast_default", "timestamp": datetime.now(timezone.utc).isoformat()}
    if sample.get('nuwa_eval'):
        e=sample['nuwa_eval']
        return {"signal_quality": e.get('signal_quality',50), "continuation_probability": e.get('continuation_probability',0.5), "manipulation_risk": e.get('manipulation_risk',0.5), "preferred_action": e.get('preferred_action','observe'), "confidence": e.get('confidence',0.5), "block_trade": e.get('block_trade',False), "reason_codes": ["nuwa_fast_structured"], "nuwa_mode": "fast", "timestamp": datetime.now(timezone.utc).isoformat()}
    return {"signal_quality": 50, "continuation_probability": 0.5, "manipulation_risk": 0.5, "preferred_action": "observe", "confidence": 0.5, "block_trade": False, "reason_codes": ["nuwa_fast_default"], "nuwa_mode": "fast_default", "timestamp": datetime.now(timezone.utc).isoformat()}
