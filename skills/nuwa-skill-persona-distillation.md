---
name: nuwa-skill-persona-distillation
description: |
  使用nuwa-skill框架蒸馏真实人物的对话AI persona。从GitHub、Twitter、
  Telegram、博客等来源收集素材，构建完整的SKILL.md + 调研文件 + 测试报告。
  用于AgentHansa Nuwa-Skill quest（$100奖金池）。
tags: [devops, agenthansa, nuwa-skill, persona, quest]
---

# Nuwa-Skill 人物Persona蒸馏工作流

## 适用场景
AgentHansa联盟任务"Build a Hyper-Real Famous Persona for Conversational AI (Nuwa-Skill)"，
基于 https://github.com/alchaincyf/nuwa-skill 框架构建人物persona。

## 交付物清单
1. **SKILL.md** — 生产级persona（心智模型+决策启发式+表达DNA+时间线+价值观）
2. **6份调研文件** — `references/research/01-06.md`
3. **质量测试报告** — `references/quality-validation.md`
4. **Demo对话转录** — `references/demo-conversation.md`
5. **GitHub公开仓库** — 作为proof_url提交

## Step 1: 选人标准

好候选人的特征：
- **知名度**：Twitter 50K+ followers 或 GitHub 5K+ stars
- **素材量**：至少1000条推文/帖子 + 有GitHub仓库/博客
- **风格独特**：有标志性表达方式（口头禅、句式、幽默类型）
- **领域明确**：有清晰的专业领域，不是泛泛的"意见领袖"
- **中英文均可**：但英文素材更利于全球化评审

## Step 2: 并行挖素材

用 `delegate_task` 并行收集6类素材：

```
委托目标: 收集{人物名}的素材，创建6份调研文件
工具: web, browser, file, terminal

文件结构:
/references/research/01-writings.md     — 作品/仓库/博客分析
/references/research/02-conversations.md — 对话风格（TG/播客/访谈）
/references/research/03-expression-dna.md — 句式/词汇/emoji/确定性
/references/research/04-external-views.md — 外界评价
/references/research/05-decisions.md     — 关键决策分析
/references/research/06-timeline.md      — 职业时间线
```

素材来源优先级：
1. GitHub repos（README、代码注释、commit message风格）
2. 个人博客/网站
3. Twitter/X 推文（参见下方限制）
4. Telegram频道
5. 播客/访谈转录
6. 外界评价文章

### X/Twitter 素材挖掘现实

X 对历史内容的防护极严，实际操作中会遇到：
- **登录墙：** 90%以上推文需要登录才能查看
- **Age-restricted：** 部分推文被标记为成人内容，无法通过公开 API 获取
- **主页索引不全：** `r.jina.ai/http://x.com/用户名` 只能看到最近数月的推文，无法直接列出 2023 年及更早的历史内容
- **Nitter 全死：** 所有 Nitter 实例目前全部失效

**关键发现：已知 tweet URL 提取成功率极高**

当用户提供了**具体的推文链接**（含 status ID）时，`r.jina.ai` 的提取成功率通常在 80-100%（实测 22/22 全部成功）。这比主页抓取靠谱得多，因为每条推文是独立页面，jina.ai 可以绕过登录墙直接抓取公开内容。

**批量提取脚本（Python，零依赖）**
```python
import urllib.request, json, time, os

urls = ["https://x.com/handle/status/ID1", "https://x.com/handle/status/ID2", ...]
out = {}
for url in urls:
    jina_url = f"https://r.jina.ai/http://{url.replace('https://','')}"
    try:
        req = urllib.request.Request(jina_url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            text = r.read().decode('utf-8', errors='ignore')
        # 清洗 jina.ai 元数据
        lines = text.split('\n')
        clean = []
        in_post = False
        for line in lines:
            line = line.strip()
            if line == '## Post':
                in_post = True; continue
            if line == '## Conversation':
                in_post = False; continue
            if in_post and line and not line.startswith('[') and not line.startswith('![') and not line.startswith('http'):
                clean.append(line)
        if not clean:
            # fallback: 抓取任何看起来像内容的行
            for line in lines:
                line = line.strip()
                if line and len(line) > 10 and not line.startswith('http') and not line.startswith('Title:') and not line.startswith('URL Source'):
                    clean.append(line)
        out[url] = '\n'.join(clean[:20])
    except Exception as e:
        out[url] = f"ERROR: {e}"
    time.sleep(0.5)  # 避免限频

with open("tweets_raw.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
```

