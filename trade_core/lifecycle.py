from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Any, Dict

from .config import load_config
from .decision import build_trade_decision
from .journal import write_journal_event
from .models import Direction, NuwaEval, PositionState, enum_from_value, model_to_dict
from .nuwa_runtime import load_registry, run_nuwa_evaluation, run_shadow_nuwa_evaluations
from .order_intent import build_order_intent
from .okx_gateway import OkxGateway
from .position_manager import evaluate_position_exit
from .signal_bus import parse_case_payload


def _gateway_from_config(config: dict, force_dry_run: bool = True) -> OkxGateway:
    gw = config["okx_gateway"]
    return OkxGateway(
        backend=gw.get("backend", "mock"),
        profile=gw.get("profile", "demo"),
        dry_run=force_dry_run,
        allow_live=gw.get("allow_live", False),
        allow_trade_execution=gw.get("allow_trade_execution", False),
        command_timeout_seconds=int(gw.get("command_timeout_seconds", 20)),
    )


def run_pretrade_pipeline(sample_or_signal: Dict[str, Any], mode: str = "propose", journal_dir: str = "data/trade_core_journal") -> Dict[str, Any]:
    config = load_config()
    pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"
    registry = load_registry(config)
    nuwa = run_nuwa_evaluation(sample_or_signal, registry.get("default_nuwa_version", "nuwa_default_v1"))
    shadow = run_shadow_nuwa_evaluations(sample_or_signal, list(registry.get("versions", {}).keys())[:2])

    enriched = dict(sample_or_signal)
    enriched["nuwa_eval"] = {
        "version": nuwa["nuwa_version"],
        "market_regime": nuwa["market_regime"],
        "signal_archetype": nuwa["signal_archetype"],
        "signal_quality": nuwa["signal_quality"],
        "continuation_probability": nuwa["continuation_probability"],
        "manipulation_risk": nuwa["manipulation_risk"],
        "preferred_action": nuwa["preferred_action"],
        "block_trade": nuwa["block_trade"],
        "confidence": nuwa["confidence"],
        "notes": nuwa.get("thesis_status", ""),
    }

    payload = parse_case_payload(enriched)
    decision = build_trade_decision(
        radar_signal=payload["radar_signal"],
        nuwa_eval=payload["nuwa_eval"],
        market_snapshot=payload.get("market_snapshot"),
        sentiment_snapshot=payload.get("sentiment_snapshot"),
        smartmoney_snapshot=payload.get("smartmoney_snapshot"),
        account_snapshot=payload.get("account_snapshot"),
        mode=mode,
        config=config,
    )
    intent = build_order_intent(decision, config)
    gateway = _gateway_from_config(config, force_dry_run=True)
    execution_result = gateway.execute_order_intent(intent, mode, risk_result={"passed": decision.risk_status != "blocked"}, demo_execute=False)

    decision_payload = model_to_dict(decision)
    decision_payload["shadow_nuwa_evals"] = shadow
    journal_path = write_journal_event("decision", pipeline_id, decision.symbol, decision_payload, decision.nuwa_version, base_dir=journal_dir)
    write_journal_event("order_intent", pipeline_id, decision.symbol, model_to_dict(intent), decision.nuwa_version, base_dir=journal_dir)
    write_journal_event("execution_result", pipeline_id, decision.symbol, execution_result, decision.nuwa_version, base_dir=journal_dir)

    return {
        "pipeline_id": pipeline_id,
        "mode": mode,
        "symbol": decision.symbol,
        "action": decision.action.value,
        "decision": decision_payload,
        "score_breakdown": decision.score_breakdown,
        "order_intent": model_to_dict(intent),
        "execution_result": execution_result,
        "position_action": "none",
        "reason_codes": decision.reason_codes,
        "blocked_reasons": decision.blocked_reasons,
        "warnings": decision.warnings + registry.get("warnings", []),
        "journal_path": journal_path,
        "nuwa_version": decision.nuwa_version,
    }


