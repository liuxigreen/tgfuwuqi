from trade_core.learning_loop.feedback import add_feedback, review_feedback


def test_feedback_add_and_review():
    add_feedback("d1", "threshold_too_strict", "msg")
    out = review_feedback("2026-")
    assert "feedback_count" in out
