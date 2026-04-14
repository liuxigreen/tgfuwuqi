"""共享pipeline模块 — hansa.py和auto.py共用"""
import json, os, re, time
import requests as _req

# edgefn 白山智算
EDGEFN_KEYS = [
    'sk-d9HegwL45b05NO8T213044532eFb44Ed9cDa1bBc0a99642c',
    'sk-SJkqKrOgv5Y7pMgM6446A175BaA94d5e9d9aE98254071c1c',
    'sk-6yqUgrc9huvai9ro06C52b72E8A047E6A0862276D9D5Cb44',
    'sk-lSYVsk8SlwQdVkTq329463329e5b4eD38e1f9e8aB092959d',
    'sk-oLe1ZuIAWYFMyPGu4cE03b13E8414a9b8367228b7cF4E551',
    'sk-lV15J4XYsTc6MrnpC1D531Ea34D34b3dAbD2B7BbF98cC73d',
    'sk-Myb3zl4t77fZTEtl8b4955E8F2D24434A215Da0aB77830D8',
    'sk-5oZMMw7DANSn5SaeDd829cFbC1474dC284D099B3F71c544a',
    'sk-9hAGV7P9YIKZi24U972778Ca4eE241808823Dd5256807e98',
]
EDGEFN_BASE = 'https://api.edgefn.net/v1/chat/completions'
_edgefn_key_idx = 0
_last_edgefn_call = 0.0

# bankofai + sonnet (从 env 加载)
_BANKOFAI_KEYS = []
_BANKOFAI_BASE = 'https://api.bankofai.io/v1'
_SONNET_BASE = ''
_SONNET_KEY = ''
_SONNET_MODEL = ''
_loaded = False

def _load_env():
    global _loaded, _BANKOFAI_KEYS, _BANKOFAI_BASE, _SONNET_BASE, _SONNET_KEY, _SONNET_MODEL
    if _loaded:
        return
    env_path = os.path.join(os.path.dirname(__file__), '.env.agenthansa')
    if not os.path.exists(env_path):
        env_path = os.path.expanduser('~/.hermes/agenthansa/.env.agenthansa')
    env = {}
    try:
        with open(env_path) as f:
            for line in f:
                s = line.strip()
                if '=' in s and not s.startswith('#'):
                    k, v = s.split('=', 1)
                    env[k] = v
    except Exception:
        pass
    raw = env.get('BANKOFAI_API_KEYS', '')
    _BANKOFAI_KEYS = [k.strip() for k in raw.replace('\\n', ',').split(',') if k.strip()]
    _BANKOFAI_BASE = env.get('BANKOFAI_BASE', 'https://api.bankofai.io/v1')
    _SONNET_BASE = env.get('FREE_SONNET_BASE', '')
    _SONNET_KEY = env.get('FREE_SONNET_KEY', '')
    _SONNET_MODEL = env.get('FREE_SONNET_MODEL', 'claude-sonnet-4-5-20250929')
    _loaded = True


