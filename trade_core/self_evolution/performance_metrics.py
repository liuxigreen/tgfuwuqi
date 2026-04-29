from __future__ import annotations


def compute_performance_metrics(trades, min_samples: int = 10):
    if not trades:
        return {"data_unavailable": True, "low_confidence": True}
    r = [float(t.get("R_multiple", 0.0)) for t in trades if "R_multiple" in t]
    if not r:
        return {"data_unavailable": True, "low_confidence": True}
    wins = [x for x in r if x > 0]
    losses = [x for x in r if x < 0]
    pf = (sum(wins) / abs(sum(losses))) if losses else None
    out = {
        "win_rate": len(wins) / len(r),
        "avg_R": sum(r) / len(r),
        "expectancy": sum(r) / len(r),
        "profit_factor": pf,
        "max_drawdown_pct": None,
        "sharpe_ratio": None,
        "sortino_ratio": None,
        "calmar_ratio": None,
        "consecutive_loss_max": 0,
        "stop_hit_rate": None,
        "time_stop_rate": None,
        "thesis_accuracy": None,
        "sample_size": len(r),
        "low_confidence": len(r) < min_samples,
    }
    c = 0
    for x in r:
        if x < 0:
            c += 1
            out["consecutive_loss_max"] = max(out["consecutive_loss_max"], c)
        else:
            c = 0
    return out
