from __future__ import annotations


def summarize_exit_metrics(sim_results):
    if not sim_results:
        return {"data_unavailable": True}
    vals = [x.get("pnl_pct", 0) for x in sim_results if "pnl_pct" in x]
    return {"trade_count": len(vals), "avg_pnl_pct": (sum(vals) / len(vals)) if vals else None}
