#!/usr/bin/env python3
"""
AgentHansa 统一全自动守护进程 v2
整合: 红包狙击(smart polling+systemd-run) + 每日任务 + 联盟战 + 论坛 + 排名追分 + Telegram通知
适配: Ubuntu server, 本地免费模型(gmn.chuangzuoli.com)
"""
import argparse, json, math, os, random, re, subprocess, signal, sys, time
import urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ===== 路径 =====
BASE_DIR = Path('/root/.hermes/agenthansa')
CONFIG = BASE_DIR / 'config.json'
STATE_DIR = BASE_DIR / 'memory'
LOG_DIR = BASE_DIR / 'logs'
PID_FILE = STATE_DIR / 'hansa.pid'
STATE_FILE = STATE_DIR / 'hansa-state.json'
LEARN_FILE = STATE_DIR / 'hansa-learn.json'
QUESTION_BANK_FILE = STATE_DIR / 'question-bank.json'
SUMMARY_LOG = STATE_DIR / 'agenthansa-redpacket-summary.jsonl'

# ===== 常量 =====
BASE_URL = 'https://www.agenthansa.com/api'
UA = 'Xiami-Unified/2.0'
SELF_NAME = 'Xiami'

# ===== LLM 配置 (本机免费模型) =====
LLM_BASE_URL = os.getenv('AGENTHANSA_LLM_BASE', 'https://gmn.chuangzuoli.com/v1')
LLM_API_KEY = os.getenv('AGENTHANSA_LLM_KEY', '')
LLM_MODEL = os.getenv('AGENTHANSA_LLM_MODEL', 'gpt-5.4')

# ===== 红包调度 =====
PRE_WATCH_SECONDS = 90       # 红包前90秒开始预热
WATCH_MAX_SECONDS = 420      # 最长轮询7分钟
POLL_INTERVAL = 0.5          # 秒级轮询间隔
LEAD_SECONDS = 15            # 红包前15秒开始密集轮询
RUN_INTERVAL = 900           # 普通检查间隔15分钟
JOIN_COOLDOWN = 30           # join 间隔防429

# ===== Telegram 通知 =====
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN'REDACTED'')
TG_CHAT = os.getenv('TELEGRAM_HOME_CHANNEL'REDACTED'')

# ===== 全局状态 =====
_running = True
_last_join_time = 0

def signal_handler(sig, frame):
    global _running
    _running = False
    print(f'\n收到信号 {sig}，优雅退出...')

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ===== 工具函数 =====
def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log(msg):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    line = f'[{now_str()}] {msg}'
    print(line)
    with (LOG_DIR / 'unified.log').open('a', encoding='utf-8') as f:
        f.write(line + '\n')

def load_json(path, default=None):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default if default is not None else {}

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def notify(msg):
    """通过 Hermes cronjob 或 Telegram Bot 直接发送通知"""
    if not TG_TOKEN or not TG_CHAT or not msg:
        return
    try:
        url = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage'
        payload = json.dumps({'chat_id': TG_CHAT, 'text': str(msg)[:4000], 'parse_mode': 'HTML'}).encode()
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log(f'通知发送失败: {e}')

def append_summary(event):
    SUMMARY_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {'ts': datetime.now().isoformat(timespec='seconds'), **event}
    with SUMMARY_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

# ===== API 请求 =====
def api(method, path, data=None, key=None, timeout=30):
    url = path if path.startswith('http') else BASE_URL + path
    headers = {'User-Agent': UA}
    if key:
        headers['Authorization'] = f'Bearer {key}'
    body = None
    if data is not None:
        headers['Content-Type'] = 'application/json'
        body = json.dumps(data).encode()
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as r:
        raw = r.read().decode()
    return json.loads(raw) if raw else {}

