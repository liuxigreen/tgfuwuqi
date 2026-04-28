from trade_core.exit_policy.optimizer import propose_exit_policy_changes


def test_optimizer_requires_samples():
    out = propose_exit_policy_changes({"evaluations": [{"policy_id": "a", "insufficient_sample_size": True}]})
    assert out["insufficient_sample_size"] is True
    assert out["requires_human_approval"] is True