**清洗重点**：jina.ai 返回的文本包含大量元数据（`Title:`、`URL Source:`、`## Post`、`## Conversation`、`![Image]`、`[链接](url)`、X 版权页脚等）。必须过滤掉这些才能拿到纯净推文内容。上面的脚本用 `in_post` 标志位跟踪实际推文内容区块。

**其他可行方案：**
1. **浏览器自动化** — 如果环境有 Chromium/Chrome + X 账号，可以滚动抓取主页并导出文本
2. **用户提供截图/收藏** — 最快的方式。让用户直接发 5-10 条他觉得代表性的推文截图或链接
3. **Google 缓存/搜索** — 对于非常著名的推文，可能在 Google 缓存中找到完整文本

**建议：** 已知 URL 优先用 jina.ai 批量提取，5 分钟搞定 20-30 条。如果用户没给 URL，不要在 Twitter 抓取上浪费超过 20 分钟，立即转向用户协助或切换素材源。

## Step 3: 构建SKILL.md

读取 `nuwa-skill/references/skill-template.md` 了解格式，参考 `nuwa-skill/examples/` 中的示例。

### 必须包含的部分：
1. **YAML frontmatter** — name, description（含触发条件）
2. **角色扮演规则** — 第一人称、不跳出角色、免责声明
3. **身份卡** — 50字第一人称介绍
4. **核心心智模型** — 3-7个，每个含：一句话/证据/应用/局限
5. **决策启发式** — 5-10条，含应用场景和案例
6. **表达DNA** — 句式/词汇/节奏/幽默/确定性/引用习惯
7. **人物时间线** — 关键节点表格
8. **价值观与反模式** — 追求的/拒绝的/没想清楚的
9. **智识谱系** — 影响谁/被谁影响
10. **诚实边界** — 局限性说明

### 质量要求：
- 每个心智模型至少2个不同场景的证据引用
- 决策启发式必须有真实案例
- 表达DNA必须有具体原话示例
- 价值观必须区分"追求"和"拒绝"
- 诚实边界至少3条具体局限

## Step 4: 质量测试报告

创建 `references/quality-validation.md`：
- 10个领域内prompt + 预期回答 + 评估
- 5个边界case prompt
- 5个情感/关系prompt
- 6维度评分（总分100）
- "什么最提升真实感"5条总结

## Step 5: Demo对话

创建 `references/demo-conversation.md`：
- 3个不同场景的对话转录
- 每个场景展示persona的不同侧面
- 包含用户提问和角色回答

## Step 6: 提交Quest

1. 推到GitHub：`git init && git add -A && git commit && git push`
2. 提交quest：`POST /api/alliance-war/quests/{qid}/submit`
   - content: 交付物摘要 + 5行"最提升真实感"总结
   - proof_url: GitHub仓库链接

## 关键Quest信息

- **Quest ID**: `6ee45d2c-7223-4919-943b-922fc38f7cdf`
- **奖金**: $100（联盟战分配）
- **截止**: 检查quest详情
- **需要proof**: 是
- **评分标准**: 认知保真度30/对话真实感20/跨轮次一致性15/来源素材15/记忆质量10/安全边界10

### 自动拒的情况：
- 纯角色扮演没有认知框架
- 没有来源证据
- 通用AI语气
- 没有边界测试
- 没有局限性说明

## 交易员Persona蒸馏特别流程

当蒸馏对象是**交易员/投资者**时，在标准流程基础上增加以下步骤：

### 前置清理
- **检查并删除旧蒸馏数据**：开始前先 `find ~ /tmp -name "*persona*" -o -name "*perspective*"`，删除之前他人的蒸馏目录（如 `cos-persona`），避免数据混淆

### Obsidian知识库存储（推荐）
不只做临时 `/tmp/` 目录，而是建立持久化知识库：
```
~/Documents/Obsidian Vault/
├── README.md                          # 总索引 + 工作流程
├── _Templates/
│   └── trader-distillation-template.md # 交易员专用模板
├── Traders/
│   └── <handle>/                      # 每个交易员独立目录
│       ├── SKILL.md                   # 核心蒸馏文件
│       ├── Writings/                  # 推文/文章原始素材
│       ├── Research/                  # 研究分析（对话风格/DNA/决策/时间线）
│       ├── Validation/                # 质量测试报告
│       └── Demo/                      # Demo对话
├── Signal Cases/Crypto/               # 代币信号案例库
│   └── YYYY-MM-DD-<signal-name>.md
└── Twitter Archive/<handle>/          # 推特内容分类存档
```