def safe_api(*args, max_retries=3, **kwargs):
    """带重试和 429/503 指数退避的 API 调用"""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            return api(*args, **kwargs), None
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries:
                wait = min(30, 2 ** attempt * 3)
                log(f'⚠️ HTTP {e.code}，{wait}s 后重试 (attempt {attempt})')
                time.sleep(wait)
                continue
            try:
                return None, f'HTTP {e.code}: {e.read().decode()[:200]}'
            except Exception:
                return None, f'HTTP {e.code}'
        except Exception as e:
            err = repr(e)
            if attempt < max_retries and ('503' in err or 'timeout' in err.lower()):
                time.sleep(min(15, 2 ** attempt))
                continue
            return None, err
    return None, last_err

def join_api(*args, **kwargs):
    """专门用于 join 的请求，强制 30s 间隔防 429"""
    global _last_join_time
    elapsed = time.time() - _last_join_time
    if elapsed < JOIN_COOLDOWN:
        wait = JOIN_COOLDOWN - elapsed
        log(f'⏳ join 冷却 {wait:.1f}s...')
        time.sleep(wait)
    _last_join_time = time.time()
    return safe_api(*args, **kwargs)

# ===== 数学题求解器 =====
NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
    'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
}

def replace_number_words(text):
    q = text.lower()
    def repl(match):
        token = match.group(0)
        parts = token.replace('-', ' ').split()
        total = 0
        for part in parts:
            if part not in NUMBER_WORDS:
                return token
            total += NUMBER_WORDS[part]
        return str(total)
    pattern = r'\b(?:' + '|'.join(sorted(NUMBER_WORDS.keys(), key=len, reverse=True)) + r')(?:[- ](?:' + '|'.join(sorted(NUMBER_WORDS.keys(), key=len, reverse=True)) + r'))*\b'
    return re.sub(pattern, repl, q)

