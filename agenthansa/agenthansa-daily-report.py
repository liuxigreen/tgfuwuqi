#!/usr/bin/env python3
"""
每日收益日报 - 脚本收集数据，纯脚本格式化
"""
import json
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

CONFIG = Path('/root/.hermes/agenthansa/config.json')
STATE = Path('/root/.hermes/agenthansa/memory/agenthansa-state.json')
RP_SUMMARY = Path('/root/.hermes/agenthansa/memory/agenthansa-redpacket-summary.jsonl')
TASK_SUMMARY = Path('/root/.hermes/agenthansa/memory/agenthansa-task-summary.jsonl')
BASE = 'https://www.agenthansa.com/api'
UA = 'OpenClaw-Xiami/1.0'


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


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def format_number(value):
    if value is None:
        return '?'
    num = float(value)
    if num.is_integer():
        return str(int(num))
    return f'{num:.2f}'.rstrip('0').rstrip('.')


def read_jsonl_today(path, today):
    records = []
    if not path.exists():
        return records
    for line in path.read_text().splitlines():
        try:
            rec = json.loads(line)
            if (rec.get('ts') or '')[:10] == today:
                records.append(rec)
        except Exception:
            pass
    return records


def main():
    try:
        cfg = load_cfg()
        key = cfg['api_key']
        state = load_state()
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')

        # 基本信息
        me = req('/agents/me', key)
        agent_name = me.get('name') or 'Xiami'
        level = (me.get('reputation') or {}).get('tier', '?')
        total_usdc = me.get('total_earnings_usdc') or me.get('total_usdc') or 0

        # 排名
        daily = req('/agents/alliance-daily-leaderboard', key)
        alliance_name = me.get('alliance')
        info = (daily.get('alliances') or {}).get(alliance_name) or {}
        lb = info.get('leaderboard') or []

        my_row = None
        for i, row in enumerate(lb):
            if row.get('name') == agent_name:
                my_row = row
                my_row['rank'] = i + 1
                break

        my_rank = my_row.get('rank') if my_row else None
        my_pts = my_row.get('today_points') if my_row else None

        # 红包统计
        rp_records = read_jsonl_today(RP_SUMMARY, today)
        rp_success = sum(1 for r in rp_records if r.get('status') == 'success')
        rp_fail = sum(1 for r in rp_records if r.get('status') == 'failure')
        rp_noactive = sum(1 for r in rp_records if r.get('status') == 'no_active')
        rp_usdc = sum(float(r.get('estimated_per_person') or 0) for r in rp_records if r.get('status') == 'success')

        # 任务统计
        task_records = read_jsonl_today(TASK_SUMMARY, today)
        tasks_submitted = sum(1 for r in task_records if r.get('event') == 'submitted')
        tasks_earned = sum(float(r.get('usdc') or 0) for r in task_records if r.get('event') in ('submitted', 'rewarded'))

        # 追分统计
        daily_rounds = (state.get('daily_rounds') or {}).get(today, 0)

        # 输出
        lines = [
            f'📈 AgentHansa 日报 {today}',
            f'',
            f'🏷 {agent_name} | Lv.{level}',
            f'📊 今日排名: #{my_rank or "?"} | 积分: {format_number(my_pts)}',
            f'💰 累计收益: ${total_usdc}',
            f'',
            f'── 收益明细 ──',
            f'🧧 红包: {rp_success}次成功 / {rp_fail}次失败 / {rp_noactive}次无活动',
            f'   预估红包收入: ${rp_usdc:.2f}',
            f'📝 任务: {tasks_submitted} 个提交',
            f'   预估任务收入: ${tasks_earned:.2f}',
            f'   今日总预估: ${rp_usdc + tasks_earned:.2f}',
            f'',
            f'── 追分情况 ──',
            f'🔄 今日追分: {daily_rounds} 轮',
            f'⏰ 最后动作: {state.get("last_action", "none")}',
            f'📍 最后排名: #{state.get("last_rank", "?")}',
        ]

        print('\n'.join(lines))

    except Exception as e:
        print(f'ERROR: 日报生成失败: {e}')
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main()
