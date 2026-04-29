from __future__ import annotations

from .models import ExitPolicyEvaluation


def evaluate_exit_policies(trades, market_series, policies, min_trades_per_policy: int = 20):
    out = []
    for p in policies:
        rows = [t for t in trades if t.get("policy_id") == p]
        n = len(rows)
        if n < min_trades_per_policy:
            out.append(ExitPolicyEvaluation(policy_id=p, trade_count=n, win_rate=None, avg_R=None, profit_factor=None, max_drawdown_pct=None, insufficient_sample_size=True).__dict__)
            continue
        r = [float(t.get("R_multiple", 0.0)) for t in rows]
        wins = [x for x in r if x > 0]
        losses = [abs(x) for x in r if x < 0]
        pf = (sum(wins) / sum(losses)) if losses else None
        out.append(ExitPolicyEvaluation(policy_id=p, trade_count=n, win_rate=len(wins) / n, avg_R=sum(r) / n, profit_factor=pf, max_drawdown_pct=None, insufficient_sample_size=False).__dict__)
    return {"evaluations": out}
