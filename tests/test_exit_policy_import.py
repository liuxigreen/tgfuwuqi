from trade_core.exit_policy import select_exit_policy
from trade_core.exit_policy.models import ExitPolicy


def test_exit_policy_import_works():
    p = select_exit_policy(None, type("N", (), {"signal_archetype": "trend", "confidence": 0.8, "manipulation_risk": 0.3})())
    assert isinstance(p, ExitPolicy)
