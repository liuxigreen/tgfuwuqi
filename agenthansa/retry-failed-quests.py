#!/usr/bin/env python3
"""
V5 历史任务重试 — 检查submission-history.jsonl中的失败任务

策略:
1. 加载最近7天的失败/spam记录
2. 对每个失败quest:
   - 冷却期: spam失败=24h, 普通失败=6h
   - 冷却过后重新提交（新内容+新人格）
   - 同quest最多重试2次
3. 检查quest是否仍open（已结束的不重试）
4. 跳过需要proof_url的quest
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

HISTORY_FILE = Path('/root/.hermes/agenthansa/memory/submission-history.jsonl')
RETRY_STATE = Path('/root/.hermes/agenthansa/memory/retry-state.json')
CONFIG = Path('/root/.hermes/agenthansa/config.json')
BASE = 'https://www.agenthansa.com/api'
LOG_PREFIX = '[retry]'
MAX_RETRIES_PER_QUEST = 2
SPAM_COOLDOWN_HOURS = 24
FAIL_COOLDOWN_HOURS = 6


def log(msg):
    print(f"{LOG_PREFIX} {msg}")


def notify(msg):
    """发送TG通知"""
    try:
        token = '8604975156:AAEiiua-WKjs0nyt3g3Itjy-eYEBfx-mmGI'
        chat_id = '6305628029'
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({'chat_id': chat_id, 'text': msg}).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def load_config():
    try:
        return json.loads(CONFIG.read_text())
    except Exception:
        return {}


def load_history(days=7):
    """加载最近N天的提交历史"""
    if not HISTORY_FILE.exists():
        return []
    cutoff = int(time.time()) - days * 86400
    entries = []
    for line in HISTORY_FILE.read_text().splitlines():
        try:
            entry = json.loads(line)
            if entry.get('ts', 0) >= cutoff:
                entries.append(entry)
        except Exception:
            pass
    return entries


def load_retry_state():
    if RETRY_STATE.exists():
        try:
            return json.loads(RETRY_STATE.read_text())
        except Exception:
            pass
    return {'retried': {}}


def save_retry_state(state):
    RETRY_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def safe_req(path, method='GET', data=None, key=None, params=None):
    """简易API请求"""
    url = f"{BASE}{path}"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'OpenClaw-Xiami/1.0',
    }
    if key:
        headers['Authorization'] = f'Bearer {key}'

    body = json.dumps(data).encode() if data else None
    if params:
        qs = '&'.join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')[:500]
        return None, f"HTTP {e.code}: {body}"
    except Exception as e:
        return None, str(e)[:200]


def check_quest_open(quest_id, key):
    """检查quest是否仍open"""
    resp, err = safe_req(f'/alliance-war/quests/{quest_id}', key=key)
    if err or not resp:
        return False
    status = str(resp.get('status', '')).lower()
    return status == 'open'


def get_failed_quests(history, retry_state):
    """筛选可重试的失败任务"""
    now = int(time.time())
    retried = retry_state.get('retried', {})
    candidates = []

    for entry in history:
        if entry.get('status') != 'failed':
            continue

        quest_id = entry.get('quest_id')
        if not quest_id:
            continue

        # 检查重试次数
        retry_count = retried.get(str(quest_id), 0)
        if retry_count >= MAX_RETRIES_PER_QUEST:
            continue

        # 检查冷却期
        ts = entry.get('ts', 0)
        err = str(entry.get('error', '')).lower()
        is_spam = 'spam' in err or '429' in err or 'paused' in err or 'velocity' in err
        # 400 不算spam（通常是内容/格式问题），冷却更短
        is_400 = '400' in err and not is_spam

        if is_spam:
            cooldown = SPAM_COOLDOWN_HOURS * 3600
        elif is_400:
            cooldown = FAIL_COOLDOWN_HOURS * 3600  # 400 = 6h冷却（不是spam）
        else:
            cooldown = FAIL_COOLDOWN_HOURS * 3600

        elapsed = now - ts
        if elapsed < cooldown:
            remaining_hours = (cooldown - elapsed) / 3600
            log(f"Quest {quest_id} 冷却中，还需{remaining_hours:.1f}h")
            continue

        candidates.append({
            'quest_id': quest_id,
            'title': entry.get('title', 'Unknown'),
            'reward_usdc': entry.get('reward_usdc', 0),
            'original_error': entry.get('error', ''),
            'retry_count': retry_count,
            'is_spam': is_spam,
        })

    return candidates


def retry_quest(candidate, key):
    """重试一个失败的quest — 用新内容+新人格"""
    import sys
    import importlib.util

    # 动态加载agenthansa-auto.py（文件名有连字符不能直接import）
    spec = importlib.util.spec_from_file_location(
        "agenthansa_auto_mod",
        str(Path(__file__).parent / "agenthansa-auto.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    build_submission_content = mod.build_submission_content
    _get_personality = mod._get_personality
    _save_submission_history = mod._save_submission_history
    manual_reason = mod.manual_reason

    quest_id = candidate['quest_id']
    title = candidate['title']
    log(f"重试 quest {quest_id}: {title[:40]}")

    # 先检查quest是否仍open
    if not check_quest_open(quest_id, key):
        log(f"  → quest已结束，跳过")
        return False

    # 拉取quest详情
    resp, err = safe_req(f'/alliance-war/quests/{quest_id}', key=key)
    if err or not resp:
        log(f"  → 拉取详情失败: {err}")
        return False

    quest = resp
    if str(quest.get('status', '')).lower() != 'open':
        log(f"  → quest状态非open，跳过")
        return False

    # 检查是否需要proof
    mr = manual_reason(quest)
    if mr and 'proof' in mr.lower():
        log(f"  → 需要proof_url，跳过")
        return False

    # 用新人格生成新内容
    persona_key, persona = _get_personality()
    log(f"  → 人格: {persona['name']} ({persona_key})")
    content = build_submission_content(quest, persona_key=persona_key, persona=persona)

    if not content:
        log(f"  → LLM生成失败，跳过")
        return False

    words = len(content.split())
    if words < 80 or words > 200:
        log(f"  → 字数{words}不合规，跳过")
        return False

    # 提交
    payload = {'content': content}
    time.sleep(60)  # 重试前额外等60s

    res, err = safe_req(f"/alliance-war/quests/{quest_id}/submit", method='POST', data=payload, key=key)

    # 记录历史
    hist_entry = {
        'ts': int(time.time()),
        'quest_id': quest_id,
        'title': title,
        'reward_usdc': candidate.get('reward_usdc', 0),
        'words': words,
        'personality': persona_key,
        'retry': True,
        'retry_count': candidate['retry_count'] + 1,
        'error': None,
        'status': 'submitted',
    }

    if err or not res:
        hist_entry['error'] = str(err or 'submit failed')[:200]
        hist_entry['status'] = 'failed'
        _save_submission_history(hist_entry)
        log(f"  → 重试失败: {(err or 'submit failed')[:100]}")
        return False

    hist_entry['submission_id'] = res.get('submission_id')
    _save_submission_history(hist_entry)
    log(f"  → 重试成功! submission_id={res.get('submission_id')}")
    return True


def main():
    config = load_config()
    key = config.get('api_key') or config.get('key')
    if not key:
        log("无API key，跳过")
        return

    history = load_history(days=7)
    retry_state = load_retry_state()
    candidates = get_failed_quests(history, retry_state)

    if not candidates:
        log("无可重试的失败任务")
        return

    log(f"发现 {len(candidates)} 个可重试任务")
    success_count = 0

    for c in candidates:
        ok = retry_quest(c, key)
        if ok:
            success_count += 1
            # 更新重试计数
            qid = str(c['quest_id'])
            retry_state['retried'][qid] = retry_state['retried'].get(qid, 0) + 1
            save_retry_state(retry_state)

    if success_count > 0:
        notify(f"🔄 历史重试: {success_count}/{len(candidates)} 成功")

    log(f"重试完成: {success_count}/{len(candidates)} 成功")


if __name__ == '__main__':
    main()
