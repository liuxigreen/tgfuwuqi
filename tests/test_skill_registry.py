from trade_core.skill_intelligence import load_skill_registry


def test_skill_registry_contains_required_skill():
    reg = load_skill_registry()
    ids = [x["skill_id"] for x in reg["skills"]]
    assert "okx-cex-market" in ids
