from __future__ import annotations


def simulate_exit_policy(trade_entry, market_series, exit_policy):
    if not market_series:
        return {"data_unavailable": True}
    entry = float(trade_entry.get("entry_price", market_series[0].get("price", 0)))
    end = float(market_series[-1].get("price", entry))
    pnl = (end - entry) / entry if entry else 0
    return {"policy_id": exit_policy.get("policy_id"), "pnl_pct": pnl, "insufficient_sample_size": len(market_series) < 2}
