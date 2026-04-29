from trade_core.skill_intelligence import route_skill_recipe


def test_skill_router_maps_task():
    out = route_skill_recipe("execute_demo_order", "demo_auto")
    assert out["selected_recipe"] == "demo_execution_v1"
