from trade_core.models import Direction, NuwaEval, PositionState, SentimentSnapshot, SmartMoneySnapshot
from trade_core.position_manager import evaluate_position_exit


def test_hard_stop_exit_full():
    ps = PositionState("1", "BTC-USDT-SWAP", Direction.LONG, 100, 95, -0.03, 10, [], "x", 0.02, 0.08)
    out = evaluate_position_exit(ps)
    assert out.recommended_action == "EXIT_FULL"


def test_first_tp_partial_profit():
    ps = PositionState("1", "BTC-USDT-SWAP", Direction.LONG, 100, 104, 0.04, 10, [], "x", 0.02, 0.08)
    out = evaluate_position_exit(ps)
    assert out.recommended_action == "TAKE_PARTIAL_PROFIT"


def test_thesis_weakening_reduce_or_tighten():
    ps = PositionState("1", "BTC-USDT-SWAP", Direction.LONG, 100, 101, 0.01, 10, [], "x", 0.02, 0.08)
    nuwa = NuwaEval("v1", "trend", "c", 0.6, 0.6, 0.2, "propose", False, 0.7, "weakening")
    out = evaluate_position_exit(ps, nuwa_eval=nuwa)
    assert out.recommended_action in {"REDUCE", "TIGHTEN_STOP", "HOLD", "TAKE_PARTIAL_PROFIT"}


def test_smartmoney_reversal_reduce_or_exit():
    ps = PositionState("1", "BTC-USDT-SWAP", Direction.LONG, 100, 99, -0.01, 10, [], "x", 0.02, 0.08)
    sm = SmartMoneySnapshot("BTC-USDT-SWAP", Direction.SHORT, Direction.SHORT, 0.7, 0.9, "distribute", 100, 99, 0.1, "2026-04-28T00:00:00Z")
    se = SentimentSnapshot("BTC-USDT-SWAP", 0.4, "down", False, 0.2, "2026-04-28T00:00:00Z")
    out = evaluate_position_exit(ps, sentiment_snapshot=se, smartmoney_snapshot=sm)
    assert out.recommended_action in {"REDUCE", "EXIT_FULL", "REVIEW_REQUIRED"}
