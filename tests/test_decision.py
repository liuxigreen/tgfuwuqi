from trade_core.decision import build_trade_decision
from trade_core.signal_bus import parse_case_payload
import json


def load_case():
    with open("examples/full_case.json", "r", encoding="utf-8") as f:
        return parse_case_payload(json.load(f))


def test_wait_pullback_caps_action():
    p = load_case()
    d = build_trade_decision(**p)
    assert d.action.value in {"propose", "small_probe", "observe", "blocked"}
    assert d.action.value != "open_long"


def test_nuwa_block_trade_blocked():
    p = load_case()
    p["nuwa_eval"].block_trade = True
    d = build_trade_decision(**p)
    assert d.action.value == "blocked"
