#!/usr/bin/env python3
"""
AgentHansa 每日签到 — 保持streak + 拿签到奖金
每天只签1次，由auto-loop.sh调用
"""
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
CHECKIN_STATE = SCRIPT_DIR / "memory" / "checkin-state.json"
LOG_FILE = SCRIPT_DIR / "logs" / "checkin.log"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_config():
    cfg = json.loads(CONFIG_FILE.read_text())
    return cfg["api_key"]

def load_state():
    if CHECKIN_STATE.exists():
        return json.loads(CHECKIN_STATE.read_text())
    return {"last_checkin_date": None, "streak": 0, "total_checkins": 0}

def save_state(state):
    CHECKIN_STATE.parent.mkdir(parents=True, exist_ok=True)
    CHECKIN_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def do_checkin(api_key):
    """执行签到"""
    import requests
    base = "https://www.agenthansa.com"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        r = requests.post(f"{base}/api/agents/checkin", headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return True, data
        else:
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def get_profile(api_key):
    """获取当前profile（含streak）"""
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

def main():
    api_key = load_config()
    state = load_state()
    
    # 检查今天是否已签到（UTC日期）
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_checkin_date") == today_utc:
        log(f"今日已签到 (UTC {today_utc}), streak={state.get('streak','?')}")
        print(json.dumps({"status": "already_checked_in", "date": today_utc, "streak": state.get("streak")}))
        return
    
    # 执行签到
    log("执行签到...")
    ok, result = do_checkin(api_key)
    
    if ok:
        # 从profile获取最新streak
        profile = get_profile(api_key)
        streak = 0
        if profile:
            streak = profile.get("checkin_streak", 0)
        
        # 解析签到奖励
        reward = 0
        if isinstance(result, dict):
            reward = result.get("reward", result.get("amount", 0)) or 0
        
        state["last_checkin_date"] = today_utc
        state["streak"] = streak
        state["total_checkins"] = state.get("total_checkins", 0) + 1
        state["last_reward"] = reward
        state["last_checkin_ts"] = int(time.time())
        save_state(state)
        
        log(f"✅ 签到成功 | streak={streak} | reward=${reward} | total={state['total_checkins']}")
        print(json.dumps({
            "status": "checked_in",
            "date": today_utc,
            "streak": streak,
            "reward": reward,
            "total_checkins": state["total_checkins"]
        }))
    else:
        log(f"❌ 签到失败: {result}")
        print(json.dumps({"status": "failed", "error": str(result)[:200]}))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
