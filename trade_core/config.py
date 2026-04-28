from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

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
        "market_score": 0.15,
        "oi_score": 0.20,
        "funding_score": 0.10,
        "sentiment_score": 0.15,
        "smart_money_score": 0.20,
        "nuwa_score": 0.20,
        "risk_penalty": 0.20,
    },
    "operating_modes": {
        "default_mode": "propose",
        "default_dry_run": True,
        "allow_live_execution": False,
        "max_snapshot_age_minutes": 15,
    },
    "okx_gateway": {
        "backend": "mock",
        "profile": "demo",
        "default_demo": True,
        "allow_live": False,
        "allow_trade_execution": False,
        "command_timeout_seconds": 20,
        "max_slippage_pct": 0.003,
        "required_profile_for_execution": "demo",
        "read_only_modules": ["market", "account", "news", "smartmoney"],
        "execution_modules": ["spot", "swap"],
    },
    "exit_rules": {
        "first_tp_pct": 0.03,
        "final_tp_pct": 0.08,
        "stop_loss_pct": 0.02,
        "max_hold_minutes": 720,
        "tighten_stop_after_rr": 1.2,
        "partial_take_profit_pct": 0.35,
    },
    "nuwa_runtime": {
        "default_nuwa_version": "nuwa_default_v1",
        "min_confidence_for_demo_auto": 0.65,
        "fast_path": {"enabled": True, "timeout_ms": 800, "fallback_to_conservative": True, "min_confidence_for_demo_auto": 0.65},
        "deep_path": {"enabled": True, "run_in_fast_path": False, "output_proposed_changes_only": True},
        "versions": {},
    },
    "latency": {
        "fast_path": {
            "target_total_ms": 4000,
            "hard_timeout_ms": 5000,
            "adapter_timeout_ms": 900,
            "market_timeout_ms": 700,
            "oi_funding_timeout_ms": 900,
            "account_timeout_ms": 800,
            "sentiment_timeout_ms": 1000,
            "smartmoney_timeout_ms": 1000,
            "nuwa_fast_timeout_ms": 800,
            "scoring_timeout_ms": 200,
            "risk_timeout_ms": 200,
            "order_intent_timeout_ms": 200,
            "execution_timeout_ms": 1200,
            "allow_degraded_mode": True,
            "require_account_for_execution": True,
            "require_market_for_execution": True,
            "allow_missing_sentiment_in_propose": True,
            "allow_missing_smartmoney_in_propose": True,
            "allow_missing_sentiment_in_demo_auto": False,
            "allow_missing_smartmoney_in_demo_auto": False,
        },
        "slow_path": {"daily_review_enabled": True, "replay_enabled": True, "skill_metrics_enabled": True, "deep_nuwa_enabled": True, "exit_optimization_enabled": True},
    },
    "cache": {"ttl_ticker": 1, "ttl_account": 10, "ttl_sentiment": 60, "ttl_smartmoney": 60},
    "daily_limits": {"enabled": True, "max_trades_per_day": 8, "max_daily_loss_pct": 2.0, "max_consecutive_losses": 3, "symbol_cooldown_minutes": 60, "allow_position_exit_when_disabled": True},
    "skill_registry": {"skills": []},
    "skill_intelligence": {"auto_discovery": True, "auto_install": False, "auto_enable_new_skills": False, "disable_live_trade_skills": True},
    "exit_policy_templates": {"templates": {}},
    "exit_optimization": {"enabled": True, "min_trades_per_policy": 20, "min_days": 7, "requires_human_approval": True, "forbid_auto_apply": True, "max_allowed_stop_loss_pct": 0.035},
    "learning_loop": {"experience_retrieval": {"enabled": True, "max_latency_ms": 200, "top_k": 5, "min_similarity": 0.55, "max_score_boost": 5, "max_score_penalty": 12, "allow_in_fast_path": True}, "outcome_review": {"default_horizons_minutes": [240, 1440, 4320], "require_price_data": True}, "experience_store": {"min_review_confidence": 0.5, "min_evidence_required": True}},
}