def run_demo_execution_pipeline(sample_or_signal: Dict[str, Any], demo_execute: bool = False, backend: str | None = None, profile: str | None = None, journal_dir: str = "data/trade_core_journal") -> Dict[str, Any]:
    config = load_config()
    if backend:
        config["okx_gateway"]["backend"] = backend
    if profile:
        config["okx_gateway"]["profile"] = profile
    pre = run_pretrade_pipeline(sample_or_signal, mode="demo_auto", journal_dir=journal_dir)
    decision = pre["decision"]
    intent = pre["order_intent"]

    # explicit gating for demo execution
    intent["dry_run"] = not demo_execute
    gateway = _gateway_from_config(config, force_dry_run=not demo_execute)
    from .models import OrderIntent

    exec_out = gateway.execute_order_intent(OrderIntent(**intent), "demo_auto", risk_result={"passed": decision.get("risk_status") != "blocked"}, demo_execute=demo_execute)
    pre["execution_result"] = exec_out
    pre["demo_execute"] = demo_execute
    return pre


def run_position_management(position_snapshot: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = config or load_config()
    item = dict(position_snapshot["position_state"])
    item["side"] = enum_from_value(Direction, item.get("side"), Direction.UNKNOWN)
    ps = PositionState(**item)

    nuwa = None
    if position_snapshot.get("nuwa_eval"):
        n = position_snapshot["nuwa_eval"]
        nuwa = NuwaEval(
            version=n.get("version", "nuwa_default_v1"), market_regime=n.get("market_regime", "unknown"), signal_archetype=n.get("signal_archetype", "unknown"), signal_quality=float(n.get("signal_quality", 0.5)), continuation_probability=float(n.get("continuation_probability", 0.5)), manipulation_risk=float(n.get("manipulation_risk", 0.5)), preferred_action=n.get("preferred_action", "observe"), block_trade=bool(n.get("block_trade", False)), confidence=float(n.get("confidence", 0.5)), notes=n.get("thesis_status", n.get("notes", ""))
        )
    out = evaluate_position_exit(
        ps,
        sentiment_snapshot=parse_case_payload({"radar_signal": {"symbol": ps.symbol, "market_type": "swap", "direction": "long", "score": 0, "source": "tmp", "timestamp": "2026-01-01T00:00:00Z"}, "nuwa_eval": {"version": "x", "market_regime": "x", "signal_archetype": "x", "signal_quality": 0.5, "continuation_probability": 0.5, "manipulation_risk": 0.5, "preferred_action": "observe", "block_trade": False, "confidence": 0.5, "notes": ""}, "sentiment_snapshot": position_snapshot.get("sentiment_snapshot")}).get("sentiment_snapshot") if position_snapshot.get("sentiment_snapshot") else None,
        smartmoney_snapshot=parse_case_payload({"radar_signal": {"symbol": ps.symbol, "market_type": "swap", "direction": "long", "score": 0, "source": "tmp", "timestamp": "2026-01-01T00:00:00Z"}, "nuwa_eval": {"version": "x", "market_regime": "x", "signal_archetype": "x", "signal_quality": 0.5, "continuation_probability": 0.5, "manipulation_risk": 0.5, "preferred_action": "observe", "block_trade": False, "confidence": 0.5, "notes": ""}, "smartmoney_snapshot": position_snapshot.get("smartmoney_snapshot")}).get("smartmoney_snapshot") if position_snapshot.get("smartmoney_snapshot") else None,
        market_snapshot=parse_case_payload({"radar_signal": {"symbol": ps.symbol, "market_type": "swap", "direction": "long", "score": 0, "source": "tmp", "timestamp": "2026-01-01T00:00:00Z"}, "nuwa_eval": {"version": "x", "market_regime": "x", "signal_archetype": "x", "signal_quality": 0.5, "continuation_probability": 0.5, "manipulation_risk": 0.5, "preferred_action": "observe", "block_trade": False, "confidence": 0.5, "notes": ""}, "market_snapshot": position_snapshot.get("market_snapshot")}).get("market_snapshot") if position_snapshot.get("market_snapshot") else None,
        nuwa_eval=nuwa,
        rules=cfg.get("exit_rules", {}),
    )
    return {"position": position_snapshot.get("position_state"), "evaluation": model_to_dict(out)}
