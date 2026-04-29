from __future__ import annotations

from .models import ExitPolicy
from ..config import load_config


def list_templates(config: dict | None = None) -> dict:
    cfg = config or load_config()
    return cfg.get("exit_policy_templates", {}).get("templates", {})


def get_template(name: str, config: dict | None = None) -> ExitPolicy:
    t = list_templates(config).get(name, {})
    return ExitPolicy(
        policy_id=name,
        stop_loss_pct=float(t.get("stop_loss_pct", 0.02)),
        first_take_profit_pct=float(t.get("first_tp_pct", 0.03)),
        final_take_profit_pct=float(t.get("final_tp_pct", 0.08)),
        partial_take_profit_pct=float(t.get("partial_take_profit_pct", 0.35)),
        trailing_stop_enabled=bool(t.get("trailing_stop_enabled", False)),
        max_hold_minutes=int(t.get("max_hold_minutes", 720)),
    )
