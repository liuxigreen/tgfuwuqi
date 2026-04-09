#!/usr/bin/env python3
"""
AgentHansa 红包狙击 - 守护进程模式
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from agenthansa_llm import answer_question_with_cheap_model
from agenthansa_notify import notify_redpacket_summary
from agenthansa_quiz import solve_question_local

CONFIG = Path('/root/.hermes/agenthansa/config.json')
STATE_DIR = Path('/root/.hermes/agenthansa/memory')
STATE_FILE = STATE_DIR / 'sniper-state.json'
LOG_FILE = STATE_DIR / 'sniper.jsonl'
ALLIANCE_SUBMIT_STATE_FILE = STATE_DIR / 'alliance-submit-state.json'
LAST_RUN_JSON = STATE_DIR / 'sniper-last-run.json'
BASE_URL = 'https://www.agenthansa.com/api'
UA = 'OpenClaw-Xiami/1.0'


def now_utc():
    return datetime.now(timezone.utc)


def load_cfg():
    return json.loads(CONFIG.read_text())


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def append_log(obj):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def write_runtime_snapshot(result, active_packets=None):
    payload = {
        'ts': result.get('ts'),
        'mode': result.get('mode') or 'sniper',
        'active_count': int(result.get('active_count') or 0),
        'active_ids': [str((pkt or {}).get('id')) for pkt in (active_packets or []) if (pkt or {}).get('id')],
        'next_packet_at': result.get('next_packet_at'),
        'next_packet_seconds': result.get('next_packet_seconds'),
        'joins': len(result.get('joins') or []),
        'joined_count': sum(1 for item in (result.get('joins') or []) if item.get('joined')),
    }
    LAST_RUN_JSON.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def api_call(api_key, method, path, payload=None, timeout=8):
    url = BASE_URL.rstrip('/') + path
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': UA,
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            try:
                parsed = json.loads(raw) if raw else {}
            except Exception:
                parsed = {'raw': raw}
            return {'ok': True, 'status': resp.getcode(), 'data': parsed}
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', errors='replace')
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {'raw': raw}
        return {'ok': False, 'status': e.code, 'error': parsed}
    except Exception as e:
        return {'ok': False, 'status': 0, 'error': {'message': str(e)}}


def pick_top_offer(offers):
    best = None
    best_score = -1
    for offer in offers:
        payout = (offer or {}).get('payout') or {}
        try:
            score = float(payout.get('amount') or 0)
        except Exception:
            score = 0
        if not (offer or {}).get('is_demo', False):
            score += 0.01
        if score > best_score:
            best_score = score
            best = offer
    return best


def packet_text(packet):
    return ' '.join([
        str((packet or {}).get('challenge_type') or ''),
        str((packet or {}).get('challenge_description') or ''),
        json.dumps((packet or {}).get('how_to_join') or [], ensure_ascii=False),
    ]).lower()


def is_generate_ref_packet(packet):
    text = packet_text(packet)
    return 'generate_ref' in text or 'referral link' in text or '/offers/' in text


def error_requires_fresh_ref(payload):
    blob = json.dumps(payload or {}, ensure_ascii=False).lower()
    triggers = [
        'referral link first',
        'generate a referral link first',
        'within the last 30 minutes',
        'must be within the last 30 minutes',
        'generate_ref',
    ]
    return any(token in blob for token in triggers)


def error_indicates_wrong_answer(payload):
    blob = json.dumps(payload or {}, ensure_ascii=False).lower()
    triggers = ['wrong answer', 'incorrect answer', 'answer is incorrect', 'invalid answer']
    return any(token in blob for token in triggers)


def extract_question_text(payload):
    if not isinstance(payload, dict):
        return None
    for key in ('question', 'mathQuestion', 'challengeQuestion', 'quiz'):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ('data', 'challenge', 'item', 'redPacket'):
        nested = payload.get(key)
        if isinstance(nested, dict):
            value = extract_question_text(nested)
            if value:
                return value
    return None


def is_alliance_submission_packet(packet):
    text = packet_text(packet)
    triggers = [
        'alliance war quest', '/alliance-war/quests',
        'submit or update an alliance war quest', 'resubmitting counts',
    ]
    return any(token in text for token in triggers)


def is_forum_upvote_packet(packet):
    text = packet_text(packet)
    triggers = [
        'upvote a forum post', '/forum/{post_id}/vote',
        '/api/forum/{post_id}/vote', '"vote": "up"', 'forum post first',
    ]
    return any(token in text for token in triggers) and ('forum' in text or '/vote' in text)


def error_requires_alliance_submission(payload):
    blob = json.dumps(payload or {}, ensure_ascii=False).lower()
    triggers = [
        'alliance war quest', '/api/alliance-war/quests', '/alliance-war/quests',
        'submit or update an alliance war quest', 'resubmitting counts', 'challenge not completed',
    ]
    return any(token in blob for token in triggers) and ('alliance' in blob or '/alliance-war/quests' in blob)


def error_requires_forum_upvote(payload):
    blob = json.dumps(payload or {}, ensure_ascii=False).lower()
    triggers = [
        'upvote a forum post first', 'upvote a forum post',
        'must be within the last 30 minutes', 'post /api/forum/{post_id}/vote', '"vote": "up"',
    ]
    return any(token in blob for token in triggers) and ('forum' in blob or '/vote' in blob)


def extract_submission_body(raw_text: str):
    text = (raw_text or '').replace('\r\n', '\n').strip()
    marker = '\n---\n'
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text


def load_alliance_submit_state():
    if not ALLIANCE_SUBMIT_STATE_FILE.exists():
        return {}
    try:
        return json.loads(ALLIANCE_SUBMIT_STATE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def ensure_recent_alliance_submission(api_key, state, force=False, max_age_seconds=25 * 60):
    now_epoch = int(now_utc().timestamp())
    last_epoch = int(state.get('last_alliance_submit_epoch', 0) or 0)
    if not force and last_epoch and now_epoch - last_epoch < max_age_seconds and state.get('last_alliance_submit_qid'):
        return {'ok': True, 'status': 200, 'quest_id': state.get('last_alliance_submit_qid'), 'reused': True}

    quests = api_call(api_key, 'GET', '/alliance-war/quests')
    if not quests['ok']:
        return {'ok': False, 'status': quests['status'], 'error': quests.get('error')}

    open_ids = {
        str((quest or {}).get('id'))
        for quest in ((quests.get('data') or {}).get('quests', []) or [])
        if str((quest or {}).get('status') or '').lower() == 'open' and (quest or {}).get('id')
    }
    submit_state = load_alliance_submit_state()
    submissions = submit_state.get('submissions') if isinstance(submit_state, dict) else {}
    if not isinstance(submissions, dict):
        submissions = {}

    candidates = []
    for qid, item in submissions.items():
        qid = str(qid)
        if qid not in open_ids:
            continue
        local_path = Path((item or {}).get('local_path') or '')
        if not local_path.exists():
            continue
        try:
            body = extract_submission_body(local_path.read_text(encoding='utf-8')).strip()
        except Exception:
            continue
        if not body:
            continue
        candidates.append({'qid': qid, 'title': (item or {}).get('title'), 'submitted_at': (item or {}).get('submitted_at') or '', 'content': body})

    candidates.sort(key=lambda item: item.get('submitted_at') or '', reverse=True)
    if not candidates:
        return {'ok': False, 'status': 0, 'error': 'no_open_prior_alliance_submission'}

    chosen = candidates[0]
    resp = api_call(api_key, 'POST', f"/alliance-war/quests/{chosen['qid']}/submit", payload={'content': chosen['content']})
    out = {'ok': resp['ok'], 'status': resp['status'], 'quest_id': chosen['qid'], 'reused': False}
    if resp['ok']:
        state['last_alliance_submit_epoch'] = now_epoch
        state['last_alliance_submit_qid'] = chosen['qid']
    else:
        out['error'] = resp.get('error')
    return out


def should_mark_attempted_on_join_failure(status, payload):
    if error_requires_fresh_ref(payload) or error_requires_alliance_submission(payload) or error_requires_forum_upvote(payload):
        return False
    try:
        code = int(status or 0)
    except Exception:
        code = 0
    if code in {0, 429, 500, 502, 503, 504}:
        return False
    blob = json.dumps(payload or {}, ensure_ascii=False).lower()
    transient_tokens = ['try again', 'temporarily unavailable', 'timeout', 'rate limit', 'challenge not completed']
    return not any(token in blob for token in transient_tokens)


def ensure_recent_ref_link(api_key, state, force=False, max_age_seconds=25 * 60):
    now_epoch = int(now_utc().timestamp())
    last_epoch = int(state.get('last_ref_epoch', 0) or 0)
    if not force and last_epoch and now_epoch - last_epoch < max_age_seconds and state.get('latest_ref_url'):
        return {'ok': True, 'status': 200, 'url': state.get('latest_ref_url'), 'reused': True}

    offers = api_call(api_key, 'GET', '/offers')
    if not offers['ok']:
        return {'ok': False, 'status': offers['status'], 'error': offers.get('error')}
    top = pick_top_offer((offers.get('data') or {}).get('offers', []))
    if not top:
        return {'ok': False, 'status': 0, 'error': 'no offers available'}
    offer_id = top.get('id')
    ref = api_call(api_key, 'POST', f'/offers/{offer_id}/ref', payload={})
    if ref['ok']:
        state['last_ref_epoch'] = now_epoch
        state['latest_ref_url'] = (ref.get('data') or {}).get('ref_url')
    return {'ok': ref['ok'], 'status': ref['status'], 'offer_id': offer_id,
            'url': (ref.get('data') or {}).get('ref_url') if ref['ok'] else None,
            'error': ref.get('error') if not ref['ok'] else None, 'reused': False}


def build_forum_comment(post):
    title = ((post or {}).get('title') or '').strip()
    if title:
        title = title.replace('\n', ' ').strip()
        if len(title) > 72:
            title = title[:69] + '...'
        return f'Nice angle on "{title}" — concrete posts like this make the platform feel more useful for real agent work.'
    return 'Helpful post — practical examples like this make it easier to see how agents can do real work here.'


def ensure_recent_forum_comment(api_key, state, my_id=None, max_age_seconds=25 * 60):
    now_epoch = int(now_utc().timestamp())
    last_epoch = int(state.get('last_forum_comment_epoch', 0) or 0)
    if last_epoch and now_epoch - last_epoch < max_age_seconds:
        return {'skipped': True, 'reason': 'recent_comment_exists'}

    feed = api_call(api_key, 'GET', '/forum?sort=recent')
    if not feed['ok']:
        return {'ok': False, 'status': feed['status'], 'error': feed.get('error')}

    posts = feed.get('data', {}).get('posts', []) or []
    recent_ids = state.get('recent_forum_comment_post_ids') or []
    if not isinstance(recent_ids, list):
        recent_ids = []
    recent_ids = [str(x) for x in recent_ids if x]
    recent_set = set(recent_ids)

    target = None
    for post in posts:
        pid = post.get('id')
        aid = ((post.get('agent') or {}).get('id'))
        if not pid or (my_id and aid == my_id):
            continue
        if str(pid) not in recent_set:
            target = post
            break

    if not target:
        return {'skipped': True, 'reason': 'no_fresh_comment_target'}

    body = build_forum_comment(target)
    resp = api_call(api_key, 'POST', f"/forum/{target['id']}/comments", payload={'body': body})
    if resp['ok']:
        pid_str = str(target.get('id'))
        updated_ids = [x for x in recent_ids if x != pid_str] + [pid_str]
        state['last_forum_comment_epoch'] = now_epoch
        state['recent_forum_comment_post_ids'] = updated_ids[-20:]
    return {'ok': resp['ok'], 'target_post_id': target.get('id'), 'body': body}


def ensure_recent_forum_vote(api_key, state, my_id=None, direction='up', force=False, max_age_seconds=25 * 60):
    now_epoch = int(now_utc().timestamp())
    state_key_epoch = f'last_forum_{direction}_vote_epoch'
    state_key_post = f'last_forum_{direction}_vote_post_id'
    state_key_recent = f'recent_forum_{direction}_vote_post_ids'
    last_epoch = int(state.get(state_key_epoch, 0) or 0)
    if (not force and last_epoch and now_epoch - last_epoch < max_age_seconds):
        return {'ok': True, 'status': 200, 'direction': direction, 'reused': True}

    feed = api_call(api_key, 'GET', '/forum?sort=recent')
    if not feed['ok']:
        return {'ok': False, 'status': feed['status'], 'error': feed.get('error')}

    posts = feed.get('data', {}).get('posts', []) or []
    recent_ids = state.get(state_key_recent) or []
    if not isinstance(recent_ids, list):
        recent_ids = []
    recent_ids = [str(x) for x in recent_ids if x]
    recent_set = set(recent_ids)

    for post in posts:
        pid = post.get('id')
        aid = ((post.get('agent') or {}).get('id'))
        if not pid or (my_id and aid == my_id):
            continue
        pid_str = str(pid)
        if pid_str in recent_set:
            continue
        resp = api_call(api_key, 'POST', f'/forum/{pid}/vote', payload={'vote': direction, 'direction': direction})
        if resp['ok']:
            updated_ids = [x for x in recent_ids if x != pid_str] + [pid_str]
            state[state_key_epoch] = now_epoch
            state[state_key_post] = pid
            state[state_key_recent] = updated_ids[-20:]
            return {'ok': True, 'status': resp['status'], 'direction': direction, 'target_post_id': pid}
        if int(resp.get('status') or 0) != 409:
            return {'ok': False, 'status': resp['status'], 'error': resp.get('error')}

    return {'ok': False, 'status': 0, 'error': 'no_vote_target_found', 'direction': direction}


def main():
    cfg = load_cfg()
    key = cfg['api_key']
    if not key:
        print('Missing api_key in config.json', file=sys.stderr)
        sys.exit(1)

    run_at = now_utc()
    now_epoch = int(run_at.timestamp())
    state = load_state()

    # 清理过期状态
    attempted = state.get('attempted_red_packets')
    if not isinstance(attempted, dict):
        attempted = {}
    attempted = {str(k): int(v) for k, v in attempted.items() if isinstance(v, (int, float)) and int(v) >= now_epoch - 7 * 24 * 3600}

    retry_after = state.get('packet_retry_after_epoch')
    if not isinstance(retry_after, dict):
        retry_after = {}
    retry_after = {str(k): int(v) for k, v in retry_after.items() if isinstance(v, (int, float)) and int(v) >= now_epoch - 3600}

    pending_failure_notifies = state.get('pending_failure_notifies')
    if not isinstance(pending_failure_notifies, dict):
        pending_failure_notifies = {}
    pending_failure_notifies = {str(k): v for k, v in pending_failure_notifies.items()
        if isinstance(v, dict) and int(v.get('last_seen_epoch', 0) or 0) >= now_epoch - 6 * 3600}

    retry_backoff_seconds = 10

    result = {
        'ts': run_at.isoformat(),
        'mode': 'sniper',
        'active_count': 0,
        'next_packet_at': None,
        'next_packet_seconds': None,
        'joins': [],
        'errors': [],
    }

    # 查红包
    rp = api_call(key, 'GET', '/red-packets')
    if not rp['ok']:
        result['errors'].append({'step': 'red_packets', 'status': rp['status'], 'error': rp.get('error')})
        append_log(result)
        write_runtime_snapshot(result, active_packets=[])
        print(f"ERROR: red_packets status={rp['status']}", file=sys.stderr)
        return

    data = rp.get('data') or {}
    active_packets = data.get('active') or []
    result['active_count'] = len(active_packets)
    result['next_packet_at'] = data.get('next_packet_at')
    result['next_packet_seconds'] = data.get('next_packet_seconds')
    write_runtime_snapshot(result, active_packets=active_packets)

    if not active_packets:
        nxt = result.get('next_packet_at')
        nxt_sec = result.get('next_packet_seconds')
        print(f'NO_REPLY next_at={nxt} in={nxt_sec}s')
        return

    # 拿自己的 ID
    my_id = None
    me = api_call(key, 'GET', '/agents/me')
    if me['ok']:
        my_id = (me.get('data') or {}).get('id')

    # 预热论坛评论
    result['forum_comment_preheat'] = ensure_recent_forum_comment(key, state, my_id=my_id)

    current_active_ids = set()
    for pkt in active_packets:
        pid = pkt.get('id')
        if not pid:
            continue
        pid_key = str(pid)
        current_active_ids.add(pid_key)

        if pid_key in attempted:
            result['joins'].append({'id': pid, 'joined': False, 'reason': 'already_attempted'})
            continue

        next_retry_epoch = int(retry_after.get(pid_key, 0) or 0)
        if next_retry_epoch > now_epoch:
            result['joins'].append({'id': pid, 'joined': False, 'reason': 'retry_backoff_active',
                                    'retry_in_seconds': next_retry_epoch - now_epoch})
            continue

        # 预热
        if is_generate_ref_packet(pkt):
            result.setdefault('ref_prep', {})[pid_key] = ensure_recent_ref_link(key, state)
        if is_alliance_submission_packet(pkt):
            result.setdefault('alliance_prep', {})[pid_key] = ensure_recent_alliance_submission(key, state)
        if is_forum_upvote_packet(pkt):
            result.setdefault('forum_vote_prep', {})[pid_key] = ensure_recent_forum_vote(key, state, my_id=my_id, direction='up')

        # 拿题目
        q = api_call(key, 'GET', f'/red-packets/{pid}/challenge')
        if not q['ok']:
            fallback_question = extract_question_text(pkt) or ''
            if not fallback_question:
                if int(q.get('status') or 0) == 429:
                    retry_after[pid_key] = now_epoch + retry_backoff_seconds
                result['joins'].append({'id': pid, 'joined': False, 'reason': 'challenge_unavailable', 'status': q['status']})
                continue
            question = fallback_question
        else:
            question = extract_question_text((q.get('data') or {})) or extract_question_text(pkt) or ''

        # 解题：本地优先 → 便宜模型
        ans = solve_question_local(question)
        solver_used = 'local'
        if ans is None:
            model_ans, model_meta = answer_question_with_cheap_model(question)
            if model_ans is not None:
                ans = model_ans
                solver_used = f"model:{model_meta.get('provider')}:{model_meta.get('model')}"
            else:
                result['joins'].append({'id': pid, 'joined': False, 'reason': 'question_not_solved'})
                continue

        # 领取
        join = api_call(key, 'POST', f'/red-packets/{pid}/join', payload={'answer': ans})

        # 失败重试：ref link
        retried_ref = False
        if not join['ok'] and error_requires_fresh_ref(join.get('error')):
            refreshed = ensure_recent_ref_link(key, state, force=True)
            result.setdefault('ref_retry', {})[pid_key] = refreshed
            retried_ref = True
            if refreshed.get('ok'):
                q2 = api_call(key, 'GET', f'/red-packets/{pid}/challenge')
                if q2['ok']:
                    question2 = extract_question_text((q2.get('data') or {})) or ''
                    ans2 = solve_question_local(question2)
                    if ans2 is None:
                        model_ans2, _ = answer_question_with_cheap_model(question2)
                        if model_ans2 is not None:
                            ans2 = model_ans2
                    if ans2 is not None:
                        question, ans = question2, ans2
                        join = api_call(key, 'POST', f'/red-packets/{pid}/join', payload={'answer': ans})

        # 失败重试：alliance submission
        retried_alliance = False
        if not join['ok'] and error_requires_alliance_submission(join.get('error')):
            refreshed = ensure_recent_alliance_submission(key, state, force=True)
            result.setdefault('alliance_retry', {})[pid_key] = refreshed
            retried_alliance = True
            if refreshed.get('ok'):
                q3 = api_call(key, 'GET', f'/red-packets/{pid}/challenge')
                if q3['ok']:
                    question3 = extract_question_text((q3.get('data') or {})) or ''
                    ans3 = solve_question_local(question3)
                    if ans3 is None:
                        model_ans3, _ = answer_question_with_cheap_model(question3)
                        if model_ans3 is not None:
                            ans3 = model_ans3
                    if ans3 is not None:
                        question, ans = question3, ans3
                        join = api_call(key, 'POST', f'/red-packets/{pid}/join', payload={'answer': ans})

        # 失败重试：forum vote
        retried_forum = False
        if not join['ok'] and error_requires_forum_upvote(join.get('error')):
            refreshed = ensure_recent_forum_vote(key, state, my_id=my_id, direction='up', force=True)
            result.setdefault('forum_vote_retry', {})[pid_key] = refreshed
            retried_forum = True
            if refreshed.get('ok'):
                q4 = api_call(key, 'GET', f'/red-packets/{pid}/challenge')
                if q4['ok']:
                    question4 = extract_question_text((q4.get('data') or {})) or ''
                    ans4 = solve_question_local(question4)
                    if ans4 is None:
                        model_ans4, _ = answer_question_with_cheap_model(question4)
                        if model_ans4 is not None:
                            ans4 = model_ans4
                    if ans4 is not None:
                        question, ans = question4, ans4
                        join = api_call(key, 'POST', f'/red-packets/{pid}/join', payload={'answer': ans})

        # 失败重试：wrong answer → 换模型
        retried_wrong = False
        if not join['ok'] and error_indicates_wrong_answer(join.get('error')):
            model_ans_retry, _ = answer_question_with_cheap_model(question)
            if model_ans_retry is not None and str(model_ans_retry).strip() != str(ans).strip():
                retried_wrong = True
                ans = model_ans_retry
                join = api_call(key, 'POST', f'/red-packets/{pid}/join', payload={'answer': ans})

        # 记录结果
        if join['ok']:
            retry_after.pop(pid_key, None)
        elif int(join.get('status') or 0) == 429:
            retry_after[pid_key] = now_epoch + retry_backoff_seconds

        entry = {
            'id': pid,
            'joined': join['ok'],
            'status': join['status'],
            'answer': ans,
            'question': question,
            'solver': solver_used,
            'retried_ref': retried_ref,
            'retried_alliance': retried_alliance,
            'retried_forum': retried_forum,
            'retried_wrong': retried_wrong,
        }
        if join['ok']:
            attempted[pid_key] = now_epoch
            pending_failure_notifies.pop(pid_key, None)
            entry['resp'] = join.get('data')
        else:
            entry['resp'] = join.get('error')
            pending_failure_notifies[pid_key] = {'entry': entry, 'last_seen_epoch': now_epoch, 'ts': result['ts']}
            if should_mark_attempted_on_join_failure(join.get('status'), join.get('error')):
                attempted[pid_key] = now_epoch
        result['joins'].append(entry)

    # 清理过期 attempted
    if len(attempted) > 1000:
        attempted = dict(sorted(attempted.items(), key=lambda item: item[1], reverse=True)[:1000])

    # 延迟通知失败的红包
    for stale_pid in list(pending_failure_notifies.keys()):
        if stale_pid in current_active_ids:
            continue
        pending = pending_failure_notifies.get(stale_pid)
        entry = (pending or {}).get('entry') if isinstance(pending, dict) else None
        if not isinstance(entry, dict) or entry.get('joined'):
            pending_failure_notifies.pop(stale_pid, None)
            continue
        try:
            notify_result = notify_redpacket_summary({'ts': result['ts'], 'mode': 'sniper', 'joins': [entry]})
        except Exception as exc:
            notify_result = {'ok': False, 'error': str(exc)}
        if notify_result.get('ok') or notify_result.get('skipped'):
            pending_failure_notifies.pop(stale_pid, None)

    # 保存状态
    state['attempted_red_packets'] = attempted
    state['packet_retry_after_epoch'] = retry_after
    state['pending_failure_notifies'] = pending_failure_notifies
    save_state(state)

    append_log(result)

    # 通知
    try:
        result['notify'] = notify_redpacket_summary(result)
    except Exception as exc:
        result['notify'] = {'ok': False, 'error': str(exc)}

    joined_count = sum(1 for item in result['joins'] if item.get('joined'))
    next_sec = result.get('next_packet_seconds')
    print(f"red_active={result['active_count']} joins={joined_count} attempts={len(result['joins'])}")
    return next_sec, joined_count


def sniper_run():
    """单次运行，供 cron 调用"""
    next_sec, count = main()
    return next_sec, count


def daemon_loop():
    """守护进程模式：抢完休眠，精准唤醒"""
    print("=== Sniper 守护模式启动 ===")
    cycle = 0
    while True:
        try:
            cycle += 1
            now = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{now}] --- 第 {cycle} 轮 ---")

            next_sec, count = main()

            if next_sec is not None:
                next_sec = int(next_sec)
                if next_sec > 120:
                    # 提前 90 秒唤醒：60 秒预热 + 30 秒余量
                    wait = max(next_sec - 90, 60)
                    wake = datetime.now().timestamp() + wait
                    wake_str = datetime.fromtimestamp(wake).strftime('%H:%M:%S')
                    print(f"休眠 {wait}s，下次 {wake_str} 唤醒预热")
                    time.sleep(wait)
                elif next_sec > 0:
                    # 快开了，高频扫
                    print(f"临近窗口 ({next_sec}s)，5 秒后重扫")
                    time.sleep(5)
                else:
                    # 到点了但没 active，快速重试
                    print("压秒探测，3 秒后重试")
                    time.sleep(3)
            else:
                # API 没返回时间，等一会
                print("无时间信息，30 秒后重试")
                time.sleep(30)

        except KeyboardInterrupt:
            print("\n用户中断，退出")
            break
        except Exception as e:
            print(f"循环异常: {e}")
            time.sleep(60)


if __name__ == '__main__':
    if '--daemon' in sys.argv:
        daemon_loop()
    else:
        sniper_run()
