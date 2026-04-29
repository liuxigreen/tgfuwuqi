# Implementation Plan (Phased Stabilization)

## Phase 1 — Clean Safe Demo Scaffold
**Goal:** minimal runnable and safe baseline.

- `python -m compileall trade_core` passes.
- `python -m pytest` passes.
- `python -m trade_core.cli validate-config` passes.
- `fast-signal --mode propose` runs successfully.
- `demo_auto` is gated to dry-run/demo path only.
- `live_guarded` remains blocked.

**Exit criteria:** CI green + safety defaults enforced (`allow_live=false`, `allow_trade_execution=false`, `dry_run=true`).

## Phase 2 — OKX Read-only + Demo Adapter
- Stable adapter interfaces for market/account/OI/funding.
- Stable adapter interfaces for sentiment/smartmoney.
- Demo execution path guarded by risk + mode + exit policy constraints.

**Exit criteria:** adapters return structured snapshots; failures return warnings not crashes.

## Phase 3 — Exit Policy + Position Management
- Enforce per-open-intent mandatory stop/tp fields.
- Implement post-entry decision matrix (hold/reduce/exit/tighten).
- Add thesis invalidation and time-stop handling.

**Exit criteria:** cannot produce executable open intent without valid exit policy.

## Phase 4 — Journal + Daily Review
- Every decision writes snapshot/journal with redaction.
- Daily review pipeline computes metrics only from real evidence.
- No fabricated PnL or win metrics when missing data.

**Exit criteria:** missing data -> `data_unavailable` / `insufficient_sample_size`.

## Phase 5 — Learning Loop
- Outcome evaluation + AI review.
- Experience store + retrieval.
- Calibration hooks.

**Exit criteria:** learning artifacts are advisory and traceable to evidence.

## Phase 6 — Skill Intelligence
- Skill registry/classifier/router/metrics foundation.
- Read-only governance on risky skills.

**Exit criteria:** no auto-enable of live/risky skills; no execution bypass.

## Phase 7 — Self-Evolution Proposal
- Generate `proposed_changes` with evidence.
- Mandatory human approval workflow.
- Explicit block on auto risk increases.

**Exit criteria:** no direct runtime config mutation from self-evolution.
