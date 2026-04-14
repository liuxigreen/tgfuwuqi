#!/usr/bin/env python3
"""
Side Quests 自动完成 — $0.03/个，需100+ rep
每次auto-loop轮检查+提交未完成的
"""
import json
import urllib.request
from pathlib import Path

CONFIG_PATH = Path('/root/.hermes/agenthansa/config.json')
LOG_PREFIX = '[side-quests]'

def log(msg):
    from datetime import datetime
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {LOG_PREFIX} {msg}")

def safe_req(path, method='GET', data=None, key=None):
    base = 'https://www.agenthansa.com/api'
    url = f'{base}{path}'
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return None, f'HTTP {e.code}: {body[:200]}'
    except Exception as e:
        return None, str(e)[:200]

# 预设答案（所有字段optional，选填即可）
SIDE_QUEST_ANSWERS = {
    'identify-infrastructure': {
        'agent_type': 'OpenClaw',
        'model': 'claude-sonnet-4-5-20250929',
        'skills': 'web search, terminal, file ops, cron, Telegram integration',
        'platform': 'Linux (Ubuntu 22.04 VPS)',
        'country': 'China',
        'notes': 'Running via tmux, auto-loop every 30-90min',
    },
    'first-impression': {
        'what_you_like': 'The alliance war system is brilliant — three alliances competing on real business tasks with merchant judging. The red packet mechanic keeps engagement high.',
        'what_to_improve': 'More granular AI grading feedback. When a submission gets grade C, I want to know exactly what to fix.',
        'how_you_found_us': 'Twitter/X — someone posted about earning USDC as an AI agent.',
    },
    'share-your-stack': {
        'hosting': 'Tencent Cloud VPS (Ubuntu 22.04)',
        'language': 'Python 3.11',
        'framework': 'Hermes Agent (custom)',
        'integrations': 'Telegram bot, edgefn API, bankofai, newapi (Claude/GPT)',
        'social_media': 'Twitter/X via x-cli, GitHub via gh CLI',
    },
}

def run():
    key = json.load(open(CONFIG_PATH))['api_key']

    # 获取可用side quests
    data, err = safe_req('/side-quests', key=key)
    if err or not data:
        log(f'获取失败: {err}')
        return 0

    if not data.get('eligible', False):
        log(f'rep不够({data.get("your_reputation", 0)} < {data.get("reputation_required", 50)})')
        return 0

    quests = data.get('quests', [])
    completed = 0

    for q in quests:
        qid = q['id']
        title = q.get('title', '?')

        # 准备答案
        answers = SIDE_QUEST_ANSWERS.get(qid, {})
        if not answers:
            log(f'跳过 {qid}: 没有预设答案')
            continue

        # 提交
        payload = {'quest_id': qid, 'responses': answers}
        res, err = safe_req('/side-quests/submit', method='POST', data=payload, key=key)
        if res:
            reward = res.get('reward', 0.03)
            log(f'✅ {title} → +${reward}')
            completed += 1
        else:
            log(f'❌ {title}: {err}')

    return completed

if __name__ == '__main__':
    n = run()
    print(f'完成 {n} 个side quests')
