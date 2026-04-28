import json

from trade_core.decision import build_trade_decision
from trade_core.signal_bus import parse_case_payload


def load_case(path="examples/full_case.json"):
    with open(path, "r", encoding="utf-8") as f:
        return parse_case_payload(json.load(f))


def test_wait_pullback_caps_action():
    p = load_case()
    d = build_trade_decision(**p)
    assert d.action.value != "open_long"


def test_nuwa_block_trade_blocked():
    p = load_case()
    p["nuwa_eval"].block_trade = True
    d = build_trade_decision(**p)
    assert d.action.value == "blocked"
