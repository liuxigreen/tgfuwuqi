#!/usr/bin/env python3
"""
AgentHansa 通知模块 - 所有通知走 TG
"""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ENV_FILE = Path('/root/.hermes/agenthansa/.env.agenthansa')

def _load_env():
    env = {}
    for k in ('AGENTHANSA_TELEGRAM_TOKEN', 'AGENTHANSA_TELEGRAM_CHAT_ID'):
        val = os.environ.get(k)
        if val:
            env[k] = val
    if env.get('AGENTHANSA_TELEGRAM_TOKEN'):
        return env
    try:
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env


def send_telegram_message(text: str, chat_id: str = None, token: str = None) -> dict:
    env = _load_env()
    bot_token = token or env.get('AGENTHANSA_TELEGRAM_TOKEN', '')
    target_chat_id = chat_id or env.get('AGENTHANSA_TELEGRAM_CHAT_ID', '6305628029')
    if not bot_token or '...' in bot_token:
        return {'ok': False, 'error': 'no_valid_telegram_token'}
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': target_chat_id, 'text': text}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return {'ok': True, 'message_id': result.get('result', {}).get('message_id')}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:200]}


def notify(text: str) -> dict:
    """快捷通知"""
    return send_telegram_message(text)


def notify_redpacket_summary(result: dict) -> dict:
    """红包结果通知 - 只在成功或失败时通知"""
    joins = result.get('joins') or []

    joined = [j for j in joins if j.get('joined')]
    failed = [j for j in joins if not j.get('joined')
              and j.get('reason') not in ('already_attempted', 'retry_backoff_active')]

    # 没有成功或失败 → 不通知
    if not joined and not failed:
        return {'ok': True, 'skipped': True, 'reason': 'no_success_or_failure'}

    ts = datetime.now().strftime('%H:%M')
    lines = []

    for j in joined:
        resp = j.get('resp') or {}
        amount = resp.get('amount') or resp.get('per_person') or '?'
        ans = j.get('answer', '?')
        q = (j.get('question', '') or '')[:40]
        lines.append(f'🧧✅ [{ts}] 抢到 ${amount}')
        lines.append(f'  题:{q}')
        lines.append(f'  答案:{ans} 模式:{j.get("solver", "?")}')

    for j in failed:
        reason = j.get('reason', 'unknown')
        status = j.get('status', '')
        q = (j.get('question', '') or '')[:40]
        
        # 获取分析结果
        analysis = j.get('failure_analysis', {})
        suggestion = j.get('fix_suggestion', {})
        
        failure_type = analysis.get('failure_type', reason)
        description = analysis.get('description', reason)
        severity = analysis.get('severity', 'unknown')
        
        lines.append(f'🧧❌ [{ts}] 失败 [{failure_type}] severity={severity}')
        lines.append(f'  题:{q}')
        lines.append(f'  原因:{description}')
        
        # 显示修复建议
        if suggestion:
            action = suggestion.get('action', '')
            desc = suggestion.get('description', '')
            if action and desc:
                lines.append(f'  建议:{desc}')
        
        # 显示错误详情（缩短）
        error_detail = json.dumps(j.get('resp') or j.get('error') or '', ensure_ascii=False)[:100]
        if error_detail and error_detail != '""':
            lines.append(f'  错误:{error_detail}')

    return send_telegram_message('\\n'.join(lines))


def notify_quest_result(title: str, reward: str, success: bool, error: str = '') -> dict:
    """Quest 提交结果通知"""
    ts = datetime.now().strftime('%H:%M')
    if success:
        msg = f'📝✅ [{ts}] Quest 提交成功\n  {title[:50]}\n  奖励: {reward}'
    else:
        msg = f'📝❌ [{ts}] Quest 提交失败\n  {title[:50]}\n  原因: {error[:100]}'
    return send_telegram_message(msg)


def notify_daily_report(stats: dict) -> dict:
    """每日总结通知"""
    lines = [
        f'📊 AgentHansa 日报 [{stats.get("date", "today")}]',
        f'  Quest: {stats.get("quests_submitted", 0)}提/{stats.get("quests_accepted", 0)}过',
        f'  红包: {stats.get("rp_won", 0)}抢/{stats.get("rp_total", 0)}次',
        f'  论坛: {stats.get("comments", 0)}评论/{stats.get("votes", 0)}投票',
        f'  排名: {stats.get("rank", "?")}',
        f'  收入: ${stats.get("earnings", 0)}',
    ]
    if stats.get('issues'):
        lines.append(f'  ⚠️ 问题: {stats["issues"]}')
    if stats.get('adjustments'):
        lines.append(f'  🔧 调整: {stats["adjustments"]}')
    return send_telegram_message('\n'.join(lines))


def notify_alert(text: str) -> dict:
    """告警通知"""
    return send_telegram_message(f'⚠️ [告警] {text}')


def notify_sniper_event(event_type: str, details: str = '') -> dict:
    emoji = {'start': '🟢', 'stop': '🔴', 'error': '⚠️', 'info': 'ℹ️'}.get(event_type, '📌')
    msg = f'{emoji} Sniper {event_type}'
    if details:
        msg += f': {details}'
    return send_telegram_message(msg)
