# Trade Core Architecture (v1)

## 1) Trade Core 是什么

`trade_core` 是一个**交易决策中枢**，负责把多源信号统一到同一条可解释流程：

Radar Signal -> OKX 市场/情绪/聪明钱/账户确认 -> 女娲结构化评估 -> 评分 -> 风控 -> 决策 -> 订单意图 -> dry-run/demo 网关

它不是实盘机器人，也不承诺收益。

## 2) 模块分工

- **radar**: 负责“发现候选机会”。
- **distillation-data / 女娲**: 负责“结构化判断与交易阻断建议”。
- **okx-trading / OKX Agent Trade Kit**: 负责“市场信息与执行能力来源”。
- **trade_core**: 负责“统一评分 + 风控裁决 + 可回放决策输出”。

## 3) 为什么默认不实盘

加密市场高波动、高噪声。v1 目标是安全 MVP：先做到可解释、可复盘、受控输出。默认 `dry_run=True`、默认非自动交易，避免凭单信号直接下单造成失控风险。

## 4) 四种运行模式

- `observe`: 只观察，不建议执行。
- `propose`: 生成建议与订单意图（dry-run）。
- `demo_auto`: 仅 demo/dry-run 自动路径。
- `live_guarded`: 默认仍禁止真实执行；仅在配置明确 `allow_live_execution: true` 且代码二次确认时才可放开。

## 5) v1 接入的 OKX 五类能力

1. 市场筛选 / OI / Funding
2. 情绪雷达 / 新闻风险
3. 聪明钱方向与溢价判断
4. 账户 / 持仓 / 风控确认
5. 基础执行（仅 order intent + dry-run 输出）

## 6) 后续扩展

- Earn
- Bot/Grid
- Options
- Event contracts
- Replay/backtest pipeline
- 多女娲版本并行打分与对照