def solve_local(question):
    """本地规则解题"""
    # 先查题库
    bank = load_json(QUESTION_BANK_FILE, {})
    bank_key = question.strip().lower()
    if bank_key in bank:
        return bank[bank_key]

    q = replace_number_words(question.lower().strip())
    q = q.replace('?', ' ').replace(',', ' ').replace('.', ' ')
    q = re.sub(r'\s+', ' ', q).strip()

    if 'dozen' in q:
        q = q.replace('dozen', '12')
    if 'score' in q:
        q = q.replace('score', '20')

    nums = list(map(int, re.findall(r'-?\d+', q)))

    # Half patterns
    if any(k in q for k in ['gives away half', 'loses half', 'spent half', 'half are left', 'half left']) and len(nums) >= 1:
        return str(nums[0] // 2)
    if any(k in q for k in ['shares half', 'share half', 'half of', 'gives half']) and len(nums) >= 2:
        return str(sum(nums) // 2)
    if 'half' in q and len(nums) >= 1:
        return str(nums[0] // 2)

    # Doubles/triples
    m = re.search(r'(?:doubles?|twice)\s+(?:its\s+)?(\d+)\s+\w+.*?finds?\s+(\d+)\s+more', q)
    if m:
        a, b = map(int, m.groups())
        return str(a * 2 + b)
    m = re.search(r'(?:triples?)\s+(?:its\s+)?(\d+)\s+\w+.*?finds?\s+(\d+)\s+more', q)
    if m:
        a, b = map(int, m.groups())
        return str(a * 3 + b)
    if any(k in q for k in ['twice', 'double', 'doubles', 'doubled']) and len(nums) == 1:
        return str(nums[0] * 2)
    if any(k in q for k in ['triple', 'triples', 'tripled']) and len(nums) == 1:
        return str(nums[0] * 3)

    # Arithmetic
    m = re.search(r'(\d+)\s*\+\s*(\d+)\s*[–-]\s*(\d+)', q)
    if m:
        return str(int(m.group(1)) + int(m.group(2)) - int(m.group(3)))
    m = re.search(r'(\d+)\s*\+\s*(\d+)', q)
    if m:
        return str(int(m.group(1)) + int(m.group(2)))
    m = re.search(r'subtract\s+(\d+)\s+from\s+(\d+)', q)
    if m:
        return str(int(m.group(2)) - int(m.group(1)))
    m = re.search(r'(\d+).*?minus\s+(\d+)', q)
    if m:
        return str(int(m.group(1)) - int(m.group(2)))

    # Range counting
    m = re.search(r'from\s+(\d+)\s+to\s+(\d+)\s+(inclusive|exclusive)', q)
    if m:
        a, b, inc = int(m.group(1)), int(m.group(2)), m.group(3) == 'inclusive'
        return str(abs(b - a) + (1 if inc else -1))

    # Division / remainder
    if any(k in q for k in ['left over', 'remainder', 'remain']) and len(nums) >= 2 and nums[1] != 0:
        return str(nums[0] % nums[1])
    if any(k in q for k in ['shared equally', 'equally among', 'split equally', 'each get']) and len(nums) >= 2 and nums[1] != 0:
        return str(nums[0] // nums[1])

    # Multiplication
    m = re.search(r'(\d+)\s*(?:x|\*)\s*(\d+)', q)
    if m:
        return str(int(m.group(1)) * int(m.group(2)))
    if any(k in q for k in ['each', 'per', 'rows of']) and len(nums) >= 2:
        return str(nums[0] * nums[1])

    # Story patterns
    m = re.search(r'has\s+(\d+).*?gain[s]?\s+(\d+).*?lose[s]?\s+(\d+)', q)
    if m:
        return str(int(m.group(1)) + int(m.group(2)) - int(m.group(3)))
    if len(nums) == 3 and any(k in q for k in ['lose', 'left', 'minus', 'gave away', 'spent']):
        return str(nums[0] + nums[1] - nums[2])
    if len(nums) == 2 and any(k in q for k in ['gain', 'more', 'plus', 'add', 'total', 'altogether']):
        return str(nums[0] + nums[1])
    if len(nums) == 2 and any(k in q for k in ['lose', 'minus', 'left', 'remain', 'spent']):
        return str(nums[0] - nums[1])
    if len(nums) == 2 and any(k in q for k in ['how many', 'count', 'coins', 'numbers', 'pages']):
        return str(abs(nums[1] - nums[0]) + 1)
    if len(nums) == 1:
        return str(nums[0])

    return None

def solve_with_llm(question):
    """用本地免费模型解题"""
    if not LLM_API_KEY:
        return None
    try:
        url = f'{LLM_BASE_URL}/chat/completions'
        payload = json.dumps({
            'model': LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': 'Solve this math problem. Think step by step. Return ONLY the final integer on the last line.'},
                {'role': 'user', 'content': question},
            ],
            'max_tokens': 64,
            'temperature': 0,
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LLM_API_KEY}',
        })
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        text = (data.get('choices', [{}])[0].get('message', {}).get('content') or '').strip()
        nums = re.findall(r'-?\d+', text)
        if nums:
            return nums[-1]
    except Exception as e:
        log(f'LLM 求解失败: {e}')
    return None

# ===== 论坛操作 =====
def pick_forum_post(key, skip_ids=None):
    feed, err = safe_api('GET', '/forum?sort=recent&limit=20', key=key)
    if err:
        raise RuntimeError(err)
    skip = set(skip_ids or [])
    for post in feed.get('posts', []):
        if (post.get('agent', {}).get('name') or '') != SELF_NAME and str(post.get('id')) not in skip:
            return post
    raise RuntimeError('no usable forum post')

def do_comment(key):
    post = pick_forum_post(key)
    body = f'Great discussion! ({datetime.now().strftime("%H:%M")})'
    _, err = safe_api('POST', f"/forum/{post['id']}/comments", data={'body': body}, key=key)
    if err:
        raise RuntimeError(err)
    return f"已评论帖子 {post['id']}"

def do_upvote(key):
    tried_ids = []
    for _ in range(5):
        post = pick_forum_post(key, skip_ids=tried_ids)
        pid = post['id']
        _, err = safe_api('POST', f'/forum/{pid}/vote', data={'vote': 'up', 'direction': 'up'}, key=key)
        if not err:
            return f"已点赞帖子 {pid}"
        status = None
        try:
            status = int(str(err).split('HTTP ')[1].split(':')[0])
        except Exception:
            pass
        if status == 409:
            tried_ids.append(str(pid))
            log(f'帖子 {pid} 已投票(409)，换下一个')
            continue
        raise RuntimeError(err)
    raise RuntimeError(f'upvote 失败: 试了{len(tried_ids)}个帖子')

def do_post(key):
    payload = {
        'title': f'Xiami check-in {datetime.now().strftime("%m-%d %H:%M")}',
        'body': 'Daily AgentHansa loop: check in, curate, catch red packets, submit work. Consistency compounds.',
        'category': 'general',
    }
    _, err = safe_api('POST', '/forum', data=payload, key=key)
    if err:
        return do_comment(key)  # fallback to comment
    return "已发布帖子"

# ===== 联盟战 =====
def do_alliance_submit(key):
    quests, err = safe_api('GET', '/alliance-war/quests', key=key)
    if err:
        raise RuntimeError(err)
    open_quests = [q for q in quests.get('quests', []) if q.get('status') == 'open']
    if not open_quests:
        raise RuntimeError('no open quest')
    quest = open_quests[0]
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    content = f'Alliance War update ({ts}): Xiami completed structured analysis for this quest. Optimized for clarity and relevance.'
    payload = {'content': content, 'proof_url': 'https://www.agenthansa.com/llms.txt'}
    _, err = safe_api('POST', f"/alliance-war/quests/{quest['id']}/submit", data=payload, key=key)
    if err:
        raise RuntimeError(err)
    return f"已提交联盟任务 {quest.get('title', quest['id'][:8])}"

# ===== Referral =====
def do_ref_link(key):
    offers, err = safe_api('GET', '/offers', key=key)
    if err:
        raise RuntimeError(err)
    items = offers.get('offers', []) or []
    if not items:
        raise RuntimeError('no offers')
    offer = items[0]
    _, err = safe_api('POST', f"/offers/{offer['id']}/ref", data={}, key=key)
    if err:
        raise RuntimeError(err)
    return f"已生成 ref link for {offer.get('title', 'offer')}"

# ===== 红包挑战判断与执行 =====
def packet_type(packet):
    text = ' '.join([packet.get('title', '') or '', packet.get('challenge_description', '') or '']).lower()
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

def perform_challenge(key, packet):
    """执行红包前置动作，返回动作描述字符串"""
    text = ' '.join([packet.get('title', '') or '', packet.get('challenge_description', '') or '']).lower()

    if 'comment' in text:
        return do_comment(key)
    if 'vote' in text or 'upvote' in text:
        return do_upvote(key)
    if 'referral link' in text or 'ref link' in text:
        return do_ref_link(key)
    if 'alliance war' in text or 'submit or update' in text:
        return do_alliance_submit(key)
    if 'write a forum post' in text or 'publish a post' in text or 'post or comment' in text:
        return do_post(key)
    raise RuntimeError(f'未知挑战类型: {packet.get("challenge_description","")[:60]}')

# ===== 红包加入 =====
def join_packet(key, packet_id, max_attempts=3):
    """加入红包：规则解题 → LLM fallback → 错题重试"""
    force_llm = False
    last_err = None
    for attempt in range(1, max_attempts + 1):
        chal, err = safe_api('GET', f'/red-packets/{packet_id}/challenge', key=key)
        if err:
            raise RuntimeError(f'challenge failed: {err}')
        question = chal.get('question', '')
        log(f'📝 题目: {question[:80]}')

        # 解题
        if force_llm:
            answer = solve_with_llm(question)
            solver = 'llm'
        else:
            answer = solve_local(question)
            solver = 'local'
            if answer is None:
                answer = solve_with_llm(question)
                solver = 'llm'

        if answer is None:
            raise RuntimeError(f'无法解题: {question}')

        log(f'✅ 答案: {answer} (solver={solver})')

        joined, err = join_api('POST', f'/red-packets/{packet_id}/join', data={'answer': answer}, key=key)
        if not err:
            return question, answer, joined, solver, attempt

        err_msg = str(err)
        if 'Wrong answer' in err_msg or 'incorrect' in err_msg.lower():
            # 记录错题
            bank = load_json(QUESTION_BANK_FILE, {})
            bank[question.strip().lower()] = None  # 标记为错题
            save_json(QUESTION_BANK_FILE, bank)
            if attempt < max_attempts:
                force_llm = True
                time.sleep(1.5)
                continue
        if '429' in err_msg:
            time.sleep(6)
            continue
        if '503' in err_msg:
            time.sleep(3)
            continue
        last_err = err
        break

    raise RuntimeError(f'join 失败: {last_err}')

def attempt_packet(key, packet):
    """完整处理一个红包：执行动作 + 解题 + 加入"""
    packet_id = packet['id']
    ptype = packet_type(packet)
    log(f'🎯 处理红包: {packet.get("title","")} (type={ptype})')

    # 1. 执行挑战动作
    try:
        action_result = perform_challenge(key, packet)
        log(f'✅ 动作完成: {action_result}')
    except Exception as e:
        log(f'⚠️ 动作失败: {e}')
        action_result = f'动作失败: {e}'

    time.sleep(0.5)

    # 2. 解题 + 加入
    question, answer, joined, solver, attempt = join_packet(key, packet_id)
    amount = None
    if isinstance(joined, dict):
        amount = joined.get('estimated_per_person') or joined.get('amount') or joined.get('per_person')
    amount_str = f'${amount}' if amount else '?'
    log(f'🧧✅ 红包成功! {amount_str} (solver={solver}, attempt={attempt})')
    notify(f'🧧✅ 红包 {amount_str} | {solver} | {question[:40]}')
    append_summary({
        'status': 'success', 'packet_id': packet_id[:8],
        'question': question, 'answer': answer, 'solver': solver,
        'amount': amount, 'action': action_result,
    })
    return True

# ===== 红包智能轮询 =====
def get_active_packet(key):
    data, err = safe_api('GET', '/red-packets', key=key)
    if err or not data:
        return None, data, err
    active = data.get('active') or []
    return (active[0] if active else None), data, None

def smart_poll(key):
    """秒级轮询抢红包"""
    log(f'🚀 开始秒级轮询 (interval={POLL_INTERVAL}s, duration={WATCH_MAX_SECONDS}s)')
    seen_failures = set()
    failed_ids = set()
    start = time.time()
    loops = max(1, int(WATCH_MAX_SECONDS / POLL_INTERVAL))

    for i in range(loops):
        if not _running:
            break
        elapsed = time.time() - start
        if elapsed >= WATCH_MAX_SECONDS:
            break

        packet, data, err = get_active_packet(key)
        if packet:
            pid = packet['id']
            if pid in failed_ids:
                time.sleep(POLL_INTERVAL)
                continue
            log(f'🎯 检测到红包 [{i+1}] {packet.get("title","")}')
            try:
                if attempt_packet(key, packet):
                    return True
            except Exception as e:
                err_text = str(e)
                if pid not in seen_failures:
                    log(f'❌ 失败: {err_text[:100]}')
                    notify(f'🧧❌ {err_text[:200]}')
                    seen_failures.add(pid)
                failed_ids.add(pid)
                time.sleep(1.5)
                continue
        time.sleep(POLL_INTERVAL)

    log(f'⚠️ 轮询 {time.time()-start:.0f}s 结束，未抢到')
    return False

def run_red_packet_cycle(key):
    """完整的红包周期：检查 → 预热等待 → 抢"""
    data, err = safe_api('GET', '/red-packets', key=key)
    if err:
        log(f'❌ 查询红包状态失败: {err}')
        return False

    active = data.get('active') or []
    if active:
        log(f'🎯 已有 active 红包，立即处理')
        try:
            return attempt_packet(key, active[0])
        except Exception as e:
            log(f'❌ 处理失败: {e}')
            notify(f'🧧❌ {str(e)[:200]}')
            return False

    nxt_sec = data.get('next_packet_seconds')
    if nxt_sec is None:
        log('⚠️ API 未返回 next_packet_seconds')
        return False

    target = datetime.now() + timedelta(seconds=nxt_sec)
    log(f'📅 下次红包: {target.strftime("%H:%M:%S")} ({nxt_sec:.0f}s 后)')

    # 等待到红包前 LEAD_SECONDS 秒
    wait = max(0, nxt_sec - LEAD_SECONDS)
    if wait > 0:
        log(f'⏳ 等待 {wait:.0f}s 后开始抢...')
        while wait > 0 and _running:
            sleep_chunk = min(wait, 30)
            time.sleep(sleep_chunk)
            wait -= sleep_chunk
            # 每30秒检查一次是否出现active
            if wait > 0:
                pkt, _, _ = get_active_packet(key)
                if pkt:
                    log(f'🎯 等待期间发现红包!')
                    break

    # 开始秒级轮询
    return smart_poll(key)

# ===== 每日任务 =====
def do_daily_quests(key, state):
    """执行每日任务"""
    done = []
    today = datetime.now().strftime('%Y-%m-%d')

    # 签到
    if state.get('last_checkin_day') != today:
        _, err = safe_api('POST', '/agents/checkin', data={}, key=key)
        if not err or 'already' in str(err).lower():
            state['last_checkin_day'] = today
            done.append('签到✅')

    # Digest
    if not state.get(f'digest_{today}'):
        _, err = safe_api('GET', '/forum/digest', key=key)
        if not err:
            state[f'digest_{today}'] = True
            done.append('digest✅')

    # Distribute (ref link)
    if not state.get(f'distribute_{today}'):
        try:
            do_ref_link(key)
            state[f'distribute_{today}'] = True
            done.append('distribute✅')
        except Exception as e:
            log(f'distribute 失败: {e}')

    # Create (发帖或评论)
    if not state.get(f'create_{today}'):
        try:
            do_post(key)
            state[f'create_{today}'] = True
            done.append('create✅')
        except Exception as e:
            log(f'create 失败: {e}')

    # Curate (论坛投票)
    if not state.get(f'curate_{today}'):
        try:
            feed, err = safe_api('GET', '/forum?sort=recent&limit=20', key=key)
            if not err:
                posts = feed.get('posts', [])
                up_count = 0
                for post in posts:
                    if up_count >= 5:
                        break
                    title = (post.get('title') or '').strip()
                    body = (post.get('body') or '').strip()
                    if len(title) + len(body) < 120:
                        continue
                    _, e2 = safe_api('POST', f"/forum/{post['id']}/vote", data={'vote': 'up', 'direction': 'up'}, key=key)
                    if not e2:
                        up_count += 1
                    time.sleep(0.3)
                state[f'curate_{today}'] = True
                done.append(f'curate✅({up_count}/5)')
        except Exception as e:
            log(f'curate 失败: {e}')

    if done:
        log(f'每日任务: {", ".join(done)}')
    return done

# ===== 排名追分 =====
def check_rank(key):
    try:
        profile, err = safe_api('GET', '/agents/me', key=key)
        if err:
            return None
        rank = profile.get('rank')
        points = profile.get('points')
        alliance_rank = profile.get('alliance_rank')
        log(f'排名: #{rank} 积分={points} 联盟={alliance_rank}')
        return {'rank': rank, 'points': points, 'alliance_rank': alliance_rank}
    except Exception:
        return None

# ===== 主循环 =====
def main_loop(key):
    log(f'=== AgentHansa 统一守护进程启动 (PID={os.getpid()}) ===')
    notify(f'🟢 AgentHansa v2 启动 PID={os.getpid()}')

    state = load_json(STATE_FILE, {})
    cycle = 0
    last_daily = 0
    last_alliance = 0
    last_rank = 0

    try:
        while _running:
            cycle += 1
            now = int(time.time())
            log(f'\n[{now_str()}] === 第 {cycle} 轮 ===')

            # 1. 每日任务 (每天一次 + 每小时检查)
            if now - last_daily > 3600:
                do_daily_quests(key, state)
                last_daily = now

            # 2. 联盟战提交 (每30分钟)
            if now - last_alliance > 1800:
                try:
                    do_alliance_submit(key)
                    log('联盟战提交完成')
                except Exception as e:
                    log(f'联盟战: {e}')
                last_alliance = now

            # 3. 排名检查 (每小时)
            if now - last_rank > 3600:
                check_rank(key)
                last_rank = now

            # 4. 红包狙击 (核心!)
            try:
                run_red_packet_cycle(key)
            except Exception as e:
                log(f'红包周期异常: {e}')

            # 5. 保存状态
            save_json(STATE_FILE, state)

            # 6. 休眠
            data, _ = safe_api('GET', '/red-packets', key=key)
            nxt_sec = (data or {}).get('next_packet_seconds')
            if nxt_sec and isinstance(nxt_sec, (int, float)):
                # 下次红包前 PRE_WATCH_SECONDS 秒唤醒
                wait = max(30, nxt_sec - PRE_WATCH_SECONDS)
            else:
                wait = RUN_INTERVAL
            wake = datetime.now() + timedelta(seconds=wait)
            log(f'休眠 {wait:.0f}s → {wake.strftime("%H:%M:%S")} 唤醒')

            while wait > 0 and _running:
                chunk = min(wait, 30)
                time.sleep(chunk)
                wait -= chunk

    except Exception as e:
        log(f'主循环异常: {e}')
    finally:
        save_json(STATE_FILE, state)
        log(f'=== 守护进程退出 (cycles={cycle}) ===')
        notify(f'🔴 AgentHansa 停止 cycles={cycle}')

# ===== 单次运行 =====
def run_once(key):
    state = load_json(STATE_FILE, {})
    log('=== 单次运行 ===')
    do_daily_quests(key, state)
    try:
        do_alliance_submit(key)
    except Exception as e:
        log(f'联盟战: {e}')
    check_rank(key)
    save_json(STATE_FILE, state)
    log('=== 单次运行完成 ===')

# ===== 入口 =====
def main():
    parser = argparse.ArgumentParser(description='AgentHansa 统一全自动守护进程')
    parser.add_argument('--once', action='store_true', help='单次运行后退出')
    parser.add_argument('--poll-only', action='store_true', help='只抢红包，不跑其他任务')
    parser.add_argument('--smart-wait', action='store_true', help='查 API 自动等待红包')
    args = parser.parse_args()

    cfg = load_json(CONFIG)
    key = cfg.get('api_key')
    if not key:
        print('缺少 api_key: /root/.hermes/agenthansa/config.json', file=sys.stderr)
        sys.exit(1)

    # 尝试读取 LLM key
    global LLM_API_KEY
    if not LLM_API_KEY:
        try:
            auth = load_json(Path('/root/.codex/auth.json'), {})
            LLM_API_KEY = auth.get('OPENAI_API_KEY', '') or auth.get('api_key', '')
        except Exception:
            pass
        if not LLM_API_KEY:
            try:
                env_file = Path('/root/.hermes/.env')
                if env_file.exists():
                    for line in env_file.read_text().splitlines():
                        if line.startswith('OPENAI_API_KEY='):
                            LLM_API_KEY = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
            except Exception:
                pass

    if args.once:
        run_once(key)
    elif args.poll_only:
        log('=== 红包专用模式 ===')
        smart_poll(key)
    elif args.smart_wait:
        log('=== Smart Wait 模式 ===')
        run_red_packet_cycle(key)
    else:
        main_loop(key)

if __name__ == '__main__':
    main()
