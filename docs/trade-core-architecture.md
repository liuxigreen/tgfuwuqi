# Trade Core Architecture (v1.2 Demo Full Loop)

- `trade_core` 是最终交易裁决层。
- Nuwa 只提供结构化评估/阻断建议/偏好，不可直接下单。
- OKX Agent Trade Kit 是能力层，不是策略脑。
- 系统内部执行协议必须是 `order_intent JSON`，不是自然语言。
- live 自动执行默认禁止。
- 当前目标是 demo full loop，不是真钱自主交易。

流程图：
`radar/signal -> OKX data -> Nuwa eval -> scoring -> risk -> decision -> order_intent -> demo/dry-run execution -> position management -> review/journal`
