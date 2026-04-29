# OKX 模拟盘接入说明（Agent Integration Pack）

> 目标：让外部 Agent 能以**安全、可控、可审计**方式接入 Trade Core，并用于 OKX 模拟盘测试。  
> 范围：仅 demo / dry-run；不启用 live 自动交易。

## 1. 总体接入拓扑

Agent 不直接下单，必须走：

`Agent -> trade_core.cli fast-signal/pipeline -> Trade Core 风控裁决 -> OKX Gateway demo/dry-run`

禁止：
- Agent 直接调用 OKX 下单命令绕过 Trade Core。
- Agent 发送自然语言“直接开仓”作为内部执行协议。

## 2. 最小可运行前置

1) 环境检查
- Python 3.10+
- 可执行命令：
  - `python -m trade_core.cli validate-config`
  - `python -m trade_core.cli okx-check`

2) 安全配置（必须）
- `configs/okx_gateway.yaml`
  - `allow_live: false`
  - `allow_trade_execution: false`
  - `backend: mock` 或 demo 适配器
- `configs/operating_modes.yaml`
  - `default_dry_run: true`

## 3. Agent 调用协议（建议）

### 3.1 信号输入（RadarSignal）
Agent 提供结构化输入字段：
- `symbol`（例：`BTC-USDT-SWAP`）
- `market_type`（`swap/spot`）
- `direction_hint`（`long/short/neutral/unknown`）
- `features`（OI/Funding/情绪等）
- `timestamp`

### 3.2 决策调用
- 推荐命令：
  - `python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode propose`
  - `python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode demo_auto`

### 3.3 输出消费
Agent 必须消费并记录：
- `decision.action`
- `decision.blocked_reasons`
- `order_intent`（结构化）
- `execution_result`
- `latency_summary`

## 4. 模式策略（供 Agent 使用）

- `observe`：仅观察，策略研究阶段。
- `propose`：生成建议，不执行。
- `demo_auto`：仅在通过风控、时延预算、exit policy 完整时允许 demo 执行。
- `live_guarded`：当前禁用。

## 5. 风控与执行硬规则（Agent 必须遵守）

1. UNKNOWN/NEUTRAL 不得映射可执行 sell/short。
2. 开仓 intent 必须有 stop_loss / take_profit 结构。
3. 超过日限额、风控失败、快照过期 -> 必须 blocked。
4. Nuwa 仅提供结构化评估，不具备执行权限。
5. self-evolution 只读 proposal，不得自动改交易参数。

## 6. 配分说明（给 Agent 的权重解释）

来自 `configs/scoring_weights.yaml` 的核心思想：
- `market_score`：市场结构健康度
- `oi_score`：持仓量结构信号
- `funding_score`：资金费率拥挤度
- `sentiment_score`：情绪一致性
- `smart_money_score`：聪明钱方向一致性
- `nuwa_score`：女娲结构化评估加权
- `risk_penalty`：风控惩罚（扣分项）

建议 Agent 解释模板：
- “高分不代表必开仓，必须先过 risk + daily_limits + exit_policy 完整性。”
- “risk_penalty 上升时，优先转 propose/observe，不追求成交。”

## 7. 对接外部 OKX 模拟盘的最小步骤

1. 保持 Trade Core 为决策中枢，外部 Agent 只负责喂信号与消费输出。
2. 先跑 `propose` 模式观察 1~3 天（或固定样本）。
3. 再开 `demo_auto`，但保留 `allow_live=false`。
4. 每日使用 `daily-review` 与 `self-evolve` 产出复盘报告。
5. 仅人工审核后调整配置，不自动应用 proposal。

## 8. 推荐验收命令（接入前）

- `python -m compileall trade_core`
- `python -m pytest`
- `python -m trade_core.cli validate-config`
- `python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode propose`
- `python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode demo_auto`
- `python -m trade_core.cli limits-status`
- `python -m trade_core.cli daily-review --date 2026-04-29`
- `python -m trade_core.cli self-evolve --date 2026-04-29`
- `python -m trade_core.cli okx-check`

## 9. 交付给 Agent 的最小字段清单

输入（Agent -> Trade Core）
- symbol, market_type, direction_hint, features, timestamp

输出（Trade Core -> Agent）
- decision_id, action, final_score, confidence
- blocked_reasons, warnings
- order_intent (full JSON)
- execution_result
- journal_path / decision_snapshot_path
- latency_summary

---

当前版本定位：**Safe Demo Scaffold for OKX 模拟盘联调**，不是 live 自动交易器。
