from trade_core.skill_intelligence import evaluate_skills, load_skill_registry


def test_skill_evaluator_has_scores():
    out = evaluate_skills(load_skill_registry())
    assert "skills" in out and out["skills"]
    assert "safety_score" in out["skills"][0]
