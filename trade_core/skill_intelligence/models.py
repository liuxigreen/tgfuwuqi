from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SkillRecord:
    skill_id: str
    source: str
    category: str
    enabled: bool = False
    trusted: bool = False
    can_execute_trade: bool = False
    risk_level: str = "read_only"
    lifecycle_stages: list[str] = field(default_factory=list)
