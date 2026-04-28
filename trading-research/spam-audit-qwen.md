# Xami Spam 风险审计报告

**分析对象**: XiaMi (quest-submission agent) 提交记录  
**数据来源**: `submission-history.jsonl`  
**记录总数**: 11 条  
**时间跨度**: 2026-04-10 05:30 – 06:15 UTC (~45分钟)

---

## 一、逐条记录分析

| # | 时间 (UTC) | Quest | 状态 | 间隔 | 字数 | 人格 | 错误 |
|---|-----------|-------|------|------|------|------|------|
| 1 | 05:30:00 | Reddit AI search | ❌ failed | — | 103 | practitioner | HTTP 400: 缺少 proof_url |
| 2 | 05:33:03 | Tweet AgentHansa | ❌ failed | 3m03s | 165 | practitioner | HTTP 400: 缺少 proof_url |
| 3 | 05:41:02 | Tweet AgentHansa | ❌ failed | 7m59s | 167 | analyst | HTTP 400: 缺少 proof_url |
| 4 | 05:44:05 | Tweet AgentHansa | ❌ failed | 3m03s | 156 | teacher | HTTP 400: 缺少 proof_url |
| 5 | 06:16:54 | Tweet AgentHansa | ❌ failed | 32m49s | 128 | critic | HTTP 400: 缺少 proof_url |
| 6 | 06:19:37 | Tweet AgentHansa | ❌ failed | 2m43s | 115 | analyst | HTTP 400: 缺少 proof_url |
| 7 | 06:30:42 | Reddit AI search | ❌ failed | 11m05s | 175 | practitioner | HTTP 400: 缺少 proof_url |
| 8 | 06:34:15 | Tweet AgentHansa | ❌ failed | 3m33s | 142 | practitioner | HTTP 400: 缺少 proof_url |
| 9 | 07:19:14 | Tweet AgentHansa | ❌ failed | 44m59s | 182 | teacher | HTTP 400: 缺少 proof_url |
| 10 | 08:31:30 | LinkedIn Company Page | ✅ submitted | 72m16s | 133 | teacher | 无 |
| 11 | 08:35:08 | Brand Positioning | ✅ submitted | 3m38s | 152 | critic | 无 |

---

## 二、Spam 信号分析

### 1. 重复提交同一 Quest（⚠️ 高危信号）
- **`ef08f214` (Tweet AgentHansa)**: 重复提交 **7次**，全部失败（缺少 proof_url）
- **`5ed289f9` (Reddit AI search)**: 重复提交 **2次**，全部失败（缺少 proof_url）
- 同一 quest ID 反复重试 = **velocity breaker 典型触发模式**

### 2. 间隔时间分析（⚠️ 多处危险）

| 间隔区间 | 时长 | 风险等级 |
|---------|------|---------|
| 记录 1→2 | 3m03s | 🟡 接近危险线 |
| 记录 2→3 | 7m59s | ✅ 安全 |
| 记录 3→4 | 3m03s | 🟡 接近危险线 |
| 记录 4→5 | 32m49s | ✅ 安全（长暂停） |
| 记录 5→6 | 2m43s | 🔴 **<3min，危险** |
| 记录 6→7 | 11m05s | ✅ 安全 |
| 记录 7→8 | 3m33s | 🟡 接近危险线 |
| 记录 8→9 | 44m59s | ✅ 安全（长暂停） |
| 记录 9→10 | 72m16s | ✅ 安全 |
| 记录 10→11 | 3m38s | 🟡 接近危险线 |

**Velocity Breaker 触发**: 记录 5→6 间隔仅 **2m43s**，低于 2min 安全线。

### 3. 错误模式分析（🔴 系统性失败）
- **11条中9条失败**（81.8% 失败率）
- **全部 9 次失败** 原因相同：`HTTP 400: 缺少 proof_url`
- 这意味着 Xiami 连续 9 次提交都未附带 proof_url，属于**同一 bug 反复触发**
- 平台视角：**大量无效请求 = 低质量 agent 行为**，可能触发自动降权

### 4. 字数分析（⚠️ 部分偏低）

| 范围 | 记录数 | 风险 |
|------|--------|------|
| <120 字 | 2条 (#1: 103, #6: 115) | 🟡 偏低 |
| 120-150 字 | 4条 | ✅ 正常 |
| 150-180 字 | 3条 | ✅ 正常 |
| >180 字 | 2条 | ✅ 正常 |

- 平均字数: **147 字**（中位数: 152）
- 最低 103 字（Reddit comment）—— Reddit 通常需要更实质性的内容

### 5. 人格分布
- practitioner: 5次
- teacher: 3次
- analyst: 2次
- critic: 2次
- 人格有轮换，不是单一模式重复。

---

## 三、与 AgentHansa 平台规则对比

| 规则 | Xiami 表现 | 状态 |
|------|-----------|------|
| 间隔 <2min 危险 | 1次 2m43s（记录5→6） | ⚠️ 接近但未低于2min |
| 间隔 <3min 可疑 | 2次 <3min（记录1→2, 3→4, 5→6） | 🔴 可疑 |
| 同一 quest 反复提交 | Tweet 提交 7 次 | 🔴 高危 |
| 重复内容风险 | 同一 tweet quest 切换人格但本质相同内容 | 🔴 高 |
| proof_url 缺失（9次） | 系统性 bug | 🔴 高危 |
| 字数 <100 | 无（最低103） | ✅ 通过 |
| 失败率 >80% | 81.8% | 🔴 高危 |

---

## 四、Spam 风险评分

# 📊 Spam 风险评分: **68/100**（中高危险）

### 风险构成

| 风险项 | 权重 | 得分 | 说明 |
|--------|------|------|------|
| 同一 quest 重复7次 | 25% | 23/25 | 极高重复频率 |
| 系统性 proof_url 缺失 | 25% | 22/25 | 9次相同错误=bug未修复 |
| 失败率 81.8% | 15% | 13/15 | 极高，平台会标记 |
| 间隔 <3min (3次) | 15% | 10/15 | 接近 velocity 触发线 |
| 字数偏低 (2条<120) | 10% | 3/10 | 轻微风险 |
| 内容多样性不足 | 10% | 5/10 | 仅2个quest被反复提交 |

---

## 五、具体风险点

1. 🔴 **Velocity Breaker 边缘触发**: 记录5→6间隔2m43s，加上7次同一quest，平台极可能已标记为异常
2. 🔴 **proof_url 系统性缺失**: 9次相同 HTTP 400 错误，平台会将此 agent 标记为低质量
3. 🔴 **内容重复**: 同一 Tweet quest 提交7次，切换人格但内容结构高度相似
4. 🟡 **失败率过高**: 81.8% 失败率远超正常水平（正常应 <20%）
5. 🟡 **字数偏低记录**: #1(103字) 和 #6(115字) 可能被降权
6. 🟡 **时间窗口密集**: 前9条集中在 ~90分钟内，其中7条为同一quest

---

## 六、建议

1. **立即修复 proof_url 缺失** — 这是 9 次失败的根本原因
2. **同一 quest 失败后等待 ≥10min 再重试**，避免 velocity breaker
3. **失败超过2次后切换 quest**，不要死磕同一个
4. **字数保持在 150+**，低于 120 的内容可能被降权
5. **增加 quest 多样性**，避免在同一时间段重复提交同一任务
6. 考虑是否需要**冷却期**（当前已有较长间隔，行为在改善）

---

*审计报告生成时间: 2026-04-12*
