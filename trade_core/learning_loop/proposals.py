from __future__ import annotations


def build_learning_proposals(review_report, calibration_report):
    changes = []
    if calibration_report.get("ok") and calibration_report.get("overconfidence_rate", 0) > 0.2:
        changes.append({
            "type": "risk_threshold_adjustment",
            "target": "min_confidence_for_demo_auto",
            "old_value": 0.65,
            "new_value": 0.7,
            "reason": "overconfidence_detected",
            "evidence": {"calibration": calibration_report},
            "sample_size": calibration_report.get("sample_size", 0),
            "confidence": 0.6,
            "expected_effect": "reduce_false_positives",
            "risk": "missed_opportunities",
            "requires_human_approval": True,
            "safe_to_auto_apply": False,
        })
    return {"proposed_changes": changes, "requires_human_approval": True, "safe_to_auto_apply": False}
