# OKX Agent Trade Kit Integration (v1.2)

## 分层
- market
- news/sentiment
- smartmoney
- account/positions
- spot/swap/futures/options（当前仅接 spot/swap demo）
- earn/bot/event（暂不接主交易链）

## v1.2 首批接入
- market/OI/funding
- sentiment/news（adapter + mock）
- smartmoney（adapter + mock）
- account/positions
- spot/swap demo execution

## 为什么先 CLI backend
- CLI 接入快、可测试、可观测。
- MCP backend 先保留接口，后续接入，不允许绕过 trade_core。

## 安装与配置
```bash
npm install -g @okx_ai/okx-trade-mcp @okx_ai/okx-trade-cli
okx config init
```

推荐 profile: `demo`

```bash
okx-trade-mcp --profile demo --modules all
okx-trade-mcp --profile live --read-only
```
