# tgfuwuqi — AI Crypto Trading Toolkit

自动化数字货币交易工具集：链上监控雷达、OKX 交易脚本、交易员蒸馏数据。

## 目录结构

```
├── okx-trading/         # OKX 合约交易脚本（仓位监控/资金费率/自动交易）
├── radar/               # 热度做多雷达 + 叙事雷达
├── skills/              # 相关 Skill 文档（OKX CLI / 交易研究 / 女娲蒸馏）
├── distillation-data/   # 交易员Persona蒸馏数据（Obsidian知识库）
│   ├── Traders/         # xiaomustock / connectfarm1 蒸馏档案
│   ├── Signal Cases/    # 历史交易信号案例
│   └── _Templates/      # 蒸馏模板
└── README.md
```

## 核心项目

### 雷达系统
- **热度做多雷达**：CG热搜 + 负费率 + OI暴涨 三维扫描
- **叙事雷达**：链上叙事检测与跟踪

### OKX Agent Trade Kit
- CLI 交易操作手册（`okx --json`）
- 仓位自动监控 + SL/TP 平仓
- 资金费率扫描
- 自动信号交易

### 交易员蒸馏
基于 [女娲·Skill造人术](https://github.com/alchaincyf/nuwa-skill) 官方框架：
- **川沐** @xiaomustock — 庄家操纵/鱼尾行情/开口空洞框架
- **潜水观察员** @connectfarm1 — 费率雷达/庄家收筹雷达/龙头战法

## 注意
所有 API Key / Token / 私钥 / 地址已被脱敏处理。
使用前需自行配置 `.env` 文件中的凭证。


## Trade Core

Trade Core 是交易决策中枢，用于把女娲蒸馏、雷达信号和 OKX Agent Trade Kit 数据统一成可解释、可回放、受风控约束的交易决策。

默认不实盘，默认 dry-run。

### Quick demo

python -m trade_core.cli validate-config
python -m trade_core.cli demo --sample examples/full_case.json

### Stabilization Status (Salvage Patch)

当前分支保留了 Trade Core scaffold，并完成稳定性收口（不新增功能）：
- Python 模块可编译（`python -m compileall trade_core`）。
- 全量测试可通过（`python -m pytest`）。
- 最小 CLI 验收命令可运行（含 `validate-config` / `fast-signal` / `limits-status` / `daily-review` / `self-evolve` / `okx-check`）。
- 当前版本仍为 **Safe Demo Scaffold**，`allow_live=false` 且 `allow_trade_execution=false`，禁止 live 自动交易。
