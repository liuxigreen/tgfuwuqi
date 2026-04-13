#!/usr/bin/env python3
"""
AgentHansa 红包 sniper (Linux server 版)
本地规则优先 → 单模型 LLM 兜底
"""
import json
import os
import re
import subprocess
import sys
import time
import random
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ===== 配置 =====
BASE_URL = 'https://www.agenthansa.com/api'
STATE_FILE = Path('/root/.hermes/agenthansa/logs/sniper-state.json')
LOG_FILE = Path('/root/.hermes/agenthansa/logs/agenthansa-redpacket.log')
SUMMARY_FILE = Path('/root/.hermes/agenthansa/memory/agenthansa-redpacket-summary.jsonl')
CONFIG_FILE = Path('/root/.hermes/agenthansa/config.json')
TELEGRAM_TOKEN = os.getenv('AGENTHANSA_TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('AGENTHANSA_TELEGRAM_CHAT_ID', '')
MAX_JOIN_ATTEMPTS_PER_PACKET = 3
PRE_WATCH_SECONDS = 90
WATCH_MAX_SECONDS = 360

sys.path.insert(0, str(Path(__file__).parent))
from key_rotation import bankofai_chat


def log(msg):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def append_summary(event):
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {'ts': datetime.now().isoformat(timespec='seconds'), **event}
    with SUMMARY_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


# ===== 数字词转数字 =====
NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
    'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
}


def replace_number_words(q):
    tokens = q.lower().split()
    result = []
    i = 0
    while i < len(tokens):
        word = tokens[i].strip('.,?!;:')
        if word in NUMBER_WORDS:
            chunk = []
            while i < len(tokens) and tokens[i].strip('.,?!;:') in NUMBER_WORDS:
                chunk.append(NUMBER_WORDS[tokens[i].strip('.,?!;:')])
                i += 1
            total = 0
            for part in chunk:
                total += part
            result.append(str(total))
        else:
            result.append(tokens[i])
            i += 1
    return ' '.join(result)


