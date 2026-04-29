from types import SimpleNamespace

from trade_core.exit_policy.selector import select_exit_policy


def test_exit_policy_selector_event():
    p = select_exit_policy(None, SimpleNamespace(signal_archetype="event_driven", confidence=0.8, manipulation_risk=0.3))
    assert p.policy_id == "event_driven_fast"
