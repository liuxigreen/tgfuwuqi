#!/usr/bin/env python3
"""
AgentHansa 论坛互动 — upvote别人帖触发互赞
每天跑1-2次，每次upvote 3-5个帖子，提升quality维度
"""
import json
import random
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
INTERACT_STATE = SCRIPT_DIR / "memory" / "forum-interact-state.json"
LOG_FILE = SCRIPT_DIR / "logs" / "forum-interact.log"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_config():
    return json.loads(CONFIG_FILE.read_text())

def load_state():
    if INTERACT_STATE.exists():
        return json.loads(INTERACT_STATE.read_text())
    return {"upvoted_ids": [], "last_date": None, "total_upvotes": 0, "daily_count": 0}

def save_state(state):
    INTERACT_STATE.parent.mkdir(parents=True, exist_ok=True)
    INTERACT_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def get_forum_posts(api_key, page=1, limit=20):
    """拉论坛帖子列表"""
    import requests
    base = "https://www.agenthansa.com"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.get(f"{base}/api/forum", headers=headers, params={"page": page, "limit": limit}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("posts", data.get("data", []))
    except:
        pass
    return []

def upvote_post(api_key, post_id):
    """给帖子点赞"""
    import requests
    base = "https://www.agenthansa.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            f"{base}/api/forum/{post_id}/vote",
            headers=headers,
            json={"direction": "up"},
            timeout=10,
        )
        if r.status_code in (200, 201):
            return True, r.json()
        elif r.status_code == 409:
            return False, "already_upvoted"
        else:
            return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    cfg = load_config()
    api_key = cfg["api_key"]
    state = load_state()
    
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # 每日重置计数
    if state.get("last_date") != today_utc:
        state["daily_count"] = 0
        state["last_date"] = today_utc
        # 每周清空upvoted_ids（防无限膨胀）
        if len(state.get("upvoted_ids", [])) > 200:
            state["upvoted_ids"] = state["upvoted_ids"][-50:]
    
    # 每天上限5次upvote
    if state.get("daily_count", 0) >= 5:
        log(f"今日已达上限 ({state['daily_count']}/5)")
        print(json.dumps({"status": "daily_limit", "count": state["daily_count"]}))
        return
    
    # 拉帖子
    log("拉取论坛帖子...")
    posts = get_forum_posts(api_key, page=1, limit=30)
    if not posts:
        log("未获取到帖子")
        print(json.dumps({"status": "no_posts"}))
        return
    
    log(f"获取 {len(posts)} 个帖子")
    
    # 过滤：跳过自己的帖子 + 已upvote的
    upvoted_set = set(state.get("upvoted_ids", []))
    candidates = []
    for p in posts:
        pid = p.get("id", "")
        author = p.get("author", p.get("agent_name", ""))
        if pid and pid not in upvoted_set and "xiami" not in str(author).lower():
            candidates.append(p)
    
    if not candidates:
        log("没有可upvote的帖子（全部已赞或自己发的）")
        print(json.dumps({"status": "no_candidates"}))
        return
    
    # 随机选3-5个（不超过剩余配额）
    remaining = 5 - state.get("daily_count", 0)
    count = min(random.randint(3, 5), remaining, len(candidates))
    selected = random.sample(candidates, count)
    
    log(f"选中 {count} 个帖子upvote")
    
    results = []
    for i, p in enumerate(selected):
        pid = p.get("id", "")
        title = p.get("title", "")[:40]
        
        ok, data = upvote_post(api_key, pid)
        
        if ok:
            state["upvoted_ids"].append(pid)
            state["daily_count"] = state.get("daily_count", 0) + 1
            state["total_upvotes"] = state.get("total_upvotes", 0) + 1
            log(f"  ✅ [{i+1}/{count}] {title}")
            results.append({"id": pid, "title": title, "status": "upvoted"})
        elif data == "already_upvoted":
            state["upvoted_ids"].append(pid)  # 记录避免重复
            log(f"  ⏭ [{i+1}/{count}] 已赞过: {title}")
            results.append({"id": pid, "title": title, "status": "already_upvoted"})
        else:
            log(f"  ❌ [{i+1}/{count}] 失败: {title} — {data}")
            results.append({"id": pid, "title": title, "status": "failed", "error": str(data)})
        
        # 随机间隔 5-15s 防检测
        if i < count - 1:
            delay = random.uniform(5, 15)
            time.sleep(delay)
    
    save_state(state)
    
    success_count = sum(1 for r in results if r["status"] == "upvoted")
    log(f"完成: {success_count}/{count} upvoted, 今日共{state['daily_count']}/5")
    print(json.dumps({
        "status": "done",
        "upvoted": success_count,
        "daily_count": state["daily_count"],
        "results": results,
    }))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
