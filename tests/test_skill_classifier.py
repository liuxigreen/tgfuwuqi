from trade_core.skill_intelligence.classifier import classify_skill


def test_skill_classifier_execution():
    assert classify_skill({"skill_id": "okx-cex-trade"}) == "execution"
