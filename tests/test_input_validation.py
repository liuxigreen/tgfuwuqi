import json

from trade_core.decision import build_trade_decision
from trade_core.signal_bus import parse_case_payload


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return parse_case_payload(json.load(f))


def test_symbol_mismatch_blocked():
    p = load_json("examples/symbol_mismatch_case.json")
    d = build_trade_decision(**p)
    assert d.action.value == "blocked"
    assert "symbol_mismatch" in d.blocked_reasons


def test_stale_market_snapshot_downgrade_propose():
    p = load_json("examples/stale_snapshot_case.json")
    p["mode"] = "propose"
    d = build_trade_decision(**p)
    assert d.action.value in {"observe", "blocked"}


def test_stale_account_snapshot_blocks_demo_auto():
    p = load_json("examples/full_case.json")
    p["account_snapshot"].timestamp = "2026-04-20T00:00:00Z"
    p["mode"] = "demo_auto"
    d = build_trade_decision(**p)
    assert d.action.value == "blocked"


def test_missing_account_blocks_execution_mode():
    p = load_json("examples/full_case.json")
    p["account_snapshot"] = None
    p["mode"] = "demo_auto"
    d = build_trade_decision(**p)
    assert d.action.value == "blocked"
