from trade_core.exit_policy.simulator import simulate_exit_policy


def test_simulator_insufficient_series():
    out = simulate_exit_policy({"entry_price": 100}, [{"price": 100}], {"policy_id": "p1"})
    assert out["insufficient_sample_size"] is True
