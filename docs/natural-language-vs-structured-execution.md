# Natural Language vs Structured Execution

- OKX Agent Trade Kit 支持自然语言下单，这适合人类交互和 agent 测试。
- `trade_core` 内部协议禁止使用自然语言作为执行协议。

正式链路必须是：

`Nuwa/radar/OKX data -> trade_core decision -> order_intent JSON -> okx_gateway deterministic call -> execution_result JSON`

安全原则：
- 女娲不能绕过 risk engine 直接下单。
- OKX MCP/CLI 工具不能绕过 trade_core。
- 任何执行都必须来自结构化 `order_intent`。
