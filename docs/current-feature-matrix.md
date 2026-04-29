# Current Feature Matrix (Based on Architecture)

> Scope: current branch implementation status after stabilization.  
> Legend: ✅ implemented, 🧪 implemented with mock fallback, 🚧 scaffold/interface only, ⛔ intentionally blocked.

## 1) Runtime Modes
- ✅ `observe`: observation-only decision path.
- ✅ `propose`: produces decision + order_intent preview without execution.
- ✅ `demo_auto`: gated execution path (demo/dry-run).
- ⛔ `live_guarded`: live auto trading disabled by policy/default config.

## 2) Fast Path (signal -> decision)
- ✅ Signal normalization and pipeline orchestration.
- ✅ Parallel enrichment hooks for market/account/OI/funding/sentiment/smartmoney.
- 🧪 Fast Nuwa structured evaluation (mock-capable).
- ✅ Score breakdown + risk gating + daily limits gating.
- ✅ Exit policy selection wiring.
- ✅ OrderIntent generation and execution gating.
- ✅ Latency measurement and budget-oriented checks.

## 3) Slow Path (review/learning)
- ✅ Daily review command path and summary output.
- ✅ Decision snapshot and replay/report plumbing.
- ✅ Outcome evaluation and AI review scaffolds.
- ✅ Experience store/retriever scaffolds.
- 🚧 Advanced calibration/optimizer quality still scaffold-level.

## 4) Safety Boundaries
- ✅ `allow_live=false` and `allow_trade_execution=false` default posture.
- ✅ Nuwa output is structured eval; no direct execution interface.
- ✅ Execution contract uses structured `order_intent` JSON.
- ✅ UNKNOWN/NEUTRAL direction guarded against executable short/sell paths.
- ✅ Self-evolution is proposal-only (`proposed_changes`), no auto-apply.
- ✅ Missing real outcomes -> null/insufficient-sample style metrics (no fabricated PnL claims).

## 5) OKX Gateway
- ✅ Read-style gateway interfaces for market/account/OI/funding style access.
- 🧪 Mock backend available and used when CLI/provider unavailable.
- ✅ `okx-check` reports backend/availability explicitly.
- ⛔ Direct bypass execution outside Trade Core decision pipeline is not intended.

## 6) Exit Policy + Position Management
- ✅ Exit policy models/templates/selector/evaluator wiring exists.
- ✅ Position management action framework exists (`HOLD/REDUCE/TIGHTEN_STOP/EXIT...`).
- ✅ Order intent carries exit-related fields for controlled execution paths.
- 🚧 Policy optimization remains non-authoritative (slow-path/scaffold usage).

## 7) Observability
- ✅ Journal records decision/execution artifacts.
- ✅ Decision snapshots available for replay/review flows.
- ✅ CLI commands for config validation, fast signal path, limits status, daily review, self-evolve, and gateway check.

## 8) What is intentionally not enabled
- ⛔ Live auto-trading.
- ⛔ Nuwa direct order placement.
- ⛔ Self-evolution automatic risk-raising config changes.
- ⛔ Fast Path deep analysis workloads (deep Nuwa/replay/optimizer/search).