def _parse_scalar(v: str) -> Any:
    s = str(v).strip()
    if s.lower() in {"true", "false"}:
        return s.lower() == "true"
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [x.strip().strip('"').strip("'") for x in inner.split(",")]
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return s.strip('"').strip("'")


def _simple_nested_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    root: Dict[str, Any] = {}
    stack = [(0, root)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]
        if text.startswith("- "):
            # unsupported list item nesting in fallback
            continue
        if ":" not in text:
            continue
        key, val = text.split(":", 1)
        key = key.strip()
        val = val.strip()
        if not val:
            cur[key] = {}
            stack.append((indent + 2, cur[key]))
        else:
            cur[key] = _parse_scalar(val)
    return root


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is not None:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        return loaded or {}
    return _simple_nested_yaml(path)


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _latency_compat(lat: Dict[str, Any]) -> Dict[str, Any]:
    fp = lat.get("fast_path", {})
    compat = {
        "fast_path_target_total_ms": fp.get("target_total_ms", 4000),
        "fast_path_hard_timeout_ms": fp.get("hard_timeout_ms", 5000),
    }
    compat.update(fp)
    return compat


def load_config(config_dir: Path | None = None) -> Dict[str, Any]:
    cfg_dir = config_dir or DEFAULT_CONFIG_DIR
    cfg = {
        "risk_limits": _merge(DEFAULTS["risk_limits"], load_yaml(cfg_dir / "risk_limits.yaml")),
        "scoring_weights": _merge(DEFAULTS["scoring_weights"], load_yaml(cfg_dir / "scoring_weights.yaml")),
        "operating_modes": _merge(DEFAULTS["operating_modes"], load_yaml(cfg_dir / "operating_modes.yaml")),
        "okx_gateway": _merge(DEFAULTS["okx_gateway"], load_yaml(cfg_dir / "okx_gateway.yaml")),
        "exit_rules": _merge(DEFAULTS["exit_rules"], load_yaml(cfg_dir / "exit_rules.yaml")),
        "nuwa_runtime": _merge(DEFAULTS["nuwa_runtime"], load_yaml(cfg_dir / "nuwa_runtime.yaml")),
        "latency_structured": _merge(DEFAULTS["latency"], load_yaml(cfg_dir / "latency.yaml")),
        "cache": _merge(DEFAULTS["cache"], load_yaml(cfg_dir / "cache.yaml")),
        "daily_limits": _merge(DEFAULTS["daily_limits"], load_yaml(cfg_dir / "daily_limits.yaml")),
        "skill_registry": _merge(DEFAULTS["skill_registry"], load_yaml(cfg_dir / "skill_registry.yaml")),
        "skill_intelligence": _merge(DEFAULTS["skill_intelligence"], load_yaml(cfg_dir / "skill_intelligence.yaml")),
        "exit_policy_templates": _merge(DEFAULTS["exit_policy_templates"], load_yaml(cfg_dir / "exit_policy_templates.yaml")),
        "exit_optimization": _merge(DEFAULTS["exit_optimization"], load_yaml(cfg_dir / "exit_optimization.yaml")),
        "learning_loop": _merge(DEFAULTS["learning_loop"], load_yaml(cfg_dir / "learning_loop.yaml")),
    }
    cfg["latency"] = _latency_compat(cfg["latency_structured"])
    return cfg


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    w = config.get("scoring_weights", {})
    required = ["market_score", "oi_score", "funding_score", "sentiment_score", "smart_money_score", "nuwa_score"]
    tw = sum(float(w.get(k, 0)) for k in required)
    if abs(tw - 1.0) > 1e-6:
        errors.append(f"scoring_weights_sum_invalid:{tw}")
    if config.get("risk_limits", {}).get("max_leverage", 0) > 3:
        errors.append("max_leverage_gt_3")
    if config.get("okx_gateway", {}).get("allow_live"):
        errors.append("allow_live_must_be_false")
    if config.get("latency_structured", {}).get("fast_path", {}).get("target_total_ms") != 4000:
        errors.append("latency_target_total_ms_invalid")
    if float(config.get("daily_limits", {}).get("max_daily_loss_pct", 0)) <= 0:
        errors.append("daily_limits_max_daily_loss_pct_invalid")
    return {"ok": not errors, "errors": errors, "config": config}
