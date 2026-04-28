from __future__ import annotations

import uuid
from typing import Any, Dict

from .config import load_config
from .decision import build_trade_decision
from .journal import write_journal_event
from .models import Direction, PositionState, enum_from_value, model_to_dict
from .order_intent import build_order_intent
from .okx_gateway import OkxGateway
from .position_manager import evaluate_position_exit
from .signal_bus import parse_case_payload


def run_pretrade_pipeline(sample_or_signal: Dict[str, Any], mode: str = "propose", journal_dir: str = "data/trade_core_journal") -> Dict[str, Any]:
    config = load_config()
    pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"
    payload = parse_case_payload(sample_or_signal)
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
    gw = config["okx_gateway"]
    gateway = OkxGateway(backend=gw.get("backend", "mock"), profile=gw.get("profile", "demo"), dry_run=True, allow_live=gw.get("allow_live", False), allow_trade_execution=gw.get("allow_trade_execution", False), command_timeout_seconds=int(gw.get("command_timeout_seconds", 20)))
    execution_result = gateway.execute_order_intent(intent, mode)

    journal_path = write_journal_event("decision", pipeline_id, decision.symbol, model_to_dict(decision), decision.nuwa_version, base_dir=journal_dir)
    write_journal_event("order_intent", pipeline_id, decision.symbol, model_to_dict(intent), decision.nuwa_version, base_dir=journal_dir)
    write_journal_event("execution_result", pipeline_id, decision.symbol, execution_result, decision.nuwa_version, base_dir=journal_dir)

    return {
        "pipeline_id": pipeline_id,
        "mode": mode,
        "symbol": decision.symbol,
        "action": decision.action.value,
        "decision": model_to_dict(decision),
        "order_intent": model_to_dict(intent),
        "execution_result": execution_result,
        "position_action": "none",
        "reason_codes": decision.reason_codes,
        "blocked_reasons": decision.blocked_reasons,
        "warnings": decision.warnings,
        "journal_path": journal_path,
    }


def run_demo_execution_pipeline(sample_or_signal: Dict[str, Any], demo_execute: bool = False, journal_dir: str = "data/trade_core_journal") -> Dict[str, Any]:
    out = run_pretrade_pipeline(sample_or_signal, mode="demo_auto", journal_dir=journal_dir)
    out["demo_execute"] = demo_execute
    return out


def run_position_management(position_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(position_snapshot["position_state"]); item["side"] = enum_from_value(Direction, item.get("side"), Direction.UNKNOWN); ps = PositionState(**item)
    out = evaluate_position_exit(ps)
    return {"position": position_snapshot["position_state"], "evaluation": model_to_dict(out)}
