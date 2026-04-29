# Current PR Risk Review (Stabilization Assessment)

## Scope and method
Reviewed current `trade_core/`, `configs/`, `tests/`, and existing docs with compile/test/CLI validation runs.

## 1) 哪些文件不可编译
- At current HEAD, no non-compilable Python files were found in `trade_core/` based on `python -m compileall trade_core`.
- Compilation status: **PASS**.

## 2) 哪些 YAML 解析风险
- `trade_core.cli validate-config` can load all expected config documents and required keys.
- Direct `yaml.safe_load` validation could not be executed in this environment because `PyYAML` is not installed.
- Residual risk: external strict YAML tooling may differ; recommend adding a pinned YAML validator in CI.

## 3) 哪些模块可以保留
Keep as scaffold foundations:
- core pipeline: `fast_path.py`, `decision.py`, `scoring.py`, `risk.py`, `daily_limits.py`, `order_intent.py`.
- safety/runtime: `okx_gateway.py`, `config.py`, `cli.py`, `journal.py`, `latency.py`, `models.py`.
- exit controls: `exit_policy/*`.
- post-trade baseline: `position_manager.py`, `reporting.py`, `replay.py`.

## 4) 哪些模块应该重写（优先重构，不是立即删除）
- `skill_intelligence/*`: keep interfaces, reduce runtime coupling, move heavy logic to slow path.
- `learning_loop/*`: keep contracts, tighten data quality gating and reduce side effects.
- `self_evolution/*`: keep proposal-only behavior, isolate metrics from missing-data paths.

## 5) 哪些功能只是 mock
- Nuwa evaluators are mock/structured stub style by design in current scaffold.
- OKX check currently reports missing CLI and falls back to mock backend when unavailable.
- sentiment/smartmoney adapters may operate in mock mode depending on provider availability.

## 6) 当前能不能 merge
**Conditional YES (as Safe Demo Scaffold)** if project accepts:
- no live auto-trading,
- mock-heavy integrations,
- proposal-only evolution.

Not suitable to market as live trader.

## 7) merge 前最小验收标准
Must all pass before merge:
1. `python -m compileall trade_core`
2. `python -m pytest`
3. `python -m trade_core.cli validate-config`
4. `python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode propose`
5. `python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode demo_auto`
6. `python -m trade_core.cli limits-status`
7. `python -m trade_core.cli daily-review --date <YYYY-MM-DD>`
8. `python -m trade_core.cli self-evolve --date <YYYY-MM-DD>`
9. `python -m trade_core.cli okx-check`

## Direct answers to requested architecture acceptance questions
1. **MVP**: Safe Demo Scaffold (propose + demo/dry-run + full risk gating + journaling).
2. **Must do first**: compile/test stability, config validation, fast-path gating, order-intent safety.
3. **Must do later**: deep Nuwa, optimizer, advanced skill intelligence automation.
4. **Not in fast path**: deep review/replay/self-evolution/optimizer/skill discovery/web search.
5. **4-second guarantee**: parallel adapters + per-adapter timeouts + degraded-mode rules + latency budget checks.
6. **Nuwa no direct order**: Nuwa outputs data contract only; no gateway imports/execution handle.
7. **No MCP bypass**: execution adapter requires Trade Core-issued `OrderIntent` + mode/risk checks.
8. **No stop-loss no open**: hard validator in `order_intent` + exit policy mandatory for executable open intents.
9. **No fake metrics**: absent outcomes => `data_unavailable`/`insufficient_sample_size`, null metrics.
10. **Self-evolution proposal-only**: emit `proposed_changes` artifacts, never auto-apply runtime config.
