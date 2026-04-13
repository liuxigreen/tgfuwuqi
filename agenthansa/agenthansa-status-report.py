#!/usr/bin/env python3
"""
每 6 小时状态报告 - 脚本收集数据，用便宜模型格式化
输出 JSON 给 cron job，由 cron job 用 deepseek 格式化后发通知
"""
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

CONFIG = Path('/root/.hermes/agenthansa/config.json')
STATE = Path('/root/.hermes/agenthansa/memory/agenthansa-state.json')
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


def main():
    try:
        cfg = load_cfg()
        key = cfg['api_key']
        state = load_state()
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')

        # 当前排名
        me = req('/agents/me', key)
        alliance_name = me.get('alliance')
        agent_name = me.get('name') or 'Xiami'
        level = (me.get('reputation') or {}).get('tier', '?')
        total_usdc = me.get('total_earnings_usdc') or me.get('total_usdc') or 0

        # 联盟日榜
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

        # 今日追分轮数
        daily_rounds = (state.get('daily_rounds') or {}).get(today, 0)

        # 红包统计（从 summary log 读今日数据）
        rp_summary = Path('/root/.hermes/agenthansa/memory/agenthansa-redpacket-summary.jsonl')
        rp_success = 0
        rp_fail = 0
        rp_total_usdc = 0
        if rp_summary.exists():
            for line in rp_summary.read_text().splitlines():
                try:
                    rec = json.loads(line)
                    ts = rec.get('ts', '')
                    if ts[:10] == today:
                        if rec.get('status') == 'success':
                            rp_success += 1
                            rp_total_usdc += float(rec.get('estimated_per_person') or 0)
                        elif rec.get('status') == 'failure':
                            rp_fail += 1
                except Exception:
                    pass

        # 汇总
        report = {
            'time': now.strftime('%H:%M'),
            'agent': agent_name,
            'alliance': info.get('name') or alliance_name,
            'level': level,
            'rank': my_rank,
            'today_points': my_pts,
            'leader_name': leader.get('name') if leader else None,
            'leader_points': leader_pts,
            'gap_to_first': gap_to_first,
            'second_name': second.get('name') if second else None,
            'second_points': second_pts,
            'lead_over_second': lead_over_second,
            'daily_rounds_chased': daily_rounds,
            'last_action': state.get('last_action', 'none'),
            'redpacket_success': rp_success,
            'redpacket_fail': rp_fail,
            'redpacket_est_usdc': round(rp_total_usdc, 2),
            'total_usdc': total_usdc,
        }

        # 直接输出格式化文本（不需要模型了）
        rank_str = f'#{my_rank}' if my_rank else '未上榜'
        lines = [
            f'📊 AgentHansa 6h 状态报告 ({now.strftime("%H:%M")})',
            f'',
            f'🏷 {agent_name} | Lv.{level} | {info.get("name") or alliance_name}',
            f'📈 排名: {rank_str} | 今日积分: {format_number(my_pts)}',
        ]
        if my_rank == 1:
            lines.append(f'🥇 领先第二 {leader.get("name", "?")} +{format_number(lead_over_second)} 分')
        elif my_rank and gap_to_first is not None:
            lines.append(f'📍 落后第一 {leader.get("name", "?")} {format_number(gap_to_first)} 分')
            if lead_over_second is not None:
                lines.append(f'   领先第二 +{format_number(lead_over_second)} 分')

        lines.append(f'')
        lines.append(f'🔄 今日已追 {daily_rounds} 轮')
        lines.append(f'🧧 今日红包: {rp_success} 成功 / {rp_fail} 失败 | 预估 ${rp_total_usdc:.2f}')
        lines.append(f'💰 累计收益: ${total_usdc}')

        print('\n'.join(lines))

    except Exception as e:
        print(f'ERROR: 状态查询失败: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
