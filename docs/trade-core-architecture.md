# Trade Core Architecture (Stabilization Design)

## 1) System Overview

Trade Core is the **final decision and safety arbitration layer** in a layered AI trading system:

1. **Radar Layer**: discovery only (signal finding), no execution rights.
2. **Nuwa Layer**: cognitive evaluation only, returns structured assessment, no execution rights.
3. **Trade Core Layer**: scoring + risk + exit policy + order intent + mode decision.
4. **OKX Gateway Layer**: capability adapter (read market/account data + demo/dry-run execution), not strategy brain.
5. **Exit Policy Layer**: mandatory protection model for every open intent.
6. **Position Management Layer**: post-entry control decisions.
7. **Journal/Snapshot Layer**: immutable traceability and replay context.
8. **Learning Loop Layer**: offline evaluation and experience accumulation.
9. **Skill Intelligence Layer**: skill registry/classification/routing support.
10. **Self-Evolution Layer**: proposal generator only, never auto-apply risk changes.

---

## 2) Layer Responsibilities

### Radar Layer
- Input: external scanners (OI/Funding anomalies, narrative, sentiment, smart-money hints).
- Output: normalized `RadarSignal` events with metadata and timestamps.
- Constraint: cannot call execution APIs directly.

### Nuwa Layer
- Input: distilled trader knowledge + current signal context.
- Output: `NuwaEval` only (market regime, signal quality, manipulation risk, thesis validity, preferred action/exit style, block_trade).
- Constraint: no order generation, no gateway execution path.

### Trade Core
- Input: radar signal + enriched market/account context + NuwaEval.
- Responsibilities:
  - score computation,
  - hard risk checks,
  - daily limits checks,
  - exit policy selection,
  - order intent generation,
  - mode gate (`observe`/`propose`/`demo_auto`/`blocked`).
- Constraint: all execution must be based on `OrderIntent` JSON contract.

### OKX Gateway
- Read-only adapters: market, OI/funding, account/positions, sentiment/news, smart-money.
- Execution adapters: dry-run + demo execution only (live disabled).
- Constraint: gateway methods require `OrderIntent` and mode/safety checks from Trade Core.

### Exit Policy
- Enforces mandatory exit controls for open intents:
  - stop_loss,
  - first TP,
  - final TP,
  - partial TP,
  - optional trailing stop,
  - time stop,
  - thesis invalidation.

### Position Management
- Post-entry actions: `HOLD`, `REDUCE`, `TIGHTEN_STOP`, `TAKE_PARTIAL_PROFIT`, `EXIT_FULL`, `BLOCK_ADD`, `REVIEW_REQUIRED`.

### Journal/Snapshot
- Stores evidence for every decision (inputs, score breakdown, risk output, intent, exit policy, rationale, latency, selected skills/recipe).

### Learning Loop / Skill Intelligence / Self-Evolution
- Run in Slow Path only.
- Learning generates `OutcomeEvaluation` + `ExperienceRecord`.
- Self-evolution produces `ProposedChange` only and requires human approval.

---

## 3) Data Flow

1. Radar emits `RadarSignal`.
2. Fast enrichment pulls market/account/OI/funding/sentiment/smartmoney snapshots.
3. Nuwa fast evaluator returns `NuwaEval`.
4. Trade Core computes `ScoreBreakdown`.
5. Risk + daily limits decide allowed/blocked state.
6. Exit policy selector produces `ExitPolicy` for executable entries.
7. `OrderIntent` is created (or null intent for non-execution).
8. Mode gate decides execution path:
   - observe/propose: no execution
   - demo_auto: demo/dry-run only
   - blocked: no execution
9. Journal writes `DecisionSnapshot` + execution result.
10. Slow Path later performs outcome/review/learning/proposal.

---

## 4) Fast Path vs Slow Path

### Fast Path (target ~4s)
Allowed:
- signal normalize,
- parallel enrich,
- fast Nuwa structured eval,
- scoring,
- risk/daily-limit checks,
- exit policy select,
- order intent,
- dry-run/demo execution.

Forbidden in Fast Path:
- deep Nuwa,
- skill discovery,
- replay/report generation,
- self-evolution,
- exit optimization,
- web search.

### Slow Path
- daily review,
- outcome evaluation,
- AI review,
- experience store/retrieval,
- skill metrics,
- replay,
- exit optimizer,
- self-evolution proposals.

---

## 5) Safety Boundaries (Hard Rules)

1. `allow_live=false` by default and guarded in runtime.
2. Nuwa cannot access execution interfaces.
3. OKX MCP/CLI adapters cannot execute without Trade Core-issued `OrderIntent`.
4. Internal execution protocol = structured JSON only (no NL instruction execution).
5. `UNKNOWN`/`NEUTRAL` direction cannot map to sell/short execution intent.
6. Open intent requires stop loss + take profit structure.
7. No real data => no fabricated PnL/win-rate/Sharpe/profit-factor.
8. Self-evolution outputs proposal artifacts only (`proposed_changes`), never auto-apply.
9. No automatic risk-increase changes (leverage, daily loss, max position).
10. Logs/journals must be redacted for secrets.

---

## 6) Mock-First vs Real Integrations

### Keep Mock in current safe scaffold
- Nuwa fast/deep evaluators.
- Smartmoney/sentiment adapters when provider unavailable.
- Demo execution return stubs when OKX CLI unavailable.

### Connect real OKX incrementally (later phases)
- Market ticker/candles/orderbook.
- Funding/OI endpoints.
- Account/positions snapshots.
- Demo trading execution adapter.

Live trading integration remains disabled until explicit future governance change.
