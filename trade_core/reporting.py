from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .journal import review_journal
from .models import ReportResult


def _redact_text(s: str) -> str:
    for k in ["api_key", "secret", "token", "password", "auth"]:
        s = s.replace(k, f"{k}_redacted")
    return s


def build_daily_report(journal_path: str) -> ReportResult:
    summary = review_journal(journal_path)
    md = f"## Trade Core Daily Report\n- decisions: {summary.get('total_decisions', 0)}\n- blocked: {summary.get('blocked_count', 0)}\n- avg score: {summary.get('avg_total_score', 0)}"
    return ReportResult("Trade Core Daily", _redact_text(md), summary, "info", datetime.now(timezone.utc).isoformat())


def build_candidate_report(candidate_report: Dict[str, Any]) -> ReportResult:
    cnt = len(candidate_report.get("candidates", []))
    md = f"## Candidate Report\nCandidates: {cnt}"
    return ReportResult("Candidate Report", md, candidate_report, "info", datetime.now(timezone.utc).isoformat())


def build_position_report(position_evaluations: List[Dict[str, Any]]) -> ReportResult:
    md = f"## Position Report\nPositions: {len(position_evaluations)}"
    return ReportResult("Position Report", md, {"positions": position_evaluations}, "info", datetime.now(timezone.utc).isoformat())
