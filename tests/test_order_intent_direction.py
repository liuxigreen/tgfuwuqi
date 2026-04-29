import json
from trade_core.decision import build_trade_decision
from trade_core.signal_bus import parse_case_payload


def _decision_from(path):
    with open(path, 'r', encoding='utf-8') as f:
        p=parse_case_payload(json.load(f))
    return build_trade_decision(**p)


def test_long_short_and_unknown_neutral_direction():
    d_long=_decision_from('examples/full_case_long_spot.json')
    assert d_long.direction.value=='long'

    d_short=_decision_from('examples/full_case_short_swap.json')
    assert d_short.direction.value=='short'

    d_unknown=_decision_from('examples/unknown_direction_case.json')
    assert d_unknown.action.value in {'observe','blocked','propose'}
