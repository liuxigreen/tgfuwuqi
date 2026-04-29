from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ExitPolicy:
    policy_id: str
    stop_loss_pct: float
    first_take_profit_pct: float
    final_take_profit_pct: float
    partial_take_profit_pct: float = 0.35
    trailing_stop_enabled: bool = False
    max_hold_minutes: int = 720
    source: str = "static_default"


@dataclass
class ExitPolicyEvaluation:
    policy_id: str
    trade_count: int
    win_rate: float | None
    avg_R: float | None
    profit_factor: float | None
    max_drawdown_pct: float | None
    insufficient_sample_size: bool


@dataclass
class ProposedExitPolicyChanges:
    requires_human_approval: bool
    forbid_auto_apply: bool
    insufficient_sample_size: bool
    changes: list[Dict[str, Any]]