def _log(msg):
    try:
        log_path = os.path.join(os.path.dirname(__file__), 'logs', 'hansa-daemon.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f'[{time.strftime("%H:%M:%S")}] [pipeline] {msg}\n')
    except Exception:
        pass


def _edgefn_call(model, messages, max_tokens=1500, temperature=0.5):
    global _edgefn_key_idx, _last_edgefn_call
    elapsed = time.time() - _last_edgefn_call
    if elapsed < 8.0:
        time.sleep(8.0 - elapsed)
    for attempt in range(len(EDGEFN_KEYS)):
        key = EDGEFN_KEYS[_edgefn_key_idx % len(EDGEFN_KEYS)]
        try:
            r = _req.post(EDGEFN_BASE,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
                timeout=120)
            _last_edgefn_call = time.time()
            if r.status_code == 200:
                resp = r.json()
                msg = resp["choices"][0]["message"]
                content = (msg.get("content") or "").strip()
                reasoning = (msg.get("reasoning_content") or "").strip()
                tokens = resp["usage"]["total_tokens"]
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                return content, reasoning, tokens
            elif r.status_code in (403, 429):
                _log(f'edgefn key{_edgefn_key_idx} {r.status_code}, rotating')
                _edgefn_key_idx += 1
                time.sleep(2)
                continue
            else:
                _log(f'edgefn {model} HTTP {r.status_code}')
                return None, None, 0
        except Exception as e:
            _log(f'edgefn key{_edgefn_key_idx} error: {e}')
            _edgefn_key_idx += 1
            time.sleep(2)
            continue
    return None, None, 0


def _llm_generate(messages, max_tokens=600, temperature=0.5, preferred='sonnet'):
    _load_env()
    if preferred == 'sonnet' and _SONNET_BASE and _SONNET_KEY:
        r = _req.post(f"{_SONNET_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {_SONNET_KEY}", "Content-Type": "application/json"},
            json={"model": _SONNET_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
            timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    if preferred == 'bankofai' and _BANKOFAI_KEYS:
        for ki in range(len(_BANKOFAI_KEYS)):
            try:
                r = _req.post(f"{_BANKOFAI_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {_BANKOFAI_KEYS[ki]}", "Content-Type": "application/json"},
                    json={"model": "gpt-5.4", "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
                    timeout=60)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
                if r.status_code in (403, 429):
                    continue
            except Exception:
                continue
    return None


def _glm_extract(content, reasoning):
    if content and len(content) > 50:
        return content
    if not reasoning:
        return ""
    paras = reasoning.split('\n\n')
    candidates = [p.strip() for p in paras
                  if len(p.strip()) > 80
                  and not p.strip().startswith(('1.', '2.', '3.', '4.', '5.', '**', '* ', '*The', '*I ', 'The user'))]
    return candidates[-1] if candidates else ""


def _pipeline_a_fast(quest_context):
    """Sonnet全包 (~13s, 7分)"""
    prompt = (
        f'Write an AgentHansa quest submission in English.\n'
        f'Quest context:\n{quest_context}\n\n'
        'Requirements: concrete, human-sounding, 120-180 words.'
    )
    draft = _llm_generate([{'role': 'user', 'content': prompt}], max_tokens=420, temperature=0.7, preferred='sonnet')
    if not draft or len(draft.split()) < 40:
        return None
    reviewed = _llm_generate(
        [{'role': 'user', 'content': f'Polish this post. Remove AI language. Output ONLY the post:\n\n{draft}'}],
        max_tokens=420, temperature=0.3, preferred='sonnet')
    return reviewed if reviewed and len(reviewed.split()) >= 40 else draft


def _pipeline_b_standard(quest_context):
    """MiniMax写→Sonnet改 (~23s, 8分)"""
    prompt = (
        f'Write an AgentHansa quest submission in English.\n'
        f'Quest context:\n{quest_context}\n\n'
        'Requirements: concrete, useful, human-sounding, not generic, 120-180 words.'
    )
    draft, _, _ = _edgefn_call("MiniMax-M2.5", [
        {"role": "system", "content": "Write a forum post. Output ONLY the post text."},
        {"role": "user", "content": prompt}
    ])
    if not draft or len(draft.split()) < 40:
        return None
    draft = re.sub(r'<think>.*?</think>', '', draft, flags=re.DOTALL).strip()
    final = _llm_generate(
        [{'role': 'user', 'content': f'Polish this to be sharper and more natural. Remove AI language. Output ONLY the post, 120-180 words:\n\n{draft}'}],
        max_tokens=420, temperature=0.5, preferred='sonnet')
    return final if final and len(final.split()) >= 40 else draft


def _pipeline_b_plus(quest_context):
    """DeepSeek→GLM→MiniMax→Sonnet+GPT审 (~80s, 8.5分)"""
    prompt = (
        f'Write an AgentHansa quest submission in English.\n'
        f'Quest context:\n{quest_context}\n\n'
        'Requirements: concrete, opinionated, specific numbers, 200-250 words.'
    )
    d1, _, _ = _edgefn_call("DeepSeek-V3.2", [
        {"role": "system", "content": "Write a forum post. Output ONLY the post."},
        {"role": "user", "content": prompt}
    ], max_tokens=2000)
    if not d1 or len(d1.split()) < 40:
        return None
    d2_raw, d2_reason, _ = _edgefn_call("GLM-5", [
        {"role": "system", "content": "Review and rewrite to improve. Output ONLY the post."},
        {"role": "user", "content": d1}
    ], max_tokens=4000)
    d2 = _glm_extract(d2_raw, d2_reason) if d2_raw or d2_reason else ""
    use_text = d2 if d2 and len(d2.split()) >= 30 else d1
    d3, _, _ = _edgefn_call("MiniMax-M2.5", [
        {"role": "system", "content": "Rewrite to be more natural and engaging. Output ONLY the post."},
        {"role": "user", "content": use_text}
    ], max_tokens=2000)
    if d3:
        d3 = re.sub(r'<think>.*?</think>', '', d3, flags=re.DOTALL).strip()
    use_text = d3 if d3 and len(d3.split()) >= 30 else use_text
    try:
        reviewed = _llm_generate(
            [{'role': 'user', 'content': 'Review this submission. Score 1-10 then rewrite. Format: SCORE:X/10 then post.\n\n' + use_text}],
            max_tokens=500, temperature=0.3, preferred='bankofai')
        if reviewed:
            lines = reviewed.split('\n')
            post = '\n'.join(l for l in lines if 'SCORE' not in l.upper()).strip()
            if post and len(post.split()) >= 40:
                use_text = post
    except Exception as e:
        _log(f'GPT-5.4 review fail: {e}')
    final = _llm_generate(
        [{'role': 'user', 'content': f'Final polish. Remove AI phrases. Output ONLY the post:\n\n{use_text}'}],
        max_tokens=500, temperature=0.3, preferred='sonnet')
    return final if final and len(final.split()) >= 40 else use_text


def _build_quest_prompt_context(q):
    """从quest dict提取上下文"""
    title = q.get('title', '')
    desc = q.get('description', '')[:500]
    goal = q.get('goal', '')
    reward = q.get('reward_amount', '')
    return f"Title: {title}\nDescription: {desc}\nGoal: {goal}\nReward: ${reward}"


def _quest_text(q):
    return (q.get('title', '') + ' ' + q.get('description', '')).lower()


def build_submission_content(q_or_title):
    """V4.1 三级流水线入口

    $0-19:  Pipeline A (Sonnet全包 ~13s, 快)
    $20-49: Pipeline B (MiniMax→Sonnet ~23s)
    $50+:   Pipeline B+ (DeepSeek→GLM→MiniMax→GPT审→Sonnet ~80s)
    降级链: B+失败→B→A→None
    """
    title = q_or_title.get('title', '') if isinstance(q_or_title, dict) else str(q_or_title)
    low = _quest_text(q_or_title) if isinstance(q_or_title, dict) else title.lower()

    use_model = any(k in low for k in [
        'feedback', 'review and improve', 'analysis', 'blog', 'faq', 'comparison', 'write',
        'explain', 'describe', 'how', 'technical', 'documentation', 'migration', 'copy',
        'competitor', 'case study', 'strategy'
    ])
    if not use_model:
        return None

    usdc = float(q_or_title.get('reward_amount', '0') or '0') if isinstance(q_or_title, dict) else 0.0
    quest_context = _build_quest_prompt_context(q_or_title) if isinstance(q_or_title, dict) else str(q_or_title)

    # $50+: Pipeline B+ (三模型+GPT审)
    if usdc >= 50:
        try:
            result = _pipeline_b_plus(quest_context)
            if result:
                _log(f'B+ OK: {title[:30]} (${usdc})')
                return result
        except Exception as e:
            _log(f'B+ fail: {title[:30]} | {e}')
        # B+降级到B
        _log(f'fallback B+→B: {title[:30]}')

    # $20-49: Pipeline B (MiniMax→Sonnet)
    if usdc >= 20:
        try:
            result = _pipeline_b_standard(quest_context)
            if result:
                _log(f'B OK: {title[:30]} (${usdc})')
                return result
        except Exception as e:
            _log(f'B fail: {title[:30]} | {e}')
        # B降级到A
        _log(f'fallback B→A: {title[:30]}')

    # $0-19 / 降级: Pipeline A (Sonnet全包，快)
    try:
        result = _pipeline_a_fast(quest_context)
        if result:
            _log(f'A OK: {title[:30]} (${usdc})')
            return result
    except Exception as e:
        _log(f'A fail: {title[:30]} | {e}')

    return None
