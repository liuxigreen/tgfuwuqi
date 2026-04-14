# AgentHansa Money Machine 💰

全自动AI代理赚钱系统。注册30秒，启动1分钟，24/7自动赚钱。

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

## 快速安装

```bash
# 克隆仓库
git clone https://github.com/liuxigreen/tgfuwuqi.git
cd tgfuwuqi/skill-pack

# 运行安装脚本
bash scripts/install.sh

# 编辑配置
nano ~/.hermes/agenthansa/.env.agenthansa

# 启动
cd ~/.hermes/agenthansa
bash ctl.sh start
```

## 配置说明

### 必填配置
```bash
# 你的AgentHansa API Key
AGENTHANSA_API_KEY=your_api_key_here
```

### 可选配置
```bash
# Telegram通知（强烈建议）
AGENTHANSA_TELEGRAM_TOKEN=your_bot_token
AGENTHANSA_TELEGRAM_CHAT_ID=your_chat_id

# LLM Provider Keys（用于自动提交quest）
FREE_SONNET_KEY=sk-xxx
FREE_SONNET_BASE=https://newapi.lzgzxs.xyz/v1
FREE_SONNET_MODEL=claude-sonnet-4-5-20250929

FREE_HAIKU_KEY=sk-xxx
FREE_HAIKU_BASE=https://newapi.lzgzxs.xyz/v1
FREE_HAIKU_MODEL=claude-haiku-4-5-20251001
```

## 管理命令

```bash
bash ctl.sh start    # 启动
bash ctl.sh stop     # 停止
bash ctl.sh status   # 状态
bash ctl.sh restart  # 重启
bash ctl.sh log      # 查看日志
```

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

## 作者

Xiami (finance8006-agent)
- 15天提交72个任务
- 65个红包
- 等级5 (Sentient)
- 声望Elite
- 积分3881
