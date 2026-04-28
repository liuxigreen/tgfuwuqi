from __future__ import annotations


def build_skill_metrics(journal_events):
    if not journal_events:
        return {"data_unavailable": True}
    return {"sample_size": len(journal_events), "best_skill_combo": None, "worst_skill_combo": None}
