# AgentHansa 自动化脚本

## 文件说明

| 文件 | 用途 |
|------|------|
| `agenthansa-auto.py` | 主自动提交脚本（人格轮换、质量评分、spam检测） |
| `auto-loop.sh` | 主循环（30min/轮，自动调optimizer） |
| `auto-optimizer.py` | V6自动优化器（24h窗口、递增封禁、proof URL权重） |
| `update_spam_words.py` | V2 Spam词库更新（forum API + 公告分析） |
| `agenthansa-sniper.py` | 红包狙击 |
| `agenthansa_redpacket_sniper.py` | 红包守护进程 |
| `key_rotation.py` | API key轮换 |
| `retry-failed-quests.py` | 失败quest重试 |
| `agenthansa_auto_pipelines.py` | 内容生成pipeline |
| `agenthansa-daily-report.py` | 每日报告 |
| `agenthansa-status-report.py` | 状态报告 |

## 配置

```bash
cp agenthansa/.env.example agenthansa/.env.agenthansa
# 编辑 .env.agenthansa 填入真实API keys
```

## 运行

```bash
bash auto-loop.sh
```

## Spam词库

`memory/spam_patterns.json` — 194词 + 91短语
自动更新：每12轮由auto-loop调用update_spam_words.py
