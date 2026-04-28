from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .journal import _sanitize, review_journal
from .models import ReportResult


def build_daily_report(journal_path: str) -> ReportResult:
    summary = review_journal(journal_path)
    redacted = _sanitize(summary)
    md = f"## Trade Core Daily Report\n- decisions: {redacted.get('total_decisions', 0)}\n- blocked: {redacted.get('blocked_count', 0)}\n- avg score: {redacted.get('avg_total_score', 0)}"
    return ReportResult("Trade Core Daily", md, redacted, "info", datetime.now(timezone.utc).isoformat())


def build_candidate_report(candidate_report: Dict[str, Any]) -> ReportResult:
    cnt = len(candidate_report.get("candidates", []))
    md = f"## Candidate Report\nCandidates: {cnt}"
    return ReportResult("Candidate Report", md, _sanitize(candidate_report), "info", datetime.now(timezone.utc).isoformat())


def build_position_report(position_evaluations: List[Dict[str, Any]]) -> ReportResult:
    md = f"## Position Report\nPositions: {len(position_evaluations)}"
    return ReportResult("Position Report", md, _sanitize({"positions": position_evaluations}), "info", datetime.now(timezone.utc).isoformat())
