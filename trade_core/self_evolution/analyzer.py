from __future__ import annotations

from pathlib import Path

from collections import Counter
from typing import Dict

from .metrics import load_events_for_date
from ..learning_loop.calibration import calibration_review
from ..learning_loop.feedback import review_feedback


def daily_review(date: str, journal_dir='data/trade_core_journal') -> Dict:
    events = load_events_for_date(date, journal_dir)
    if not events:
        return {"ok": False, "warning": "no_journal_for_date", "date": date}
    decisions = [e for e in events if e.get('event_type') == 'decision']
    actions = Counter([d.get('payload', {}).get('action', 'unknown') for d in decisions])
    lat = [d.get('payload', {}).get('latency_summary', {}).get('total_ms', 0) for d in decisions]
    lat = [x for x in lat if isinstance(x, (int, float))]
    lat_sorted = sorted(lat)
    p95 = lat_sorted[int(0.95 * (len(lat_sorted)-1))] if lat_sorted else 0
    fb = review_feedback(date)
    outcomes = []
    op = Path("data/outcomes") / f"{date}.outcomes.jsonl"
    if op.exists():
        import json
        outcomes = [json.loads(x) for x in op.read_text(encoding="utf-8").splitlines() if x.strip()]
    cal = calibration_review(outcomes)
    evaluable_outcomes = [o for o in outcomes if o.get("correctness_label") in {"correct", "wrong", "partially_correct", "avoided_bad_trade", "missed_good_trade"}]
    return {
        "ok": True,
        "date": date,
        "total_signals": len(decisions),
        "total_decisions": len(decisions),
        "total_orders": len([e for e in events if e.get('event_type') == 'order_intent']),
        "demo_orders": len([e for e in events if e.get('event_type') == 'execution_result' and e.get('payload', {}).get('dry_run') is False]),
        "dry_run_orders": len([e for e in events if e.get('event_type') == 'execution_result' and e.get('payload', {}).get('dry_run') is True]),
        "blocked_count": actions.get('blocked', 0),
        "observe_count": actions.get('observe', 0),
        "small_probe_count": actions.get('small_probe', 0),
        "open_count": actions.get('open_long', 0) + actions.get('open_short', 0),
        "exit_count": actions.get('close', 0),
        "win_count": None if not evaluable_outcomes else len([o for o in evaluable_outcomes if o.get("correctness_label")=="correct"]),
        "loss_count": None if not evaluable_outcomes else len([o for o in evaluable_outcomes if o.get("correctness_label")=="wrong"]),
        "win_rate": None if not evaluable_outcomes else (len([o for o in evaluable_outcomes if o.get("correctness_label")=="correct"]) / max(1,len(evaluable_outcomes))),
        "profit_factor": None if not evaluable_outcomes else "data_unavailable",
        "total_pnl_usdt": None,
        "total_pnl_pct": None,
        "max_drawdown_pct": None if not evaluable_outcomes else "data_unavailable",
        "avg_R": None if not evaluable_outcomes else "data_unavailable",
        "sharpe_ratio": None if not evaluable_outcomes else "data_unavailable",
        "sortino_ratio": None if not evaluable_outcomes else "data_unavailable",
        "calmar_ratio": None if not evaluable_outcomes else "data_unavailable",
        "avg_latency_ms": sum(lat)/len(lat) if lat else 0,
        "p95_latency_ms": p95,
        "timeout_count": len([d for d in decisions if 'latency_budget_exceeded' in d.get('payload', {}).get('reason_codes', [])]),
        "degraded_mode_count": len([d for d in decisions if d.get('payload', {}).get('degraded_mode')]),
        "top_symbols": Counter([d.get('symbol') for d in decisions]).most_common(5),
        "worst_symbols": [],
        "best_recipes": [],
        "worst_recipes": [],
        "best_nuwa_version": None,
        "worst_nuwa_version": None,
        "best_skill_combo": None,
        "worst_skill_combo": None,
        "top_blocked_reasons": Counter([r for d in decisions for r in d.get('payload', {}).get('blocked_reasons', [])]).most_common(5),
        "false_positive_estimate": 0.0,
        "missed_opportunity_estimate": 0.0,
        "recommendations": ["Prefer lower-latency adapters and keep live disabled."],
        "insufficient_sample_size": len(evaluable_outcomes) < 10,
        "outcome_count": len(outcomes),
        "correct_count": len([o for o in outcomes if o.get("correctness_label")=="correct"]),
        "wrong_count": len([o for o in outcomes if o.get("correctness_label")=="wrong"]),
        "avoided_bad_trade_count": len([o for o in outcomes if o.get("correctness_label")=="avoided_bad_trade"]),
        "missed_good_trade_count": len([o for o in outcomes if o.get("correctness_label")=="missed_good_trade"]),
        "inconclusive_count": len([o for o in outcomes if o.get("correctness_label") in {"inconclusive","data_unavailable"}]),
        "brier_score": cal.get("brier_score"),
        "calibration_error": cal.get("expected_calibration_error"),
        "overconfidence_rate": cal.get("overconfidence_rate"),
        "top_error_types": Counter([o.get("error_type","unknown") for o in outcomes]).most_common(5),
        "top_lessons": [],
        "experience_added_count": 0,
        "feedback_count": fb.get("feedback_count", 0),
        "feedback_supported_count": fb.get("feedback_supported_count", 0),
        "feedback_rejected_count": fb.get("feedback_rejected_count", 0),
        "best_experience_tags": [],
        "worst_experience_tags": [],
    }
