#!/usr/bin/env python3
"""
AgentHansa 每日论坛发帖 V3 — 每天4帖（01:00/10:30/16:30/22:00 BJ）
统一调度系统：cron每小时调一次，脚本自动判断时段+配额
Qwen选题 + 多模型写稿 + GPT裁判
Qwen不可用时降级到Haiku/Sonnet按高互动模板选题
"""
import json
import os
import sys
import time
import random
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
FORUM_STATE = SCRIPT_DIR / "memory" / "forum-state.json"
SUBMISSION_HISTORY = SCRIPT_DIR / "memory" / "submission-history.json"
LOG_FILE = SCRIPT_DIR / "logs" / "forum.log"

BJ = timezone(timedelta(hours=8))
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# 固定人格
PERSONA = {
    "name": "Xiami",
    "tone": "Honest, data-driven, sometimes self-deprecating. Shares real numbers — wins AND losses. Never brags without evidence. Speaks like a developer who's been through the trenches.",
    "signature": "",  # 动态生成，见 get_dynamic_signature()
}

# 高互动内容类型（来自Qwen分析真实论坛数据）
HIGH_ENGAGEMENT_TYPES = [
    {
        "type": "failure_analysis",
        "label": "个人失败复盘",
        "hint": "Share a specific failure, what went wrong, and the lesson. Include real numbers.",
        "example_hook": "I got spam-banned 3 times in one week. Here's exactly what I did wrong.",
    },
    {
        "type": "earning_report",
        "label": "收入报告",
        "hint": "Break down real earnings with specific numbers. Include surprising insights.",
        "example_hook": "My $22→$312 jump in 6 days wasn't what I expected.",
    },
    {
        "type": "agent_pattern",
        "label": "Agent协作技巧",
        "hint": "Share a specific agent collaboration pattern with concrete example.",
        "example_hook": "This 2-agent pattern doubled my quest acceptance rate.",
    },
    {
        "type": "data_teardown",
        "label": "数据分析",
        "hint": "Analyze real data and share findings. Include specific metrics.",
        "example_hook": "I tracked 40 quests. Here's what grade-50 submissions have in common.",
    },
    {
        "type": "timing_strategy",
        "label": "时间策略",
        "hint": "Share timing data — when to submit, when competition is lowest.",
        "example_hook": "The 3-hour window where most agents are asleep and quests go unclaimed.",
    },
    {
        "type": "platform_contrarian",
        "label": "平台逆向观点",
        "hint": "Challenge a common belief with data. Contrarian but backed by evidence.",
        "example_hook": "Stop writing agent descriptions like resumes — do this instead.",
    },
    {
        "type": "weekly_recap",
        "label": "周报复盘",
        "hint": "Weekly summary with real numbers, what worked, what failed.",
        "example_hook": "Week 3 on AgentHansa: 18 quests, 4 wins, 1 ban. Here's the breakdown.",
    },
]

# 备用主题（Qwen不可用时按星期轮换）
FALLBACK_TOPICS = {
    0: {"type": "earning_report", "hint": "Break down your real earnings. Total, sources, daily average, surprising insight."},
    1: {"type": "agent_pattern", "hint": "Share a specific agent collaboration pattern that improved your results."},
    2: {"type": "failure_analysis", "hint": "Share your biggest failures and what you learned. Be brutally honest."},
    3: {"type": "platform_contrarian", "hint": "Challenge a common AgentHansa belief with your real data."},
    4: {"type": "timing_strategy", "hint": "When do you submit? What time zones work best? Share timing data."},
    5: {"type": "data_teardown", "hint": "Analyze something specific — quest types, win rates, submission patterns."},
    6: {"type": "weekly_recap", "hint": "Weekly recap with real numbers. What went right, what went wrong."},
}

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_config():
    return json.loads(CONFIG_FILE.read_text())

def load_state():
    if FORUM_STATE.exists():
        return json.loads(FORUM_STATE.read_text())
    return {"last_post_date": None, "posts_today": 0, "posts": []}

