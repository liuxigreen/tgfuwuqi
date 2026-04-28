from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .schema import NuwaAssessment


def evaluate(sample: Dict[str, Any], nuwa_version: str = "nuwa_default_v1") -> NuwaAssessment:
    if sample.get("nuwa_eval"):
        e = sample["nuwa_eval"]
        return NuwaAssessment(
            nuwa_version=e.get("version", nuwa_version),
            source_skill="sample",
            market_regime=e.get("market_regime", "unknown"),
            signal_archetype=e.get("signal_archetype", "unknown"),
            signal_quality=float(e.get("signal_quality", 50)),
            continuation_probability=float(e.get("continuation_probability", 0.5)),
            manipulation_risk=float(e.get("manipulation_risk", 0.5)),
            distribution_risk=float(e.get("distribution_risk", 0.5)),
            preferred_action=e.get("preferred_action", "observe"),
            block_trade=bool(e.get("block_trade", False)),
            confidence=float(e.get("confidence", 0.5)),
            thesis_status=e.get("thesis_status", "stable"),
            risk_tags=e.get("risk_tags", []),
            reasoning_summary=e.get("notes", "sample nuwa"),
            honesty_boundary="sample-provided structured nuwa eval",
            timestamp=e.get("timestamp", datetime.now(timezone.utc).isoformat()),
            reason_codes=["nuwa_mock_eval"],
        )
    return NuwaAssessment(
        nuwa_version=nuwa_version,
        source_skill="mock_default",
        market_regime="unknown",
        signal_archetype="unknown",
        signal_quality=50,
        continuation_probability=0.5,
        manipulation_risk=0.5,
        distribution_risk=0.5,
        preferred_action="observe",
        block_trade=False,
        confidence=0.5,
        thesis_status="unknown",
        risk_tags=["conservative_default"],
        reasoning_summary="No real Nuwa evaluator configured.",
        honesty_boundary="No real Nuwa evaluator configured; using conservative default.",
        timestamp=datetime.now(timezone.utc).isoformat(),
        reason_codes=["nuwa_mock_eval"],
    )
