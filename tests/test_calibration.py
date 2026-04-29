from trade_core.learning_loop.calibration import calibration_review


def test_calibration_overconfidence_detected():
    out = calibration_review([
        {"confidence_at_entry": 0.85, "correctness_label": "wrong", "calibration_bucket": "0.8-0.9"},
        {"confidence_at_entry": 0.82, "correctness_label": "wrong", "calibration_bucket": "0.8-0.9"},
    ], min_samples=1)
    assert out["overconfidence_rate"] > 0