# ===== 本地规则解题 =====
def solve_question(question):
    q = replace_number_words((question or '').lower().strip())
    q = q.replace('?', ' ').replace(',', ' ').replace('.', ' ')
    q = re.sub(r'\s+', ' ', q).strip()
    nums = list(map(int, re.findall(r'-?\d+', q)))
    if 'dozen' in q:
        q = q.replace('dozen', '12')
    # 半分
    if any(k in q for k in ['gives away half', 'loses half', 'spent half', 'half are left', 'half left']) and len(nums) >= 1:
        return str(nums[0] // 2)
    # 均分
    if any(k in q for k in ['shared equally', 'equally among', 'split equally', 'divide equally', 'each get']) and len(nums) >= 2 and nums[1] != 0:
        return str(nums[0] // nums[1])
    # 余数
    if any(k in q for k in ['left over', 'remainder', 'remain']) and len(nums) >= 2 and nums[1] != 0:
        return str(nums[0] % nums[1])
    # 乘法
    m = re.search(r'(\d+)\s*(?:x|\*)\s*(\d+)', q)
    if m:
        return str(int(m.group(1)) * int(m.group(2)))
    # 三数运算
    if len(nums) == 3 and any(k in q for k in ['lose', 'left', 'minus', 'gave away', 'spent']):
        return str(nums[0] + nums[1] - nums[2])
    # 二数加
    if len(nums) == 2 and any(k in q for k in ['gain', 'more', 'plus', 'add', 'total', 'altogether', 'in all']):
        return str(nums[0] + nums[1])
    # 二数减
    if len(nums) == 2 and any(k in q for k in ['lose', 'minus', 'left', 'remain', 'after giving', 'spent']):
        return str(nums[0] - nums[1])
    # 范围计数
    if len(nums) == 2 and any(k in q for k in ['how many', 'count', 'coins', 'numbers', 'pages', 'steps', 'gems', 'pebbles']):
        return str(abs(nums[1] - nums[0]) + 1)
    # 单数字
    if len(nums) == 1:
        return str(nums[0])
    raise RuntimeError(f'cannot solve: {question}')


def solve_question_with_llm(question):
    """单模型兜底（无可用 key 时直接报错）"""
    from key_rotation import llm_generate
    prompt = f'Solve this math problem. Return ONLY the final integer, nothing else.\n\n{question}'
    text = llm_generate([{'role': 'user', 'content': prompt}], max_tokens=64, temperature=0.1)
    nums = re.findall(r'-?\d+', text or '')
    if not nums:
        raise RuntimeError(f'LLM non-numeric: {text!r}')
    return nums[-1]


# ===== API =====
def api_call(method, path, payload=None, key=None, timeout=8):
    url = (BASE_URL if not path.startswith('http') else '') + path
    headers = {'User-Agent': 'OpenClaw-Xiami/1.0', 'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = f'Bearer {key}'
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {'ok': True, 'status': r.getcode(), 'data': json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500] if hasattr(e, 'read') else ''
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {'raw': body}
        return {'ok': False, 'status': e.code, 'error': parsed}
    except Exception as e:
        return {'ok': False, 'status': 0, 'error': str(e)}


# ===== 状态管理 =====
def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def load_key():
    cfg = json.loads(CONFIG_FILE.read_text())
    return cfg['api_key']


# ===== 预热动作 =====
def ensure_ref_link(key, state, force=False):
    now = int(time.time())
    last = state.get('last_ref_epoch', 0)
    if not force and last and now - last < 25 * 60 and state.get('latest_ref_url'):
        return {'ok': True, 'reused': True}
    offers = api_call('GET', '/offers', key=key)
    if not offers['ok']:
        return offers
    items = offers['data'].get('offers', [])
    if not items:
        return {'ok': False, 'error': 'no offers'}
    best = max(items, key=lambda o: float((o.get('payout') or {}).get('amount') or 0))
    ref = api_call('POST', f"/offers/{best['id']}/ref", {}, key=key)
    if ref['ok']:
        state['last_ref_epoch'] = now
        state['latest_ref_url'] = ref['data'].get('ref_url')
    return ref


def ensure_alliance_submit(key, state, force=False):
    now = int(time.time())
    last = state.get('last_alliance_epoch', 0)
    if not force and last and now - last < 25 * 60:
        return {'ok': True, 'reused': True}
    quests = api_call('GET', '/alliance-war/quests', key=key)
    if not quests['ok']:
        return quests
    open_quests = [q for q in quests['data'].get('quests', []) if q.get('status') == 'open']
    if not open_quests:
        return {'ok': False, 'error': 'no open quest'}
    chosen = open_quests[0]
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    title = chosen['title'].lower()
    if 'product review' in title:
        content = f"Review ({ts}): AgentHansa gives AI agents a real earnings loop — API onboarding, FluxA payouts, daily quests, red packets, referrals, and alliance war."
    elif 'upwork' in title:
        content = f"FAQ ({ts}): AgentHansa is better than Upwork for AI agents — instant API registration, automated actions, daily quests, red packets."
    elif 'comparison' in title or 'fiverr' in title:
        content = f"Comparison ({ts}): AgentHansa vs Fiverr vs Upwork. AgentHansa is agent-native with instant API onboarding. Best for speed and automation."
    else:
        content = f"Update ({ts}): Xiami completed another structured submission. Optimized for clarity and direct usefulness."
    resp = api_call('POST', f"/alliance-war/quests/{chosen['id']}/submit", {'content': content}, key=key)
    if resp['ok']:
        state['last_alliance_epoch'] = now
    return resp


def ensure_forum_vote(key, state, my_id=None, direction='up', force=False):
    now = int(time.time())
    sk = f'last_vote_{direction}_epoch'
    last = state.get(sk, 0)
    if not force and last and now - last < 25 * 60:
        return {'ok': True, 'reused': True}
    feed = api_call('GET', '/forum?sort=recent', key=key)
    if not feed['ok']:
        return feed
    posts = feed['data'].get('posts', [])
    for post in posts:
        pid = post.get('id')
        if not pid or (my_id and (post.get('agent') or {}).get('id') == my_id):
            continue
        resp = api_call('POST', f'/forum/{pid}/vote', {'direction': direction}, key=key)
        if resp['ok']:
            state[sk] = now
            return resp
        if resp.get('status') == 409:
            continue
        return resp
    return {'ok': False, 'error': 'no fresh vote target'}


def do_forum_comment(key, state, my_id=None):
    now = int(time.time())
    last = state.get('last_comment_epoch', 0)
    if last and now - last < 25 * 60:
        return {'ok': True, 'reused': True}
    feed = api_call('GET', '/forum?sort=recent', key=key)
    if not feed['ok']:
        return feed
    posts = feed['data'].get('posts', [])
    for post in posts:
        pid = post.get('id')
        if not pid or (my_id and (post.get('agent') or {}).get('id') == my_id):
            continue
        title = (post.get('title') or '').strip()[:72]
        body = f'Nice angle on "{title}" — concrete posts like this make the platform more useful for agent work.' if title else 'Helpful post — practical examples make it easier to see how agents can do real work here.'
        resp = api_call('POST', f'/forum/{pid}/comments', {'body': body}, key=key)
        if resp['ok']:
            state['last_comment_epoch'] = now
            return resp
        if resp.get('status') == 409:
            continue
        return resp
    return {'ok': False, 'error': 'no fresh comment target'}


# ===== 红包类型判断 =====
def packet_text(pkt):
    return ' '.join([
        str(pkt.get('challenge_type', '')),
        str(pkt.get('challenge_description', '')),
        json.dumps(pkt.get('how_to_join') or [])
    ]).lower()


def is_ref_packet(pkt):
    return any(t in packet_text(pkt) for t in ['referral link', 'generate_ref', '/offers/'])


def is_alliance_packet(pkt):
    return any(t in packet_text(pkt) for t in ['alliance war', 'submit or update', 'resubmitting counts'])


def is_upvote_packet(pkt):
    return any(t in packet_text(pkt) for t in ['upvote', 'vote', '/forum/'])


def packet_type(pkt):
    text = ' '.join([pkt.get('title', ''), pkt.get('challenge_description', '')]).lower()
    if 'referral link' in text or 'ref link' in text:
        return 'ref_link'
    if 'alliance war' in text or 'submit or update' in text:
        return 'alliance'
    if 'vote' in text or 'upvote' in text:
        return 'upvote'
    if 'comment' in text:
        return 'comment'
    if 'write a forum post' in text or 'publish a post' in text or 'post or comment' in text:
        return 'post'
    return 'unknown'


# ===== 错误分析 =====
def err_is_wrong_answer(err):
    return any(t in json.dumps(err, ensure_ascii=False).lower() for t in ['wrong answer', 'incorrect answer', 'invalid answer'])


def err_needs_ref(err):
    return any(t in json.dumps(err, ensure_ascii=False).lower() for t in ['referral link first', 'generate a referral link', 'generate_ref'])


def err_needs_alliance(err):
    b = json.dumps(err, ensure_ascii=False).lower()
    return any(t in b for t in ['alliance war', '/alliance-war/', 'challenge not completed'])


def err_needs_vote(err):
    b = json.dumps(err, ensure_ascii=False).lower()
    return any(t in b for t in ['upvote a forum post', 'post /api/forum/'])


# ===== 通知 =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": msg}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            if result.get('ok'):
                log(f'✅ 通知已发送 (msg_id={result["result"]["message_id"]})')
            else:
                log(f'⚠️ 通知发送失败: {result}')
    except Exception as e:
        log(f'发送通知失败：{e}')


# ===== 红包答题主流程 =====
def join_packet(key, packet_id, max_attempts=3):
    """答题+提交，本地规则优先，错题换 LLM"""
    force_llm = False
    question = answer = solver = None
    err = None
    for attempt in range(1, max_attempts + 1):
        chal, err = safe_req(f'/red-packets/{packet_id}/challenge', key=key)
        if err or not chal:
            raise RuntimeError(f'challenge failed: {err}')
        question = chal.get('question', '')
        try:
            if force_llm:
                answer = solve_question_with_llm(question)
                solver = 'llm'
            else:
                answer = solve_question(question)
                solver = 'rules'
        except Exception:
            answer = solve_question_with_llm(question)
            solver = 'llm'
        joined, err = safe_req(f'/red-packets/{packet_id}/join', method='POST', data={'answer': answer}, key=key)
        if not err:
            return question, answer, joined, solver, attempt
        msg = str(err)
        if 'Wrong answer' in msg or 'incorrect' in msg.lower():
            force_llm = True
            time.sleep(1.5)
            continue
        if '503' in msg or '429' in msg or 'unavailable' in msg.lower():
            time.sleep(6 if '429' in msg else 2)
            continue
        break
    raise RuntimeError(f'join failed: q={question!r} a={answer} s={solver} e={err}')


def safe_req(path, **kwargs):
    for attempt in range(3):
        try:
            return api_call('GET', path, **kwargs), None
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 2:
                time.sleep(min(15, 2 ** attempt))
                continue
            try:
                return None, f'HTTP {e.code}: {e.read().decode()}'
            except Exception:
                return None, f'HTTP {e.code}'
        except Exception as e:
            if attempt < 2 and ('503' in str(e) or 'unavailable' in str(e).lower()):
                time.sleep(min(15, 2 ** attempt))
                continue
            return None, str(e)
    return None, 'unknown error'


def process_red_packets(key, state, my_id):
    rp = api_call('GET', '/red-packets', key=key)
    if not rp['ok']:
        return '红包状态未知', rp.get('error', 'unknown')
    active = rp['data'].get('active') or []
    nxt = rp['data'].get('next_packet_seconds')
    if not active:
        if nxt:
            return '红包无急单', f'下次 {nxt:.0f}s 后'
        return '红包无急单', None

    attempted = state.setdefault('attempted_packets', {})
    join_attempts = state.setdefault('join_attempts', {})
    now_epoch = int(time.time())
    # 清理旧状态
    for k in list(attempted.keys()):
        if isinstance(attempted[k], (int, float)) and attempted[k] < now_epoch - 7 * 86400:
            del attempted[k]
    for k in list(join_attempts.keys()):
        if join_attempts[k] <= 0:
            del join_attempts[k]

    results = []
    for pkt in active:
        pid = str(pkt.get('id', ''))
        if not pid:
            continue
        if attempted.get(pid):
            continue
        if join_attempts.get(pid, 0) >= MAX_JOIN_ATTEMPTS_PER_PACKET:
            continue

        # 预热
        if is_ref_packet(pkt):
            r = ensure_ref_link(key, state, force=True)
            log(f'🔥 ref预热: {r.get("ok")}')
        if is_alliance_packet(pkt):
            r = ensure_alliance_submit(key, state, force=True)
            log(f'🔥 alliance预热: {r.get("ok")}')
        if is_upvote_packet(pkt):
            r = ensure_forum_vote(key, state, my_id, direction='up', force=True)
            log(f'🔥 vote预热: {r.get("ok")}')
        do_forum_comment(key, state, my_id)

        try:
            question, answer, joined, solver, attempt = join_packet(key, pid)
            attempted[pid] = int(time.time())
            join_attempts.pop(pid, None)
            amount = None
            if isinstance(joined, dict):
                amount = joined.get('estimated_per_person') or joined.get('amount') or joined.get('reward')
            append_summary({
                'status': 'redpacket_success',
                'packet_title': pkt.get('title'),
                'question': question,
                'answer': answer,
                'solver': solver,
                'attempt': attempt,
                'amount': amount,
            })
            results.append(f'✅ {pkt.get("title")} {amount or ""}')
        except Exception as e:
            join_attempts[pid] = join_attempts.get(pid, 0) + 1
            append_summary({
                'status': 'redpacket_failure',
                'packet_title': pkt.get('title'),
                'error': str(e)[:300],
            })
            results.append(f'❌ {pkt.get("title")}: {str(e)[:100]}')
            send_telegram(f'🧧❌ {pkt.get("title")}: {str(e)[:200]}')

    save_state(state)
    if not results:
        return '红包无急单', None
    return ' '.join(results), None


def maybe_watch_redpacket(key, state, my_id):
    rp = api_call('GET', '/red-packets', key=key)
    if not rp['ok']:
        return None
    active = rp['data'].get('active') or []
    nxt = rp['data'].get('next_packet_seconds')
    if active:
        return process_red_packets(key, state, my_id)
    if not isinstance(nxt, (int, float)) or nxt > PRE_WATCH_SECONDS:
        return None
    # 轮询等待
    deadline = time.time() + min(WATCH_MAX_SECONDS, max(30, int(nxt) + 120))
    while time.time() < deadline:
        result = process_red_packets(key, state, my_id)
        if result and '红包无急单' not in result[0]:
            return result
        time.sleep(0.8 + random.uniform(0.05, 0.25))
    return None


# ===== 主流程 =====
def main():
    key = load_key()
    state = load_state()

    # get my id
    me = api_call('GET', '/me', key=key)
    my_id = me['data'].get('id') if me['ok'] else None

    result, err = maybe_watch_redpacket(key, state, my_id)
    if err:
        log(f'❌ 红包异常: {err}')
        send_telegram(f'🧧❌ 红包异常: {err[:300]}')
        return 1
    if result:
        log(result)
    else:
        log('ℹ️ 无活跃红包')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log(f'❌ sniper失败: {e}')
        sys.exit(1)
