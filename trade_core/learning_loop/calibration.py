from __future__ import annotations


def calibration_review(outcomes, min_samples: int = 10):
    if not outcomes:
        return {"ok": False, "warning": "data_unavailable", "low_confidence": True}
    buckets = {"0.5-0.6": [], "0.6-0.7": [], "0.7-0.8": [], "0.8-0.9": [], "0.9-1.0": []}
    y, p = [], []
    for o in outcomes:
        conf = float(o.get("confidence_at_entry", 0.5) or 0.5)
        actual = 1.0 if o.get("correctness_label") == "correct" else 0.0
        key = o.get("calibration_bucket", "unknown")
        if key in buckets:
            buckets[key].append(actual)
        y.append(actual); p.append(conf)
    brier = sum((pp - yy) ** 2 for pp, yy in zip(p, y)) / len(y)
    ece = 0.0
    for b, vals in buckets.items():
        if not vals:
            continue
        lo = float(b.split("-")[0])
        pred = lo + 0.05
        acc = sum(vals) / len(vals)
        ece += (len(vals) / len(y)) * abs(acc - pred)
    over = len([1 for pp, yy in zip(p, y) if pp >= 0.8 and yy == 0.0]) / max(1, len(y))
    under = len([1 for pp, yy in zip(p, y) if pp <= 0.6 and yy == 1.0]) / max(1, len(y))
    return {"ok": True, "sample_size": len(y), "low_confidence": len(y) < min_samples, "brier_score": brier, "expected_calibration_error": ece, "overconfidence_rate": over, "underconfidence_rate": under, "calibration_by_bucket": {k: (sum(v) / len(v) if v else None) for k, v in buckets.items()}}
