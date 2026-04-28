from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"


DEFAULTS: Dict[str, Any] = {
    "risk_limits": {
        "max_daily_loss_pct": 3.0,
        "max_open_positions": 3,
        "max_total_exposure_pct": 50.0,
        "max_leverage": 3.0,
        "allowed_market_types": ["swap", "spot"],
        "default_stop_loss_pct": 1.8,
        "default_take_profit_pct": 3.5,
        "max_hold_minutes": 720,
    },
    "scoring_weights": {
        "radar": 0.25,
        "market": 0.20,
        "sentiment": 0.15,
        "smartmoney": 0.20,
        "nuwa": 0.20,
    },
    "operating_modes": {
        "default_mode": "propose",
        "default_dry_run": True,
        "allow_live_execution": False,
    },
}


def _parse_scalar(value: str) -> Any:
    v = value.strip()
    if v.lower() in {"true", "false"}:
        return v.lower() == "true"
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip('"').strip("'") for x in inner.split(",")]
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v.strip('"').strip("'")


def load_simple_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    result: Dict[str, Any] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        result[key] = _parse_scalar(value)
    return result


def load_config(config_dir: Path | None = None) -> Dict[str, Any]:
    cfg_dir = config_dir or DEFAULT_CONFIG_DIR
    risk = {**DEFAULTS["risk_limits"], **load_simple_yaml(cfg_dir / "risk_limits.yaml")}
    weights = {**DEFAULTS["scoring_weights"], **load_simple_yaml(cfg_dir / "scoring_weights.yaml")}
    modes = {**DEFAULTS["operating_modes"], **load_simple_yaml(cfg_dir / "operating_modes.yaml")}
    return {"risk_limits": risk, "scoring_weights": weights, "operating_modes": modes}


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    weights = config.get("scoring_weights", {})
    total_weight = sum(float(weights.get(k, 0)) for k in ["radar", "market", "sentiment", "smartmoney", "nuwa"])
    if abs(total_weight - 1.0) > 1e-6:
        errors.append(f"scoring_weights_sum_invalid:{total_weight}")
    if config.get("risk_limits", {}).get("max_leverage", 0) > 3:
        errors.append("max_leverage_gt_3")
    return {"ok": not errors, "errors": errors, "config": config}
