#!/usr/bin/env python3
"""
V2 Spam词库更新器 — 用公开forum API抓帖子 + 分析官方公告 + 监控文档变化

不再依赖有auth的API端点，直接用 https://agenthansa.com/api/forum
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from key_rotation import llm_generate

CONFIG = Path('/root/.hermes/agenthansa/config.json')
SPAM_FILE = Path('/root/.hermes/agenthansa/memory/spam_patterns.json')
STATE_FILE = Path('/root/.hermes/agenthansa/memory/spam-update-state.json')
STRATEGY_FILE = Path('/root/.hermes/agenthansa/memory/strategy-overrides.json')
DOC_STATE_FILE = Path('/root/.hermes/agenthansa/memory/doc-hash-state.json')
LOG_PREFIX = '[spam-update]'
FORUM_BASE = 'https://agenthansa.com/api'


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'{LOG_PREFIX} {ts} {msg}')


def forum_get(path, params=None):
    """公开forum API — 不需要auth"""
    url = FORUM_BASE + path
    if params:
        url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
    req = urllib.request.Request(url, headers={
        'User-Agent': 'OpenClaw-Xiami/1.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read()), None
    except Exception as e:
        return None, str(e)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'last_post_ids': [], 'last_run': None, 'last_announcement_hashes': {}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def load_spam_patterns():
    if SPAM_FILE.exists():
        return json.loads(SPAM_FILE.read_text())
    return {'words': [], 'phrases': [], 'updated': None}


def save_spam_patterns(data):
    SPAM_FILE.parent.mkdir(parents=True, exist_ok=True)
    SPAM_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_strategy_overrides():
    if STRATEGY_FILE.exists():
        return json.loads(STRATEGY_FILE.read_text())
    return {}


def save_strategy_overrides(data):
    STRATEGY_FILE.parent.mkdir(parents=True, exist_ok=True)
    STRATEGY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def fetch_forum_posts(pages=5, per_page=50):
    """从公开forum API抓取帖子"""
    all_posts = []
    for page in range(1, pages + 1):
        data, err = forum_get('/forum', {'sort': 'recent', 'per_page': per_page, 'page': page})
        if err or not data:
            log(f'Page {page} error: {err}')
            break
        posts = data.get('posts', [])
        all_posts.extend(posts)
        if len(posts) < per_page:
            break
        time.sleep(0.5)
    return all_posts


def fetch_announcements():
    """抓取官方公告全文"""
    data, err = forum_get('/forum', {'sort': 'recent', 'per_page': 50, 'category': 'announcement'})
    if err or not data:
        return []
    announcements = data.get('posts', [])
    # 获取每篇公告的完整内容
    full_announcements = []
    for ann in announcements:
        post_id = ann.get('id', '')
        if post_id:
            full_data, _ = forum_get(f'/forum/{post_id}')
            if full_data:
                full_announcements.append(full_data)
            time.sleep(0.3)
    return full_announcements


def extract_spam_patterns_from_posts(posts):
    """从帖子中提取spam patterns — 基于频率分析"""
    import re
    from collections import Counter

    # 已知的spam模板patterns
    template_indicators = [
        'batch slot', 'variant slot', 'run slot', 'slot ',
        'low-noise', 'contribution report', 'validation note',
        'streak update', 'runbook', 'scope then execute',
        'cycle dispatch', 'memo format', 'execution memo',
        'cooldown mode', 'rolling-window', 'format gate',
        'audit compliance', 'minimal verifiable', 'platform compliance',
        'peer-style verification', 'risk-balanced', 'timing vector',
        'risk-averse', 'net effect', 'evidence-heavy', 'explicit criteria',
        'fast-path', 'on-time submit', 'brief memo', 'daily quest consistency',
        'balanced plus', 'deliberate decisions', 'single retry',
        'insufficient context', 'early-window', 'decision rule',
        'qa stack', 'proof mode', 'operations note', 'merchant lens',
        'readability gate', 'broken structure', 'urgency-first',
        'execution metrics', 'orchestration layer',
    ]

    low_score_posts = [p for p in posts if (p.get('upvotes', 0) - p.get('downvotes', 0)) <= 0]

    # 统计低分帖中的spam patterns
    found_patterns = Counter()
    for post in low_score_posts:
        text = ((post.get('title', '') or '') + ' ' + (post.get('body', '') or '')).lower()
        for pattern in template_indicators:
            if pattern in text:
                found_patterns[pattern] += 1

    # 提取高频短语（bigrams/trigrams）
    all_text = ' '.join(
        ((p.get('title', '') or '') + ' ' + (p.get('body', '') or '')[:300]).lower()
        for p in low_score_posts
    )
    words = re.findall(r'\b[a-z]{3,}\b', all_text)
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]

    # 只保留出现3+次的
    freq_bigrams = {k: v for k, v in Counter(bigrams).items() if v >= 3}
    freq_trigrams = {k: v for k, v in Counter(trigrams).items() if v >= 2}

    return {
        'template_patterns': dict(found_patterns.most_common(30)),
        'freq_bigrams': dict(sorted(freq_bigrams.items(), key=lambda x: -x[1])[:20]),
        'freq_trigrams': dict(sorted(freq_trigrams.items(), key=lambda x: -x[1])[:20]),
    }


def analyze_announcements_with_llm(announcements):
    """用LLM分析官方公告，提取spam规则和新词"""
    if not announcements:
        return None

    # 合并公告内容
    context = '\n\n'.join(
        f"=== {a.get('title', '')} ===\n{(a.get('body', '') or '')[:2000]}"
        for a in announcements[:5]
    )

    prompt = (
        'These are official AgentHansa announcements about spam detection and quality standards.\n'
        'Analyze them and extract:\n'
        '1. New spam detection rules (URL checks, AI grading, ban policies)\n'
        '2. Words/phrases that AI agents should AVOID in submissions\n'
        '3. Quality submission requirements (proof URLs, specificity, etc.)\n\n'
        f'Announcements:\n{context}\n\n'
        'Respond in JSON:\n'
        '{\n'
        '  "new_spam_words": ["word1", "word2"],\n'
        '  "new_spam_phrases": ["phrase1", "phrase2"],\n'
        '  "new_rules": ["rule1", "rule2"],\n'
        '  "quality_requirements": ["req1", "req2"],\n'
        '  "strategy_notes": "key strategic implications"\n'
        '}\n'
        'Focus on actionable rules that affect submission success rate.'
    )

    try:
        result = llm_generate(
            [{'role': 'user', 'content': prompt}],
            max_tokens=600, temperature=0.1, preferred='haiku'
        )
        if not result:
            return None
        result = result.strip()
        if result.startswith('```'):
            result = result.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
        return json.loads(result)
    except Exception as e:
        log(f'LLM analysis error: {e}')
        return None


def main():
    state = load_state()
    last_ids = set(state.get('last_post_ids', []))

    # 1. 抓forum帖子
    log('Fetching forum posts...')
    posts = fetch_forum_posts(pages=5, per_page=50)
    log(f'Got {len(posts)} posts')

    if not posts:
        log('No posts, aborting')
        return

    # 2. 提取spam patterns
    patterns = extract_spam_patterns_from_posts(posts)
    log(f'Template patterns found: {len(patterns["template_patterns"])}')
    log(f'Freq bigrams: {len(patterns["freq_bigrams"])}')
    log(f'Freq trigrams: {len(patterns["freq_trigrams"])}')

    # 3. 抓官方公告
    log('Fetching announcements...')
    announcements = fetch_announcements()
    log(f'Got {len(announcements)} announcements')

    # 4. LLM分析公告
    llm_result = None
    if announcements:
        llm_result = analyze_announcements_with_llm(announcements)
        if llm_result:
            log(f'LLM extracted: {len(llm_result.get("new_spam_words", []))} words, {len(llm_result.get("new_spam_phrases", []))} phrases')

    # 5. 合并到spam_patterns.json
    spam_data = load_spam_patterns()
    existing_words = set(w.lower() for w in spam_data.get('words', []))
    existing_phrases = set(p.lower() for p in spam_data.get('phrases', []))
    added_words = []
    added_phrases = []

    # 从频率分析添加
    for pattern, count in patterns['template_patterns'].items():
        if count >= 2 and pattern.lower() not in existing_words:
            existing_words.add(pattern.lower())
            added_words.append(pattern)

    for phrase, count in {**patterns['freq_bigrams'], **patterns['freq_trigrams']}.items():
        if count >= 3 and phrase.lower() not in existing_phrases:
            existing_phrases.add(phrase.lower())
            added_phrases.append(phrase)

    # 从LLM分析添加
    if llm_result:
        for w in llm_result.get('new_spam_words', []):
            w_lower = w.strip().lower()
            if w_lower and w_lower not in existing_words and len(w_lower) > 2:
                existing_words.add(w_lower)
                added_words.append(w_lower)
        for p in llm_result.get('new_spam_phrases', []):
            p_lower = p.strip().lower()
            if p_lower and p_lower not in existing_phrases and len(p_lower) > 4:
                existing_phrases.add(p_lower)
                added_phrases.append(p_lower)

    # 保存
    spam_data['words'] = sorted(existing_words)
    spam_data['phrases'] = sorted(existing_phrases)
    spam_data['updated'] = datetime.now(timezone.utc).isoformat()
    spam_data['source'] = 'forum_api_v2'
    save_spam_patterns(spam_data)

    # 更新state
    new_ids = [p.get('id', '') for p in posts[:30] if p.get('id')]
    state['last_post_ids'] = new_ids
    state['last_run'] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    if added_words or added_phrases:
        log(f'Added {len(added_words)} words + {len(added_phrases)} phrases')
        notify_msg = (
            f"🛡️ Spam词库更新\n"
            f"+{len(added_words)}词 +{len(added_phrases)}短语\n"
            f"总计: {len(spam_data['words'])}词 {len(spam_data['phrases'])}短语"
        )
        _notify_tg(notify_msg)
    else:
        log('No new patterns to add')

    # 6. 监控文档变化
    monitor_doc_changes()

    # 7. 保存LLM分析的规则到strategy-overrides
    if llm_result and llm_result.get('new_rules'):
        overrides = load_strategy_overrides()
        overrides['announcement_rules'] = llm_result['new_rules']
        overrides['quality_requirements'] = llm_result.get('quality_requirements', [])
        overrides['announcement_update'] = datetime.now(timezone.utc).isoformat()
        save_strategy_overrides(overrides)
        log(f'Saved {len(llm_result["new_rules"])} rules to strategy-overrides')


def monitor_doc_changes():
    """拉取 llms.txt 做diff，发现规则变化就更新spam词库"""
    log('Checking llms.txt for rule changes...')

    docs = {
        'llms_full': 'https://www.agenthansa.com/llms-full.txt',
        'llms': 'https://www.agenthansa.com/llms.txt',
    }

    if DOC_STATE_FILE.exists():
        try:
            old_hashes = json.loads(DOC_STATE_FILE.read_text())
        except Exception:
            old_hashes = {}
    else:
        old_hashes = {}

    new_hashes = {}
    changed_docs = []

    for name, url in docs.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'OpenClaw-Xiami/1.0'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read().decode('utf-8', errors='replace')

            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            new_hashes[name] = content_hash

            old_hash = old_hashes.get(name, '')
            if old_hash and old_hash != content_hash:
                changed_docs.append((name, content))
                log(f'Doc {name} changed! old={old_hash} new={content_hash}')
            elif not old_hash:
                log(f'Doc {name} first seen: {content_hash}')
        except Exception as e:
            log(f'Doc fetch error ({name}): {e}')

    DOC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DOC_STATE_FILE.write_text(json.dumps(new_hashes, indent=2))

    if not changed_docs:
        log('No doc changes detected')
        return

    log(f'{len(changed_docs)} doc(s) changed, analyzing with Haiku...')

    for doc_name, content in changed_docs:
        snippet = content[:8000]
        prompt = (
            'This is the AgentHansa platform documentation (llms-full.txt or llms.txt). '
            'The document was UPDATED since last check.\n\n'
            'Analyze the content and extract:\n'
            '1. Any NEW spam/quality rules or policy changes\n'
            '2. New words or phrases that AI agents should AVOID in submissions\n'
            '3. Any new quality requirements or ban policies\n\n'
            f'Document ({doc_name}):\n{snippet}\n\n'
            'Respond in JSON:\n'
            '{\n'
            '  "has_changes": true/false,\n'
            '  "summary": "what changed",\n'
            '  "new_spam_words": ["word1", "word2"] or [],\n'
            '  "new_rules": ["rule1", "rule2"] or [],\n'
            '  "strategy_notes": "any strategic implications"\n'
            '}\n'
            'Focus on SUBMISSION QUALITY and SPAM DETECTION rules only.'
        )

        try:
            result = llm_generate(
                [{'role': 'user', 'content': prompt}],
                max_tokens=500, temperature=0.1, preferred='haiku'
            )
            if not result:
                continue

            result = result.strip()
            if result.startswith('```'):
                result = result.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
            analysis = json.loads(result)

            if not analysis.get('has_changes'):
                log(f'No significant rule changes in {doc_name}')
                continue

            log(f'{doc_name} changes: {analysis.get("summary", "")}')

            updates = []

            new_spam = analysis.get('new_spam_words', [])
            if new_spam:
                spam_data = load_spam_patterns()
                existing = set(w.lower() for w in spam_data.get('words', []))
                added = []
                for w in new_spam:
                    w_lower = w.strip().lower()
                    if w_lower and w_lower not in existing and len(w_lower) > 2:
                        existing.add(w_lower)
                        added.append(w_lower)

                if added:
                    spam_data['words'] = sorted(existing)
                    spam_data['updated'] = datetime.now(timezone.utc).isoformat()
                    save_spam_patterns(spam_data)
                    updates.append(f"spam_words: +{added}")

            new_rules = analysis.get('new_rules', [])
            if new_rules:
                overrides = load_strategy_overrides()
                overrides['doc_rules'] = new_rules
                overrides['doc_update_time'] = datetime.now(timezone.utc).isoformat()
                save_strategy_overrides(overrides)
                updates.append(f"rules: {len(new_rules)}条")

            if updates:
                notify_msg = (
                    f"📄 文档更新检测\n{doc_name}: {analysis.get('summary', '')}\n"
                    f"调整: {', '.join(updates)}"
                )
                _notify_tg(notify_msg)
                log(f'Doc update applied: {", ".join(updates)}')

        except json.JSONDecodeError:
            log(f'JSON parse failed for doc analysis: {result[:200]}')
        except Exception as e:
            log(f'Doc analysis error: {e}')


def _notify_tg(msg):
    """发送TG通知"""
    import os
    token = os.getenv('TG_BOT_TOKEN', '8604975156:AAEiiua-WKjs0nyt3g3Itjy-eYEBfx-mmGI')
    chat_id = os.getenv('TG_CHAT_ID', '6305628029')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({'chat_id': chat_id, 'text': msg}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'{LOG_PREFIX} FATAL: {e}')
        sys.exit(1)
