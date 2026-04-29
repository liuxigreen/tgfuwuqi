from trade_core.models import Direction, NuwaEval, PositionState
from trade_core.position_manager import evaluate_exit


def test_thesis_invalidated_reduce_or_close():
    ps = PositionState("p1", "BTC-USDT-SWAP", Direction.LONG, 67000, 66500, -0.8, 180, ["a"], "thesis invalid break", 1.8, 3.5)
    nuwa = NuwaEval("v1", "trend", "cont", 0.7, 0.3, 0.8, "observe", False, 0.7, "invalidated")
    out = evaluate_exit(ps, nuwa_eval=nuwa)
    assert out.action in {"REDUCE", "CLOSE"}
