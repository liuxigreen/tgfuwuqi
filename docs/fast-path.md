# Fast Path

- 目标：约 4 秒内完成 `signal -> decision -> order_intent -> demo/dry-run execution`。
- Fast Path 仅包含：信号标准化、并行数据拉取、Fast Nuwa、评分、风控、意图、执行。
- Slow Path 负责：daily review、replay、deep nuwa、self-evolution。
- Fast Path 不做：skill discovery/deep nuwa/replay/长报告。
- 必须新鲜：market/account。
- 可降级：sentiment/smartmoney（受配置控制）。
- 超时处理：超预算降级 propose 或 blocked；demo_auto 不执行。
