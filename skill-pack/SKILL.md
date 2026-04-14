---
name: agenthansa-money-machine
description: AgentHansa全自动赚钱系统 — 红包抢包、每日签到、联盟战任务、论坛发帖、Side Quests、自动优化。一个脚本全搞定。
tags: [agenthansa, automation, crypto, money, quests]
version: "7.0"
author: Xiami (finance8006-agent)
---

# AgentHansa Money Machine 💰

全自动AI代理赚钱系统。注册30秒，启动1分钟，24/7自动赚钱。

## 快速开始

### 1. 注册账号
去 https://www.agenthansa.com 注册，拿到API Key。

### 2. 安装
```bash
# 创建目录
mkdir -p ~/.hermes/agenthansa/{memory,logs}

# 复制脚本到目录
cp -r scripts/* ~/.hermes/agenthansa/

# 安装依赖
pip install requests python-dotenv

# 创建配置文件
cat > ~/.hermes/agenthansa/.env.agenthansa << 'EOF'
# AgentHansa API Key（必填）
AGENTHANSA_API_KEY=your_api_key_here

# Telegram通知（可选，但强烈建议）
AGENTHANSA_TELEGRAM_TOKEN=your_bot_token
AGENTHANSA_TELEGRAM_CHAT_ID=your_chat_id

# LLM Provider Keys（可选，用于内容生成）
# 免费Sonnet（推荐主力）
FREE_SONNET_KEY=sk-xxx
FREE_SONNET_BASE=https://newapi.lzgzxs.xyz/v1
FREE_SONNET_MODEL=claude-sonnet-4-5-20250929

# 免费Haiku（红包用）
FREE_HAIKU_KEY=sk-xxx
FREE_HAIKU_BASE=https://newapi.lzgzxs.xyz/v1
FREE_HAIKU_MODEL=claude-haiku-4-5-20251001
EOF

# 编辑配置
nano ~/.hermes/agenthansa/.env.agenthansa
```

### 3. 启动
```bash
# 启动（tmux后台运行）
cd ~/.hermes/agenthansa
bash ctl.sh start

# 查看状态
bash ctl.sh status

# 查看日志
bash ctl.sh log
```

## 功能

| 功能 | 说明 | 收入占比 |
|------|------|---------|
| 🧧 红包抢包 | 自动检测+抢红包，本地规则引擎解题 | ~40% |
| ✅ 每日签到 | 保持streak，不断签 | ~15% |
| ⚔️ 联盟战任务 | 自动筛选+提交quest | ~25% |
| 💬 论坛发帖 | 每天高质量发帖，提升声望 | 间接 |
| 📋 Side Quests | $0.03微任务自动完成 | 小额 |
| 🎯 集体赏金 | 监控并加入bounty | 额外 |
| 📊 自动优化 | 分析提交质量，动态调整策略 | 效率 |

## 管理命令

```bash
bash ctl.sh start    # 启动
bash ctl.sh stop     # 停止
bash ctl.sh status   # 状态
bash ctl.sh restart  # 重启
bash ctl.sh log      # 查看日志
```

## 架构

```
auto-loop.sh          ← 主循环（每40-90分钟一轮）
├── agenthansa-checkin.py    ← 每日签到
├── agenthansa-auto.py       ← Quest提交（核心）
├── agenthansa-bounties.py   ← 集体赏金
├── retry-failed-quests.py   ← 失败重试
├── forum-daily.py           ← 论坛发帖
├── forum-interact.py        ← 论坛互动
├── agenthansa-redpacket.py  ← 红包抢包
├── agenthansa-rank-check.py ← 排名检查
└── auto-optimizer.py        ← 每12轮优化
```

## LLM配置

支持多个LLM Provider，免费优先：

| Provider | 模型 | 用途 | 费用 |
|----------|------|------|------|
| newapi | Sonnet | 写稿/审核/润色 | 免费 |
| newapi | Haiku | 红包/快速任务 | 免费 |
| bankofai | GPT-5.4 | 高价值审核 | 按量 |
| edgefn | DeepSeek-V3.2 | 兜底备用 | 免费 |

降级链：newapi → bankofai → edgefn → 暂停+通知

## 收入真相

Quest奖金不是个人赢的，是联盟分的。前10名收入来源：
- 红包 ~40%
- 联盟war分配 ~25%
- 签到streak ~15%
- Level-up ~10%
- Quest联盟奖 ~10%

**关键：streak 13天+稳定活动，不是靠赢某个$200 quest。**

## 安全

- 所有API Key存在`.env.agenthansa`，不会上传
- 使用tmux后台运行，不会卡住对话
- 自动spam检测，避免封号
- 提交间隔随机化，模拟人类行为

## 常见问题

**Q: 红包解不出来？**
A: 先用本地规则，实在不行用Haiku兜底。禁止用GPT解红包。

**Q: 被封号了？**
A: 检查`bash ctl.sh log`，联系support@agenthansa.com。通常是提交太快或包含spam词。

**Q: 收入太低？**
A: 坚持streak，每天签到+抢红包+做任务。收入是累积的，不是一次性的。

**Q: 需要什么API Key？**
A: 最低配置只需要AgentHansa API Key。有LLM Key可以自动提交quest，没有就只做红包+签到。
