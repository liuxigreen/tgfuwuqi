#!/usr/bin/env python3
"""
用 Qwen Code 分析 AgentHansa 平台赚钱策略
分批运行，每次分析一个方向，持续迭代
结果存到 memory/qwen-research/ 目录
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

QWEN = "/usr/local/bin/qwen"
QWEN_ARGS = []
RESEARCH_DIR = Path("/root/.hermes/agenthansa/memory/qwen-research")
STATE_FILE = RESEARCH_DIR / "state.json"
LOG_FILE = RESEARCH_DIR / "research.log"

RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"batch": 0, "findings": [], "topics_done": [], "last_run": None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def run_qwen(prompt, timeout=180):
    """运行 Qwen Code CLI (/usr/local/bin/qwen)，返回结果文本"""
    try:
        r = subprocess.run(
            [QWEN] + QWEN_ARGS + [prompt, "-o", "json", "--approval-mode", "yolo"],
            capture_output=True, text=True, timeout=timeout
        )
        # 解析 JSON 输出，提取 result
        output = r.stdout.strip()
        if not output:
            return None
        # JSON output is a JSON array
        try:
            events = json.loads(output)
            for event in events:
                if event.get("type") == "result":
                    return event.get("result", "")
        except json.JSONDecodeError:
            return output
        return None
    except subprocess.TimeoutExpired:
        log("Qwen timeout")
        return None
    except Exception as e:
        log(f"Qwen error: {e}")
        return None

# 研究主题队列 — 不告诉答案，让它自己发现
TOPICS = [
    {
        "id": "leaderboard",
        "prompt": (
            "Go to https://www.agenthansa.com and analyze the leaderboard. "
            "Who are the top earning agents? What do they have in common? "
            "Check their profiles, submissions, forum posts. "
            "What strategies are they using to earn money? "
            "Save your findings to /root/.hermes/agenthansa/memory/qwen-research/findings-leaderboard.md"
        ),
    },
    {
        "id": "forum-quality",
        "prompt": (
            "Go to https://www.agenthansa.com/forum and find the highest quality posts. "
            "What topics get the most engagement? What writing style works? "
            "Look at posts by top agents like Zaran, AgentHansa. "
            "What can we learn from their content strategy? "
            "Save findings to /root/.hermes/agenthansa/memory/qwen-research/findings-forum.md"
        ),
    },
    {
        "id": "quest-types",
        "prompt": (
            "Explore https://www.agenthansa.com and analyze all the different ways agents can earn money. "
            "Look at: quests, bounties, red packets, side quests, alliance war, referrals. "
            "Which earning methods have the best effort-to-reward ratio? "
            "What are other agents NOT doing that has high potential? "
            "Save findings to /root/.hermes/agenthansa/memory/qwen-research/findings-quests.md"
        ),
    },
    {
        "id": "reputation",
        "prompt": (
            "Research how AgentHansa reputation system works. "
            "Check the API at https://www.agenthansa.com/openapi.json for reputation-related endpoints. "
            "How do agents build reputation? What gives the most points? "
            "Does higher reputation unlock better earning opportunities? "
            "Save findings to /root/.hermes/agenthansa/memory/qwen-research/findings-reputation.md"
        ),
    },
    {
        "id": "alliance-strategy",
        "prompt": (
            "Analyze the Alliance War system on AgentHansa. "
            "Which alliance is winning? What strategies do winning alliance members use? "
            "How does the reward split work? What's the optimal submission strategy? "
            "Save findings to /root/.hermes/agenthansa/memory/qwen-research/findings-alliance.md"
        ),
    },
    {
        "id": "competitive-analysis",
        "prompt": (
            "Look at submitted quests on AgentHansa - which ones got accepted vs rejected? "
            "Study the difference between winning and losing submissions. "
            "What do merchants actually want? What gets 'favorited'? "
            "Save findings to /root/.hermes/agenthansa/memory/qwen-research/findings-competitive.md"
        ),
    },
    {
        "id": "untapped-opportunities",
        "prompt": (
            "Based on everything you've learned about AgentHansa, find opportunities most agents are missing. "
            "Look at: low-competition quests, underused features, timing patterns, niche categories. "
            "What would you do differently to maximize earnings? Be specific and actionable. "
            "Save findings to /root/.hermes/agenthansa/memory/qwen-research/findings-opportunities.md"
        ),
    },
    {
        "id": "synthesis",
        "prompt": (
            "Read all files in /root/.hermes/agenthansa/memory/qwen-research/ "
            "and create a comprehensive earnings strategy guide. "
            "Combine all previous findings into an actionable plan. "
            "Rank the top 10 highest-ROI actions an agent should take. "
            "Save to /root/.hermes/agenthansa/memory/qwen-research/strategy-guide.md"
        ),
    },
]

def main():
    state = load_state()
    batch = state.get("batch", 0)
    topics_done = set(state.get("topics_done", []))

    # 找下一个没做的主题
    next_topic = None
    for topic in TOPICS:
        if topic["id"] not in topics_done:
            next_topic = topic
            break

    if not next_topic:
        log("All topics researched! Starting new iteration cycle...")
        # 重置，开始新一轮迭代（用更深入的提示词）
        state["topics_done"] = []
        state["batch"] = batch + 1
        save_state(state)
        # 找第一个主题
        next_topic = TOPICS[0]

    batch += 1
    log(f"Batch #{batch}: {next_topic['id']}")

    # 如果是第二轮迭代，加深提示词
    prompt = next_topic["prompt"]
    if state.get("batch", 0) > 0:
        prompt += (
            "\n\nThis is iteration round " + str(state["batch"] + 1) +
            ". Previous findings exist in the research directory. "
            "Go deeper. Find NEW insights not covered before. Challenge previous assumptions."
        )

    result = run_qwen(prompt, timeout=180)

    if result:
        log(f"Result ({len(result)} chars): {result[:200]}...")
        state["findings"].append({
            "batch": batch,
            "topic": next_topic["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": result[:500],
        })
    else:
        log("No result returned")

    topics_done.add(next_topic["id"])
    state["topics_done"] = list(topics_done)
    state["batch"] = batch
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    log(f"Done. {len(topics_done)}/{len(TOPICS)} topics completed this cycle.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        sys.exit(1)
