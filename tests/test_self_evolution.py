from trade_core.self_evolution import build_proposal, validate_proposal


def test_proposal_guardrails():
    p=build_proposal('2026-04-29',{})
    assert p['requires_human_approval'] is True
    g=validate_proposal(p)
    assert g['requires_human_approval'] is True
