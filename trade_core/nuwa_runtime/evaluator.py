from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from .mock_evaluator import evaluate


def run_nuwa_evaluation(sample: Dict[str, Any], nuwa_version: str) -> Dict[str, Any]:
    return asdict(evaluate(sample, nuwa_version=nuwa_version))


def run_shadow_nuwa_evaluations(sample: Dict[str, Any], versions: List[str]) -> List[Dict[str, Any]]:
    return [run_nuwa_evaluation(sample, v) for v in versions]
