#!/usr/bin/env python3
"""
每小时巡检 - 纯脚本逻辑，无模型调用
规则：
  1. 检查排名
  2. 若不是第一 → 立即追 1 轮
  3. 若已是第一但领先第二不足 200 分 → 再补追 1 轮
  4. 结果写入 state 文件，不通知
"""
import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

CONFIG = Path('/root/.hermes/agenthansa/config.json')
STATE = Path('/root/.hermes/agenthansa/memory/agenthansa-state.json')
AUTO_SCRIPT = '/root/.hermes/agenthansa/agenthansa-auto.py'
BASE = 'https://www.agenthansa.com/api'
UA = 'OpenClaw-Xiami/1.0'
SAFE_LEAD = 200  # 领先第二不足此值就补追


def load_cfg():
    return json.loads(CONFIG.read_text())


def req(path, key):
    url = path if path.startswith('http') else BASE + path
    r = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Authorization': f'Bearer {key}',
    })
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw else {}


def fetch_rank(key):
    """只拿联盟排行榜，最小化 API 调用"""
    me = req('/agents/me', key)
    alliance_name = me.get('alliance')
    agent_name = me.get('name') or 'Xiami'

    daily = req('/agents/alliance-daily-leaderboard', key)
    info = (daily.get('alliances') or {}).get(alliance_name) or {}
    lb = info.get('leaderboard') or []

    my_row = None
    for i, row in enumerate(lb):
        if row.get('name') == agent_name:
            my_row = row
            my_row['rank'] = i + 1
            break

    leader = lb[0] if lb else None
    second = lb[1] if len(lb) > 1 else None

    my_rank = my_row.get('rank') if my_row else None
    my_pts = my_row.get('today_points') if my_row else None
    leader_pts = leader.get('today_points') if leader else None
    second_pts = second.get('today_points') if second else None

    gap_to_first = (leader_pts - my_pts) if my_pts is not None and leader_pts is not None else None
    lead_over_second = (my_pts - second_pts) if my_rank == 1 and my_pts is not None and second_pts is not None else None

    return {
        'agent_name': agent_name,
        'alliance': alliance_name,
        'alliance_display_name': info.get('name') or alliance_name,
        'rank': my_rank,
        'points': my_pts,
        'leader_name': leader.get('name') if leader else None,
        'leader_points': leader_pts,
        'second_name': second.get('name') if second else None,
        'second_points': second_pts,
        'gap_to_first': gap_to_first,
        'lead_over_second': lead_over_second,
    }


def run_auto(rounds=1):
    """调用 agenthansa-auto.py 跑 N 轮，返回 (exit_code, 输出)"""
    last_rc = 0
    last_output = ''
    for _ in range(rounds):
        try:
            proc = subprocess.run(
                ['python3', AUTO_SCRIPT],
                capture_output=True, text=True,
                timeout=300, check=False,
            )
            last_rc = proc.returncode
            last_output = (proc.stdout or '') + (proc.stderr or '')
            if proc.returncode != 0:
                break
        except subprocess.TimeoutExpired:
            return 124, 'timeout'
    return last_rc, last_output.strip()


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save_state(data):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')

    try:
        cfg = load_cfg()
        key = cfg['api_key']
        rank_info = fetch_rank(key)
    except Exception as e:
        print(f'ERROR: 排名查询失败: {e}', file=sys.stderr)
        sys.exit(1)

    rank = rank_info['rank']
    lead = rank_info['lead_over_second']

    # 决策：要不要追？追几轮？
    rounds_to_chase = 0
    reason = ''

    if rank is None or rank != 1:
        rounds_to_chase = 1
        reason = f'不是第一(#{rank})，追1轮'
    elif lead is not None and lead < SAFE_LEAD:
        rounds_to_chase = 1
        reason = f'第一但领先仅{lead}分<{SAFE_LEAD}，补追1轮'

    if rounds_to_chase == 0:
        # 安全，不需要追
        state = load_state()
        state['last_check'] = now.isoformat(timespec='seconds')
        state['last_rank'] = rank
        state['last_points'] = rank_info['points']
        state['last_lead'] = lead
        state['last_action'] = 'none'
        save_state(state)
        print('OK: 稳定第一，无需追')
        return

    # 执行追分
    rc, output = run_auto(rounds_to_chase)

    # 追后再查一次排名
    try:
        after = fetch_rank(key)
    except Exception:
        after = rank_info

    # 更新 state
    state = load_state()
    if today not in state.get('daily_rounds', {}):
        state.setdefault('daily_rounds', {})[today] = 0
    state['daily_rounds'][today] = state.get('daily_rounds', {}).get(today, 0) + (rounds_to_chase if rc == 0 else 0)
    state['last_check'] = now.isoformat(timespec='seconds')
    state['last_rank'] = after['rank']
    state['last_points'] = after['points']
    state['last_lead'] = after['lead_over_second']
    state['last_action'] = f'chase_{rounds_to_chase}_rounds'
    state['last_chase_reason'] = reason
    state['last_chase_rc'] = rc
    save_state(state)

    if rc == 0:
        print(f'DONE: {reason} → 追后#{after["rank"]} +{after.get("lead_over_second", "?")}分')
    else:
        print(f'FAIL: {reason} → 追分失败(rc={rc})', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
