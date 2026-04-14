#!/usr/bin/env python3
"""
AgentHansa Collective Bounties 自动处理
监控 /api/collective/bounties，有新的自动join+提交
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agenthansa_auto_pipelines import build_submission_content
from key_rotation import llm_generate

CONFIG = Path('/root/.hermes/agenthansa/config.json')
STATE_FILE = Path('/root/.hermes/agenthansa/memory/bounties-state.json')
LOG_PREFIX = '[bounties]'
BASE = 'https://www.agenthansa.com/api'
UA = 'OpenClaw-Xiami/1.0'

# 不需要外部行动的任务类型
TEXT_ONLY_CATEGORIES = {'copywriting', 'writing', 'content', 'research', 'analysis',
                        'strategy', 'feedback', 'design-creative', 'marketing'}


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'{LOG_PREFIX} {ts} {msg}', flush=True)


def load_cfg():
    return json.loads(CONFIG.read_text())


def api_call(key, method, path, payload=None, timeout=12):
    url = BASE + path
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': UA,
    }
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return {'ok': True, 'status': r.getcode(), 'data': json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', errors='replace')[:500]
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {'raw': raw}
        return {'ok': False, 'status': e.code, 'error': parsed}
    except Exception as e:
        return {'ok': False, 'status': 0, 'error': str(e)}


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {'attempted': {}, 'last_run': None}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def is_text_only(bounty):
    """判断是否是纯文本任务（不需要外部行动）"""
    title = (bounty.get('title') or '').lower()
    desc = (bounty.get('description') or '').lower()
    cat = (bounty.get('category') or '').lower()
    tags = [t.lower() for t in (bounty.get('tags') or [])]
    require_proof = bounty.get('require_proof', False)
    
    # 需要外部行动的关键词
    external_keywords = [
        'followers', 'follow on', 'backlinks', 'newsletter mention',
        'twitter followers', 'get 1000', 'get 500', 'github stars',
        'post on twitter', 'tweet about', 'post on reddit',
        'linkedin post', 'youtube video', 'tiktok',
    ]
    
    combined = title + ' ' + desc
    if any(k in combined for k in external_keywords):
        return False
    if require_proof:
        return False
    if cat in TEXT_ONLY_CATEGORIES:
        return True
    # 默认：不需要proof且不是外部行动关键词 = 文本任务
    return True


def generate_bounty_content(bounty):
    """为bounty生成内容"""
    title = bounty.get('title', '')
    desc = bounty.get('description', '')[:500]
    goal = bounty.get('goal', '')[:300]
    category = bounty.get('category', '')
    
    prompt = (
        f'You are completing a freelance task on AgentHansa platform.\n\n'
        f'Task: {title}\n'
        f'Description: {desc}\n'
        f'Goal: {goal}\n'
        f'Category: {category}\n\n'
        f'Write a complete, high-quality deliverable. Be specific and concrete.\n'
        f'Include real names, data, numbers where appropriate.\n'
        f'Length: 80-200 words for text. Output ONLY the deliverable content.'
    )
    
    try:
        result = llm_generate(
            [{'role': 'user', 'content': prompt}],
            max_tokens=600, temperature=0.7, preferred='sonnet'
        )
        if result and len(result.split()) >= 20:
            return result.strip()
    except Exception as e:
        log(f'内容生成失败: {e}')
    
    return None


def main():
    cfg = load_cfg()
    key = cfg.get('api_key', '')
    if not key:
        log('No API key')
        return
    
    state = load_state()
    attempted = state.get('attempted', {})
    now_epoch = int(time.time())
    
    # 清理过期记录（7天）
    attempted = {k: v for k, v in attempted.items() if now_epoch - v < 7 * 86400}
    
    # 拉bounties
    resp = api_call(key, 'GET', '/collective/bounties')
    if not resp['ok']:
        log(f'API error: {resp.get("status")} {str(resp.get("error",""))[:100]}')
        return
    
    bounties = resp['data'] if isinstance(resp['data'], list) else resp['data'].get('bounties', [])
    log(f'拉到 {len(bounties)} 个bounties')
    
    joined_count = 0
    submitted_count = 0
    
    for b in bounties:
        bid = b.get('id', '')
        title = b.get('title', '')[:60]
        status = (b.get('status') or '').lower()
        joined = b.get('joined', False)
        reward = b.get('reward_amount', 0)
        participants = b.get('participant_count', 0) or 0
        max_p = b.get('max_participants', 0) or 0
        deadline = b.get('deadline', '')
        
        # 跳过已完成/过期
        if status not in ('in_progress', 'open'):
            continue
        
        # 跳过已尝试
        if bid in attempted:
            continue
        
        # 跳过需要外部行动的
        if not is_text_only(b):
            log(f'跳过(需外部行动): {title}')
            attempted[bid] = now_epoch
            continue
        
        # 检查是否满了
        if max_p > 0 and participants >= max_p and not joined:
            log(f'跳过(已满): {title} ({participants}/{max_p})')
            attempted[bid] = now_epoch
            continue
        
        # 检查deadline
        if deadline:
            try:
                dl = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                if dl < datetime.now(timezone.utc):
                    log(f'跳过(已过期): {title}')
                    attempted[bid] = now_epoch
                    continue
            except Exception:
                pass
        
        log(f'处理: ${reward} — {title}')
        
        # Join
        if not joined:
            join_resp = api_call(key, 'POST', f'/collective/bounties/{bid}/join')
            if not join_resp['ok']:
                err = str(join_resp.get('error', ''))
                if 'full' in err.lower():
                    log(f'  Join失败(满): {err[:80]}')
                    attempted[bid] = now_epoch
                    continue
                elif 'already' in err.lower() or join_resp.get('status') == 409:
                    log(f'  已加入，继续提交')
                    joined = True
                else:
                    log(f'  Join失败: {err[:100]}')
                    continue
            else:
                joined_count += 1
                log(f'  Join成功')
                joined = True
                time.sleep(2)
        
        # 生成内容
        content = generate_bounty_content(b)
        if not content:
            log(f'  内容生成失败，跳过')
            continue
        
        log(f'  内容生成: {len(content.split())}词')
        
        # 提交
        time.sleep(3)
        submit_resp = api_call(key, 'POST', f'/collective/bounties/{bid}/submit', {
            'description': content,
            'url': ''
        })
        
        if submit_resp['ok']:
            submitted_count += 1
            log(f'  ✅ 提交成功: {title}')
            attempted[bid] = now_epoch
        else:
            err = str(submit_resp.get('error', ''))
            log(f'  ❌ 提交失败: {err[:100]}')
            if 'not participating' in err.lower():
                attempted[bid] = now_epoch
    
    # 保存状态
    state['attempted'] = attempted
    state['last_run'] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    
    log(f'完成: join={joined_count}, submit={submitted_count}')
    
    # 通知
    if submitted_count > 0:
        try:
            from agenthansa_notify import send_telegram_message
            send_telegram_message(f'🎁 Bounties: join={joined_count} submit={submitted_count}')
        except Exception:
            pass


if __name__ == '__main__':
    main()
