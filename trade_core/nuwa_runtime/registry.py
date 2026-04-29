from __future__ import annotations

from pathlib import Path
from typing import Dict

from ..config import load_config


def load_registry(config=None) -> Dict:
    cfg = config or load_config()
    rt = cfg.get("nuwa_runtime", {})
    warnings = []
    for name, meta in rt.get("versions", {}).items():
        path = Path(str(meta.get("skill_path", "")))
        if not path.exists():
            warnings.append(f"missing_skill_path:{name}")
    return {"default_nuwa_version": rt.get("default_nuwa_version"), "min_confidence_for_demo_auto": rt.get("min_confidence_for_demo_auto", 0.65), "versions": rt.get("versions", {}), "warnings": warnings}
