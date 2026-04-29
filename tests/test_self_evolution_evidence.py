from trade_core.self_evolution import build_proposal


def test_proposal_requires_human_approval():
    out = build_proposal("2026-04-28", {"ok": True})
    assert out["requires_human_approval"] is True
