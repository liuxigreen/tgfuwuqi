from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class NuwaAssessment:
    nuwa_version: str
    source_skill: str
    market_regime: str
    signal_archetype: str
    signal_quality: float
    continuation_probability: float
    manipulation_risk: float
    distribution_risk: float
    preferred_action: str
    block_trade: bool
    confidence: float
    thesis_status: str
    risk_tags: List[str] = field(default_factory=list)
    reasoning_summary: str = ""
    honesty_boundary: str = ""
    timestamp: str = ""
    reason_codes: List[str] = field(default_factory=list)