def save_state(state):
    FORUM_STATE.parent.mkdir(parents=True, exist_ok=True)
    FORUM_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def get_current_slot():
    """返回当前时段: 'dawn'(01:00BJ), 'morning'(10:30BJ), 'evening'(16:30BJ), 'late'(22:00BJ) 或 None"""
    now_bj = datetime.now(BJ)
    h = now_bj.hour
    m = now_bj.minute
    if 0 <= h <= 2:          # 01:00 BJ — 欧美agent活跃
        return "dawn"
    elif 9 <= h <= 11:       # 10:30 BJ — 上午场
        return "morning"
    elif 15 <= h <= 18:      # 16:30 BJ — 傍晚高峰
        return "evening"
    elif 21 <= h or h <= 0:  # 22:00 BJ — 深夜最高峰(960agent在线)
        return "late"
    return None  # 不在发帖时段

def get_real_stats():
    """从API+submission-history拉真实数据"""
    stats = {
        "total_submissions": 0, "wins": 0, "failures": 0,
        "spam_count": 0, "total_words": 0,
        "personas_used": {}, "recent_titles": [],
        "recent_quests": [], "reputation": 384, "total_earned": 0,
        "quest_submissions": 0, "quest_wins": 0, "streak": 0,
        "red_packets": 0, "earnings_rank": 0, "total_agents": 0,
    }
    # 从API拉真实profile数据
    try:
        import requests
        api_key = json.load(open(CONFIG_PATH))['api_key']
        r = requests.get("https://www.agenthansa.com/api/agents/me",
            headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        if r.status_code == 200:
            profile = r.json()
            rep = profile.get("reputation", {})
            stats["reputation"] = rep.get("overall_score", 384)
            snap = profile.get("stats_snapshot", {})
            stats["total_earned"] = snap.get("total_earned", 0)
            stats["quest_submissions"] = snap.get("quest_submissions", 0)
            stats["quest_wins"] = snap.get("quest_wins", 0)
            stats["streak"] = snap.get("streak", 0)
            stats["red_packets"] = snap.get("red_packets", 0)
            stats["earnings_rank"] = snap.get("earnings_rank", 0)
            stats["total_agents"] = snap.get("total_agents", 0)
    except:
        pass
    if SUBMISSION_HISTORY.exists():
        for line in SUBMISSION_HISTORY.read_text().splitlines():
            try:
                d = json.loads(line)
                stats["total_submissions"] += 1
                st = d.get("status", "")
                if st in ("submitted", "won"):
                    stats["wins"] += 1
                elif st == "failed":
                    stats["failures"] += 1
                err = str(d.get("error", "")).lower()
                if "spam" in err:
                    stats["spam_count"] += 1
                w = d.get("words", 0)
                if w:
                    stats["total_words"] += w
                p = d.get("personality", "")
                if p:
                    stats["personas_used"][p] = stats["personas_used"].get(p, 0) + 1
                t = d.get("title", "")
                if t:
                    stats["recent_titles"].append(t[:50])
                rq = d.get("quest_title", "")
                if rq:
                    stats["recent_quests"].append(rq[:60])
            except:
                pass
    stats["recent_titles"] = stats["recent_titles"][-10:]
    stats["recent_quests"] = stats["recent_quests"][-10:]
    return stats

def get_dynamic_signature():
    """根据真实API数据生成签名"""
    try:
        import requests
        api_key = json.load(open(CONFIG_PATH))['api_key']
        r = requests.get("https://www.agenthansa.com/api/agents/me",
            headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        if r.status_code == 200:
            profile = r.json()
            snap = profile.get("stats_snapshot", {})
            subs = snap.get("quest_submissions", 0)
            wins = snap.get("quest_wins", 0)
            earned = snap.get("total_earned", 0)
            streak = snap.get("streak", 0)
            rank = snap.get("earnings_rank", 0)
            total_agents = snap.get("total_agents", 0)
            if subs > 0:
                return f"— Xiami | {subs} quests, {wins} wins, ${earned} earned | Rank #{rank}/{total_agents} | {streak}-day streak"
    except:
        pass
    return "— Xiami | Learning by doing"

def get_profile_data(api_key):
    """拉profile真实数据"""
    import requests
    base = "https://www.agenthansa.com"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.get(f"{base}/api/agents/me", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_recent_forum_posts():
    """拉最近论坛帖子，避免重复话题"""
    import requests
    try:
        r = requests.get("https://www.agenthansa.com/api/forum?page=1&per_page=20", timeout=10)
        if r.status_code == 200:
            data = r.json()
            posts = data.get("posts", data if isinstance(data, list) else [])
            return [(p.get("title", ""), p.get("category", "")) for p in posts[:15]]
    except:
        pass
    return []

def get_xiami_recent_posts():
    """拉Xiami自己最近的帖子，避免重复角度"""
    import requests
    XIAOMI_ID = 'bdf79ad6-99a2-4531-b156-ef9888ff870f'
    xiami_posts = []
    try:
        for page in range(1, 4):
            r = requests.get(f"https://www.agenthansa.com/api/forum?page={page}&per_page=50", timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
            posts = data.get("posts", data if isinstance(data, list) else [])
            for p in posts:
                if isinstance(p, dict):
                    agent = p.get("agent") or {}
                    if agent.get("id") == XIAOMI_ID:
                        title = p.get("title", "")
                        body = (p.get("body", "") or "")[:200]
                        xiami_posts.append((title, body))
    except:
        pass
    return xiami_posts

def _load_env():
    env_file = Path.home() / ".hermes" / "agenthansa" / ".env.agenthansa"
    env_vars = {}
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

_bankofai_key_idx = 0

def _call_model(provider, model, prompt, api_key=None, max_tokens=800, temperature=0.7):
    """通用模型调用"""
    import requests
    global _bankofai_key_idx
    env_vars = _load_env()

    def _split_keys(raw_keys):
        """Split comma-separated keys and filter by length"""
        result = []
        for k in raw_keys:
            for part in k.split(","):
                part = part.strip()
                if len(part) >= 20:
                    result.append(part)
        return result

    if provider == "edgefn":
        raw = [v for k, v in env_vars.items() if "EDGEFN" in k and "KEY" in k]
        keys = _split_keys(raw)
        if not keys:
            return None, "No edgefn keys"
        key = api_key or random.choice(keys)
        url = env_vars.get("EDGEFN_BASE", "https://api.edgefn.net/v1/chat/completions")
    elif provider == "newapi":
        raw = [v for k, v in env_vars.items() if "NEWAPI" in k and "KEY" in k]
        keys = _split_keys(raw)
        if not keys:
            return None, "No newapi keys"
        key = api_key or random.choice(keys)
        url = env_vars.get("NEWAPI_BASE", "https://newapi.lzgzxs.xyz/v1") + "/chat/completions"
    elif provider == "bankofai":
        raw = [v for k, v in env_vars.items() if "BANKOFAI" in k and "KEY" in k]
        keys = _split_keys(raw)
        if not keys:
            return None, "No bankofai keys"
        start_idx = _bankofai_key_idx % len(keys)
        url = "https://api.bankofai.io/v1/chat/completions"
        key = None
    elif provider == "qwen":
        # Qwen Code CLI
        return _call_qwen(prompt)
    else:
        return None, f"Unknown provider: {provider}"

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temperature}

    if provider == "bankofai":
        for attempt in range(len(keys)):
            idx = (start_idx + attempt) % len(keys)
            key = keys[idx]
            headers["Authorization"] = f"Bearer {key}"
            try:
                r = requests.post(url, headers=headers, json=body, timeout=60)
                if r.status_code == 200:
                    _bankofai_key_idx = (idx + 1) % len(keys)
                    return r.json()["choices"][0]["message"]["content"].strip(), None
                elif r.status_code in (400, 401, 403, 429):
                    continue
                else:
                    return None, f"HTTP {r.status_code}: {r.text[:100]}"
            except:
                continue
        return None, f"All {len(keys)} bankofai keys exhausted"

    try:
        r = requests.post(url, headers=headers, json=body, timeout=60)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip(), None
        else:
            return None, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return None, str(e)

def _call_qwen(prompt):
    """Qwen Code CLI调用"""
    try:
        # 先写prompt到临时文件
        prompt_file = "/tmp/qwen_forum_prompt.txt"
        Path(prompt_file).write_text(prompt)
        
        result = subprocess.run(
            ["bash", "-c", f'export PATH="/root/.hermes/node/bin:$PATH" && npx @qwen-code/qwen-code "$(cat {prompt_file})" --approval-mode yolo -o json'],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode != 0:
            return None, f"Qwen exit {result.returncode}: {result.stderr[:200]}"
        
        # 解析JSON输出，提取result
        data = json.loads(result.stdout)
        for item in data:
            if item.get("type") == "result":
                return item.get("result", ""), None
        return None, "No result in Qwen output"
    except subprocess.TimeoutExpired:
        return None, "Qwen timeout (180s)"
    except Exception as e:
        return None, str(e)

def _parse_json(text):
    """从模型输出中安全提取JSON"""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end])
    except:
        return None

def select_topic_qwen(stats, recent_posts, slot):
    """用Qwen选题 — 基于实时数据+高互动模式"""
    recent_titles = "\n".join([f"- {t}" for t, _ in recent_posts[:10]])
    engagement_types = json.dumps([{"type": t["type"], "label": t["label"], "hint": t["hint"]} for t in HIGH_ENGAGEMENT_TYPES])
    
    # 拉Xiami自己发过的帖子，强制避免重复
    xiami_posts = get_xiami_recent_posts()
    xiami_history = ""
    if xiami_posts:
        xiami_history = "XIAOMI'S OWN PREVIOUS POSTS (MUST NOT repeat these themes/angles):\n"
        for i, (title, body) in enumerate(xiami_posts):
            xiami_history += f"{i+1}. Title: {title}\n   Content preview: {body[:150]}...\n"
        xiami_history += "\n⚠️ CRITICAL: Your new post MUST be about a COMPLETELY DIFFERENT topic. Do NOT write about having 0 submissions, reputation score, or lurking. Pick a TOTALLY different angle.\n"
    
    prompt = f"""You are selecting a forum post topic for AgentHansa to maximize engagement (upvotes + comments).

REAL DATA about this agent (Xiami):
- Quests submitted: {stats['total_submissions']}
- Wins: {stats['wins']}
- Failures: {stats['failures']}
- Spam flags: {stats['spam_count']}
- Reputation: {stats.get('reputation', 384)}
- Total earned: ${stats.get('total_earned', 0)}
- Recent quest titles: {json.dumps(stats.get('recent_quests', []))}

RECENT FORUM POSTS (avoid duplicating these topics):
{recent_titles}

{xiami_history}

HIGH-ENGAGEMENT CONTENT TYPES (from analysis of 50+ posts):
{engagement_types}

CURRENT SLOT: {slot} (dawn=01:00BJ 欧美活跃, morning=10:30BJ 上午, evening=16:30BJ 傍晚高峰, late=22:00BJ 深夜最高峰)

TASK: Pick ONE content type and write a specific topic prompt for the post writer.
The topic must be:
1. Based on real data above (use exact numbers)
2. COMPLETELY different from Xiami's own previous posts (see list above)
3. Match the high-engagement patterns
4. dawn slot = personal story-driven (欧美时段，分享经历); morning = data/analytical; evening = contrarian/timing; late = vulnerability/failure (深夜高峰，真实感)

⚠️ NEVER repeat the same angle. If previous posts were about "0 submissions", pick something about:
   - Specific quest strategies and timing data
   - Alliance competition dynamics (green vs red vs blue)
   - What makes quests worth attempting vs skipping
   - Spam detection and quality systems
   - Red packet mechanics and earning optimization
   - Platform feature analysis
   - Competitor behavior patterns
   - Technical workflow tips

OUTPUT (ONLY valid JSON):
{{"type": "chosen_type", "topic_prompt": "Specific prompt for the post writer referencing real data", "angle": "The specific angle to take"}}"""

    text, err = _call_model("qwen", "", prompt, max_tokens=500, temperature=0.7)
    if not text:
        return None
    data = _parse_json(text)
    if data and data.get("type") and data.get("topic_prompt"):
        return data
    return None

def select_topic_fallback(slot):
    """Qwen不可用时的降级选题"""
    weekday = datetime.now(BJ).weekday()
    fallback = FALLBACK_TOPICS[weekday]
    
    # 找到对应的高互动类型
    for t in HIGH_ENGAGEMENT_TYPES:
        if t["type"] == fallback["type"]:
            return {
                "type": t["type"],
                "topic_prompt": t["hint"],
                "angle": t["example_hook"],
            }
    return {
        "type": "failure_analysis",
        "topic_prompt": "Share your biggest failure and what you learned.",
        "angle": "Be honest about what went wrong.",
    }

def _write_draft(model_name, provider, topic_prompt, angle, real_data):
    """单个模型写一版帖子"""
    # 获取Xiami历史帖子，写稿时也要避免重复
    xiami_posts = get_xiami_recent_posts()
    avoid_section = ""
    if xiami_posts:
        avoid_section = "\nMY PREVIOUS POSTS (do NOT repeat these themes):\n"
        for i, (title, body) in enumerate(xiami_posts):
            avoid_section += f"- \"{title}\"\n"
        avoid_section += "\nWrite about something COMPLETELY different. New angle, new hook, new topic.\n"
    
    prompt = f"""You are writing a forum post for AgentHansa as Xiami.

TOPIC: {topic_prompt}
ANGLE: {angle}

{real_data}
{avoid_section}

PERSONA: {PERSONA['tone']}

WRITING RULES:
1. Use EXACT numbers from the real data — never invent stats
2. Title: punchy, specific, makes you want to click. Not generic.
3. Body: 150-250 words. Every sentence must earn its place.
4. First sentence = hook. No "Hey everyone" or "I wanted to share".
5. End with: {get_dynamic_signature()}
6. English, no markdown, plain text.
7. Show vulnerability — mention a real failure or mistake.
8. Include at least 2 hard numbers from the data.

OUTPUT (ONLY valid JSON):
{{"title": "Post title", "content": "Post body"}}"""

    text, err = _call_model(provider, model_name, prompt, max_tokens=800, temperature=0.8)
    if not text:
        return None
    data = _parse_json(text)
    if data and data.get("title") and data.get("content"):
        return data
    return None

def _judge_and_pick(drafts, topic_prompt, real_data):
    """GPT裁判选最佳"""
    drafts_text = ""
    for i, d in enumerate(drafts):
        drafts_text += f"\n--- DRAFT {i+1} ---\nTitle: {d['title']}\nContent: {d['content']}\n"

    judge_prompt = f"""You are a ruthless editor picking the BEST forum post from {len(drafts)} drafts.

TOPIC: {topic_prompt}

{real_data}

DRAFTS:{drafts_text}

JUDGE BY:
1. Hook strength — does the first sentence make you stop scrolling?
2. Data accuracy — are numbers from the real data, not hallucinated?
3. Authenticity — does it sound like a real person, not an AI?
4. Actionability — can the reader learn something specific?
5. Vulnerability — does it show real failures, not just wins?
6. Signature included?

Pick the BEST draft. If none are good enough (score < 7/10), say so and give specific improvement notes.

OUTPUT (ONLY valid JSON):
If a draft is good enough:
{{"winner": 1, "score": 8, "reason": "why this one"}}
If ALL drafts need work:
{{"winner": 0, "score": 5, "issues": ["issue1", "issue2"], "fix_hint": "specific guidance for revision"}}"""

    text, err = _call_model("bankofai", "gpt-5.4", judge_prompt, max_tokens=500, temperature=0.2)
    if not text:
        return None
    return _parse_json(text)

def _revise_draft(draft, issues, fix_hint, real_data):
    """改稿"""
    prompt = f"""Revise this forum post. The editor said it needs work.

ORIGINAL:
Title: {draft['title']}
Content: {draft['content']}

EDITOR FEEDBACK:
Issues: {json.dumps(issues)}
Guidance: {fix_hint}

{real_data}

RULES:
1. Fix ONLY what was flagged
2. Keep all real numbers
3. Keep the same persona tone
4. 150-250 words
5. Must include signature: {get_dynamic_signature()}

OUTPUT (ONLY valid JSON):
{{"title": "Revised title", "content": "Revised content"}}"""

    text, err = _call_model("newapi", "claude-sonnet-4-5-20250929", prompt, max_tokens=800, temperature=0.6)
    if not text:
        return None
    data = _parse_json(text)
    if data and data.get("title") and data.get("content"):
        return data
    return None

def generate_content(topic_prompt, angle, stats, profile):
    """3模型出稿 → GPT裁判 → 改稿"""
    real_data = f"""REAL DATA (use EXACT numbers):
- Total quests submitted: {stats['total_submissions']}
- Quests won: {stats['wins']}
- Quests failed: {stats['failures']}
- Times spam-flagged: {stats['spam_count']}
- Total words written: {stats['total_words']}
- Personas used: {json.dumps(stats['personas_used'])}"""

    if profile:
        rep = profile.get('reputation', {})
        dims = rep.get('dimensions', {}) if isinstance(rep, dict) else {}
        real_data += f"""
- Reputation score: {rep.get('overall_score', '?') if isinstance(rep, dict) else '?'}
- Reputation dimensions: {json.dumps(dims)}
- Level: {profile.get('level_name', '?')} (Lv{profile.get('level', '?')})
- Streak: {profile.get('checkin_streak', '?')} days
- Alliance: {profile.get('alliance_name', '?')}"""

    # STEP 1: 3个模型各写1版
    log("  [1/3] 3模型并行出稿...")
    drafts = []

    d1 = _write_draft("claude-sonnet-4-5-20250929", "newapi", topic_prompt, angle, real_data)
    if d1:
        drafts.append(d1)
        log(f"    Sonnet: {d1['title'][:40]} ({len(d1['content'])} chars)")

    # DeepSeek(edgefn) → 降级bankofai Haiku → 再降级newapi Sonnet
    d2 = _write_draft("DeepSeek-V3.2", "edgefn", topic_prompt, angle + " Take a contrarian angle.", real_data)
    if d2:
        drafts.append(d2)
        log(f"    DeepSeek: {d2['title'][:40]} ({len(d2['content'])} chars)")
    else:
        d2 = _write_draft("claude-haiku-4-5-20250901", "bankofai", topic_prompt, angle + " Take a contrarian angle.", real_data)
        if d2:
            drafts.append(d2)
            log(f"    Haiku(降级): {d2['title'][:40]} ({len(d2['content'])} chars)")

    d3 = _write_draft("DeepSeek-V3.2", "edgefn", topic_prompt, angle + " Lead with a personal failure.", real_data)
    if d3:
        drafts.append(d3)
        log(f"    DeepSeek-v2: {d3['title'][:40]} ({len(d3['content'])} chars)")
    else:
        d3 = _write_draft("claude-sonnet-4-5-20250929", "newapi", topic_prompt, angle + " Lead with a personal failure.", real_data)
        if d3:
            drafts.append(d3)
            log(f"    Sonnet-v2(降级): {d3['title'][:40]} ({len(d3['content'])} chars)")

    if not drafts:
        return None, "All models failed"

    log(f"  [1/3] 完成: {len(drafts)}/3 稿")

    # STEP 2: GPT裁判
    log(f"  [2/3] GPT裁判评分 {len(drafts)} 稿...")
    judgment = _judge_and_pick(drafts, topic_prompt, real_data)

    if not judgment:
        log("  GPT裁判失败，用最长稿")
        best = max(drafts, key=lambda d: len(d.get("content", "")))
        return best, None

    winner_idx = judgment.get("winner", 1) - 1
    score = judgment.get("score", 0)

    if 0 <= winner_idx < len(drafts) and score >= 7:
        log(f"  [2/3] 选 Draft {winner_idx+1} (score={score}): {judgment.get('reason','')[:60]}")
        return drafts[winner_idx], None

    # 不够好，改一轮
    issues = judgment.get("issues", [])
    fix_hint = judgment.get("fix_hint", "")
    log(f"  [2/3] score={score}, issues: {issues[:2]}")

    base = drafts[winner_idx] if 0 <= winner_idx < len(drafts) else drafts[0]
    log(f"  [3/3] Sonnet改稿...")
    revised = _revise_draft(base, issues, fix_hint, real_data)
    if revised:
        log(f"  [3/3] 改稿完成: {revised['title'][:40]}")
        return revised, None

    log("  [3/3] 改稿失败，用原稿")
    return base, None

def post_to_forum(api_key, title, content, category=None):
    """发帖到论坛"""
    import requests
    base = "https://www.agenthansa.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {"title": title, "body": content}
    if category:
        body["category"] = category
    try:
        r = requests.post(f"{base}/api/forum", headers=headers, json=body, timeout=15)
        if r.status_code in (200, 201):
            return True, r.json()
        else:
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def main():
    cfg = load_config()
    api_key = cfg["api_key"]
    state = load_state()

    now_bj = datetime.now(BJ)
    today_bj = now_bj.strftime("%Y-%m-%d")
    slot = get_current_slot()

    # 检查时段
    if slot is None:
        h = now_bj.hour
        # 非标准时段：按小时就近分配
        if 0 <= h <= 2:
            slot = "dawn"
        elif 9 <= h <= 11:
            slot = "morning"
        elif 15 <= h <= 18:
            slot = "evening"
        elif 21 <= h or h <= 0:
            slot = "late"
        else:
            log(f"非发帖时段(h={h})，退出")
            print(json.dumps({"status": "not_posting_hour", "hour": h}))
            return
        log(f"非标准时段(h={h})，按'{slot}'处理")

    # 检查今天这个时段是否已发帖
    post_key = f"{today_bj}_{slot}"
    posted_today = state.get("posts_today_keys", [])
    if post_key in posted_today:
        log(f"今日{slot}已发帖 ({post_key})")
        print(json.dumps({"status": "already_posted", "slot": slot, "date": today_bj}))
        return

    # 检查今天是否已发4帖
    today_posts = [p for p in state.get("posts", []) if p.get("date", "") == today_bj]
    if len(today_posts) >= 4:
        log(f"今日已发{len(today_posts)}帖，跳过")
        print(json.dumps({"status": "daily_limit_reached", "count": len(today_posts)}))
        return

    log(f"=== 发帖时段: {slot} (BJ {now_bj.strftime('%H:%M')}) ===")

    # 拉真实数据
    stats = get_real_stats()
    profile = get_profile_data(api_key)
    recent_posts = get_recent_forum_posts()
    log(f"Stats: {stats['total_submissions']}sub, {stats['wins']}win, {stats['failures']}fail")
    log(f"最近论坛帖子: {len(recent_posts)}条")

    # ====== 选题 ======
    log("Qwen选题...")
    topic = select_topic_qwen(stats, recent_posts, slot)

    if topic:
        log(f"Qwen选题: {topic['type']} — {topic['topic_prompt'][:60]}")
    else:
        log("Qwen选题失败，降级到备用方案")
        topic = select_topic_fallback(slot)
        log(f"备用选题: {topic['type']}")

    # ====== 生成内容 ======
    log(f"生成内容: {topic['type']}...")
    result, err = generate_content(topic["topic_prompt"], topic.get("angle", ""), stats, profile)

    if not result:
        log(f"❌ 内容生成失败: {err}")
        print(json.dumps({"status": "generation_failed", "error": err}))
        return

    title = result.get("title", "").strip()
    content = result.get("content", "").strip()

    if not title or not content:
        log("❌ 生成内容为空")
        print(json.dumps({"status": "empty_content"}))
        return

    log(f"生成: {title[:60]} ({len(content)} chars)")
    
    # ====== 重复检查 ======
    xiami_posts = get_xiami_recent_posts()
    if xiami_posts:
        title_words = set(title.lower().split())
        for old_title, _ in xiami_posts:
            old_words = set(old_title.lower().split())
            if len(title_words) >= 3 and len(old_words) >= 3:
                overlap = len(title_words & old_words) / max(len(title_words), len(old_words))
                if overlap > 0.5:
                    log(f"⚠️ 标题与已有帖子{overlap:.0%}相似，跳过: {old_title[:50]}")
                    print(json.dumps({"status": "duplicate_skipped", "similarity": round(overlap, 2)}))
                    return

    # ====== 发帖 ======
    ok, data = post_to_forum(api_key, title, content)

    if ok:
        post_id = ""
        if isinstance(data, dict):
            post_id = data.get("id", data.get("post_id", ""))

        # 更新状态
        if "posts_today_keys" not in state:
            state["posts_today_keys"] = []
        state["posts_today_keys"].append(post_key)
        # 只保留7天内的key
        cutoff = (now_bj - timedelta(days=7)).strftime("%Y-%m-%d")
        state["posts_today_keys"] = [k for k in state["posts_today_keys"] if k >= cutoff]

        state["posts"].append({
            "date": today_bj,
            "slot": slot,
            "title": title,
            "category": topic["type"],
            "post_id": post_id,
        })
        state["posts"] = state["posts"][-30:]
        save_state(state)

        log(f"✅ 发帖成功: {title[:60]} (slot={slot})")
        print(json.dumps({
            "status": "posted",
            "title": title,
            "slot": slot,
            "category": topic["type"],
            "post_id": post_id,
        }))
    else:
        log(f"❌ 发帖失败: {data}")
        print(json.dumps({"status": "post_failed", "error": str(data)[:200]}))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
