# tgfuwuqi — AI Crypto Trading Toolkit

自动化数字货币交易工具集：链上监控雷达、女娲蒸馏框架、OKX 交易脚本、量化研究数据。

## 目录结构

```
├── okx-trading/         # OKX 合约交易脚本（仓位监控/资金费率/自动交易）
├── radar/               # 热度做多雷达 + 叙事雷达
├── skills/              # 相关 Skill 文档（OKX CLI / 交易研究 / 女娲蒸馏）
├── nuwaswap/            # 女娲换手框架（回测引擎/妖币检测/蒸馏器）
├── distillation-data/   # 交易员Persona蒸馏数据（Obsidian知识库）
│   ├── Traders/         # xiaomustock / connectfarm1 蒸馏档案
│   ├── Signal Cases/    # 历史交易信号案例
│   └── _Templates/      # 蒸馏模板
├── trading-research/    # Moss.site 量化策略研究数据
└── README.md
```

## 核心项目

### NuwaSwap — 女娲换手框架
基于多时间框架的合约交易回测系统，包含：
- 4H 趋势剥头皮策略（EMA 8/100 + RSI）
- 100分妖币检测器（社交/流动性/叙事/风险四维评分）
- 千名交易员蒸馏框架
- 3年历史回测引擎

### 雷达系统
- **热度做多雷达**：CG热搜 + 负费率 + OI暴涨 三维扫描
- **叙事雷达**：链上叙事检测与跟踪

### OKX Agent Trade Kit
- CLI 交易操作手册
- 仓位自动监控 + SL/TP 平仓
- 资金费率扫描
- 自动信号交易

## 注意
所有 API Key / Token / 私钥 / 地址已被脱敏处理。
使用前需自行配置 `.env` 文件中的凭证。