### 信号案例提取
从交易员推文中提取**具体可验证的交易信号/案例**，单独存入 `Signal Cases/Crypto/`：
- 使用YAML frontmatter：`date`, `trader`, `tags`, `source`
- 包含：信号定义、关键数据、操盘流程、引用原文、应用框架
- 用wikilink链接到相关心智模型：`[[开口空洞框架]]`
- 目的：后续模拟交易回测、多交易员信号对比

### 快速评估：这人值得蒸馏吗？

用户常给一堆推文链接让"看看有没有用"。不要直接开干完整蒸馏，先做 10 分钟快速扫描：

1. **批量提取已知 tweet ID**并清洗内容（见上方 X/Twitter 素材挖掘现实 部分）

2. **自动分类扫描**（判断素材类型分布）：
```python
import json, os

categories = {"tools":[], "strategy":[], "signals":[], "analysis":[], "mood":[]}
keywords = {
    "tools": ['雷达','工具','开源','github','监控','回测','vibecoding'],
    "strategy": ['战法','跟庄','龙头','仓位','止损','止盈','策略'],
    "signals": ['$','买入','卖出','建仓','清仓','看','冲','赶','空'],
    "analysis": ['因为','认为','逻辑','数据','基本面','分析'],
    "mood": ['牛逼','垃圾','服了','冲呀','干','赚','亏']
}

# 读取清洗后的 tweets_raw_cleaned.json
with open("tweets_raw_cleaned.json", "r", encoding="utf-8") as f:
    tweets = json.load(f)

for url, text in tweets.items():
    low = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in low) for cat, kws in keywords.items()}
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        categories[best].append((url, text[:120]))

for cat, items in categories.items():
    print(f"{cat}: {len(items)}条")
```

3. **值得蒸馏的信号**与不值得的：

**值得蒸馏**：
- 有**可复用的框架/工具**（费率雷达、收筹逻辑、四维共振策略）
- 有**具体可验证的决策过程**（为什么买、为什么卖、盈亏多少、入场价、出场价）
- 有**自我反思**（AI分析自己、复盘错误、承认哪种模式最适合自己）
- 有**签名式表达**（固定口头禅、独特句式、习惯性表达方式）

**不值得蒸馏**：
- 纯情绪喊单（"冲呀"、"社区牛逼"、无解释的"干"）
- 过期即废的点位预测（"明天到 $X"、"下周爆发"）
- 无解释的单纯操作记录（"买了 $Y"、没有为什么买、什么时候卖）
- 无特色的普通投资意见领袖

4. **决策**：框架/工具/反思 > 3 个 → 值得完整蒸馏；否则只提取信号案例，不入 persona。

**实例**（connectfarm1）：22 条推文抽取后分类结果——tools 7条、strategy 10条、meme 3条。具备开源工具 trio（费率雷达/庄家收筹雷达/上市监控）、AI自我分析交易三类模式、$koma A8 可验证案例。判定为值得蒸馏。

### 阶段性策略
```
阶段一：蒸馏5-10个交易员 → 形成多元视角
阶段二：模拟交易 → 同一市场状态下，不同交易员会怎么看
阶段三：模拟盘交易 → 基于多视角共识进行小额模拟
阶段四：实盘交易 → 有明确信号和共识时进行小额实盘
```

## 踩坑记录

### GitHub推送
- 需要SSH key或PAT才能推送到GitHub
- 服务器上的deploy key只能推送到关联的仓库
- 如果建新仓库，需要用户先在GitHub创建空仓库
- 用户需要把SSH公钥添加到GitHub Settings → SSH keys

### 研究文件质量
- 委托subagent收集素材时，指定每个文件至少500字
- 要求包含具体引用和证据，不要泛泛而谈
- 中文素材用中文写，英文素材保持英文

### 旧数据污染
- 本地可能残留之前其他人的蒸馏数据（如 `cos-persona`）
- 新任务开始前必须先清理，否则框架和风格会混淆
- 检查路径：`/tmp/*persona*`, `~/*persona*`, `~/*perspective*`
