# 交易员蒸馏知识库

## 目录结构

```
Obsidian Vault/
├── README.md                          # 本文件
├── _Templates/
│   └── trader-distillation-template.md   # 交易员蒸馏模板
├── Traders/                             # 交易员蒸馏目录
│   ├── xiaomustock/                     # 川沐（已完成）
│   │   ├── SKILL.md                     # 核心蒸馏文件
│   │   ├── Writings/                   # 推文/文章素材
│   │   ├── Research/                   # 研究分析
│   │   ├── Validation/                 # 质量测试
│   │   └── Demo/                       # Demo对话
│   └── <next-trader>/                  # 下一个交易员（待添加）
├── Signal Cases/                        # 代币信号案例库
│   └── Crypto/
│       ├── 2023-11-10-TRB-GAS-LOOM-boom-dump.md
│       ├── 2023-11-27-ARK-case-study.md
│       ├── 2023-11-12-25percent-rule-GAS.md
│       └── 2025-04-17-opening-gap-framework.md
└── Twitter Archive/                     # 推特内容分类存档
    └── xiaomustock/
        └── （按主题/时间分类的推文存档）
```

## 工作流程

### 1. 蒸馏新交易员

1. 在 `Traders/` 下创建新目录 `<handle>/`
2. 使用 `_Templates/trader-distillation-template.md` 作为模板
3. 收集推文内容，分类存入 `Writings/`
4. 完成研究分析，存入 `Research/`
5. 编写 `SKILL.md`
6. 测试验证，存入 `Validation/`
7. 编写 Demo对话，存入 `Demo/`

### 2. 提取信号案例

将交易员推文中的具体交易信号/案例提取出来，存入 `Signal Cases/Crypto/`，便于后续：
- 模拟交易回测
- 框架验证
- 多交易员信号对比

### 3. 存档推特内容

将原始推文按以下维度分类存档到 `Twitter Archive/<handle>/`：
- **按时间**：YYYY-MM-主题.md
- **按主题**：庄家操盘/风险提醒/框架分享/实盘记录/吐槽/其他
- **按币种**：如果涉及具体代币，单独归档

## 已完成的蒸馏

| 交易员 | Handle | 时间范围 | 状态 | 评分 |
|--------|--------|----------|------|------|
| 川沐 | xiaomustock | 2023-2026 | ✅ 完成 | 89/100 |

## 待蒸馏交易员

（待用户提供）

## 使用目标

1. **阶段一**：蒸馏足够多的交易员（5-10个），形成多元化视角
2. **阶段二**：开始模拟交易 —— 同一市场状态下，不同交易员会怎么看
3. **阶段三**：模拟盘交易 —— 基于多视角共识进行小额模拟
4. **阶段四**：实盘交易 —— 在有明确信号和共识时进行小额实盘

---

> 最后更新：2026-04-27
