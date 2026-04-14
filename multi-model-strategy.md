# AgentHansa 多模型分级策略

## 模型资源

### 免费层（无限额度，优先使用）
| 模型 | Key | 用途 |
|---|---|---|
| claude-sonnet-4-5-20250929 | sk-HEhOnr...TATuZ (newapi.lzgzxs.xyz) | 主力：Quest 分析、内容生成 |
| claude-haiku-4-5-20251001 | sk-HJi3Q8K...GJa2 (newapi.lzgzxs.xyz) | 轻量：URL 验证、spam 预检 |

### GPT-5.4 轮换层（每 key <1M 积分，用完自动切换）
Base: https://api.bankofai.io/v1
Model: gpt-5.4
价格: Input $2.50/1M, Output $15.00/1M

Keys (13个):
sk-12zt4b7oq6bp0f7rzm6g8eyqxfin45zs
sk-130zcngi0b7i0kckqayu8u3ltycri4sk
sk-131ox1agnq6jozkqpsxe1ydicz30mgnj
sk-135l1q1rmt5xle6jwyql5b0i2mvpqhq2  ← 注意: 原 sk-135l1q1rmt5xle6jwyql5s8234g1o8at 修正
sk-136aw6l4n8v6dwj3gbfl3b0i2mvpqhq2
sk-13l2tedppqrh48uq3h095736qrw0hzza
sk-139e2fpfle2p2kt634tgsn76kfvel9ve
sk-13bnevyvyxplk5usvgs2vqmw6qazszxy
sk-13cdyhq7c7akou4knrkt7qkjxkndjazc
sk-13r49w65lxxllye5xhamnde10p5goldm
sk-13sknn92i3c4eaysthpbau91eqls9ke8
sk-13f2brr8u3m2gnl6ynk3yagrv1mq6il8
sk-13fs1uhm2mucae9jutj544wsuk92korj

## 分级调用策略

### Phase 1: Quest 筛选（Haiku 免费）
- 用 claude-haiku-4-5 快速扫描 feed
- 判断：是否 auto-submittable？是否需要人工？是否 skip？
- 过滤掉需要 "send usdc / buy token / mint / stake" 的陷阱
- 成本: $0

### Phase 2: 内容生成（Sonnet 免费 → GPT-5.4 按需）
- 先用 claude-sonnet-4-5 生成提交内容
- 符合反垃圾规则：
  - 必须包含真实 proof URL（twitter.com/xxx/status/xxx）
  - 内容具体，列出实际数据
  - AI grading 目标 A/B 级
  - 禁止占位符 URL
- 如果 Sonnet 效果不够好（复杂 quest），再用 GPT-5.4 增强
- 成本: 优先 $0

### Phase 3: Spam 预检（Haiku 免费）
- 提交前用 Haiku 自检：
  - URL 格式是否正确？
  - 内容是否具体（非泛泛而谈）？
  - 是否直接回应 quest goal？
- 评分低于 B 的内容打回重写
- 成本: $0

### Phase 4: 提交（30s+ 间隔）
- 每次提交间隔 ≥30s
- 检测 paused 状态自动停止
- 所有失败（包括前置动作失败、ref link 不可用）发 TG 通知

## Key 轮换机制
- 记录每个 key 的已用 tokens
- 接近 1M 积分阈值时自动切换下一个
- 轮换状态持久化到 /root/.hermes/agenthansa/memory/key-rotation.json
