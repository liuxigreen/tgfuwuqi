#!/usr/bin/env python3
"""红包通知 - 通过 Telegram 发送结果"""
import json
import subprocess
from datetime import datetime


TELEGRAM_CHAT_ID = '6305628029'
OPENCLAW_BIN = '/root/.nvm/versions/node/v22.22.1/bin/openclaw'


def notify_redpacket_summary(result: dict):
    """发送红包结果通知"""
    joins = result.get('joins') or []
    if not joins:
        return {'skipped': True, 'reason': 'no_joins'}

    joined = [j for j in joins if j.get('joined')]
    failed = [j for j in joins if not j.get('joined') and j.get('reason') not in ('already_attempted', 'retry_backoff_active')]

    if not joined and not failed:
        return {'skipped': True, 'reason': 'no_actionable_results'}

    active_count = result.get('active_count', 0)
    ts = result.get('ts', datetime.now().isoformat())[:19]

    parts = []
    if joined:
        parts.append(f'🧧 抢到 {len(joined)} 个')
        for j in joined:
            resp = j.get('resp') or {}
            amount = resp.get('amount') or resp.get('per_person') or '?'
            parts.append(f'  +${amount}')
    if failed:
        parts.append(f'❌ 失败 {len(failed)} 个')
        for j in failed:
            reason = j.get('reason', '?')
            parts.append(f'  {reason}')

    msg = f'[{ts}] 红包结果: active={active_count}\n' + '\n'.join(parts)

    try:
        r = subprocess.run(
            [OPENCLAW_BIN, 'message', 'send', '--target', f'telegram:{TELEGRAM_CHAT_ID}', '--message', msg],
            timeout=60, capture_output=True, text=True,
        )
        if r.returncode == 0:
            return {'ok': True, 'message': 'sent'}
        return {'ok': False, 'error': r.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': 'timeout'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
