# Learning Loop v1

- 决策后写入 `decision_snapshot`（journal + `data/decision_snapshots/*.jsonl`）。
- 默认按 4h/24h/72h 做 outcome 回访；无价格数据输出 `data_unavailable`。
- AI reviewer 仅 slow path 运行，输出结构化 review，不改配置。
- 经验库记录 lesson + when_to_apply + when_not_to_apply + evidence。
- Fast Path 仅可用本地 Top-K 经验检索，200ms 超时即跳过。
- 经验只能加权评分/风控偏好，不能绕过 risk engine/order_intent。
- feedback 只进学习闭环，不允许直接改规则。
- calibration 用于判断过度自信，低样本只输出 low_confidence。
