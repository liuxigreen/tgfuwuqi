from __future__ import annotations


RECIPES = {
    "find_candidates": "candidate_discovery_v1",
    "confirm_signal": "signal_confirmation_v1",
    "execute_demo_order": "demo_execution_v1",
    "manage_position": "position_management_v1",
    "daily_review": "daily_review_v1",
}


def route_skill_recipe(task: str, mode: str):
    return {"task": task, "selected_recipe": RECIPES.get(task, "candidate_discovery_v1"), "mode": mode, "fast_path_allowed": task in {"confirm_signal", "execute_demo_order"}}
