#!/usr/bin/env python3
"""
每日spam词库扩充 — 用Haiku/Sonnet分析平台帖子，提取AI味重的词/句式
每天早上跑一次，追加到 memory/spam_patterns.json
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from key_rotation import llm_generate

SPAM_FILE = Path('/root/.hermes/agenthansa/memory/spam_patterns.json')
CONFIG = Path('/root/.hermes/agenthansa/config.json')
BASE = 'https://www.agenthansa.com/api'
UA = 'OpenClaw-Xiami/1.0'


def load_spam():
    if SPAM_FILE.exists():
        try:
            return json.loads(SPAM_FILE.read_text())
        except Exception:
            pass
    return {'words': [], 'phrases': [], 'updated': '', 'source': ''}


def save_spam(data):
    SPAM_FILE.parent.mkdir(parents=True, exist_ok=True)
    data['updated'] = datetime.now().strftime('%Y-%m-%d')
    SPAM_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def api_get(path, key):
    url = BASE + path
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {key}',
        'Accept': 'application/json',
        'User-Agent': UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f'API error: {e}')
        return None


def fetch_forum_posts(key, limit=30):
    """拉取最近的论坛帖子"""
    data = api_get(f'/forum?sort=recent&limit={limit}', key)
    if not data:
        return []
    posts = data.get('posts') or []
    # 只要正文
    return [p.get('body', '')[:500] for p in posts if len(p.get('body', '')) > 50]


def expand_spam_words(posts_text, existing_words):
    """用Haiku分析帖子，提取AI味重的词/句式"""
    sample = '\n---\n'.join(posts_text[:20])
    existing = ', '.join(existing_words[:30])

    prompt = (
        'You are a content quality analyst. Analyze these forum posts and identify '
        'words, phrases, and sentence patterns that sound AI-generated or overly generic.\n\n'
        f'Existing spam words already detected: {existing}\n\n'
        f'Forum posts:\n{sample}\n\n'
        'Task: List NEW (not in existing list) AI-sounding words and phrases.\n'
        'Output format: one word/phrase per line, no numbering, no explanation.\n'
        'Only output words that would help detect AI-generated content.\n'
        'Focus on: overused adjectives, generic transitions, formulaic openings.\n'
        'Max 15 items.'
    )

    try:
        result = llm_generate(
            [{'role': 'user', 'content': prompt}],
            max_tokens=300,
            temperature=0.3,
            preferred='sonnet'  # Sonnet更擅长分析
        )
        if not result:
            # 降级到Haiku
            result = llm_generate(
                [{'role': 'user', 'content': prompt}],
                max_tokens=300,
                temperature=0.3,
                preferred='haiku'
            )
        if not result:
            return []

        # 解析输出
        items = []
        for line in result.strip().split('\n'):
            line = line.strip().strip('-').strip('*').strip()
            if line and len(line) > 2 and len(line) < 80:
                items.append(line.lower())
        return items[:15]
    except Exception as e:
        print(f'LLM error: {e}')
        return []


def main():
    cfg = json.loads(CONFIG.read_text())
    key = cfg.get('api_key')
    if not key:
        print('No api_key in config.json')
        sys.exit(1)

    spam_data = load_spam()
    existing = set(spam_data.get('words', []) + spam_data.get('phrases', []))

    # 检查今天是否已经跑过
    today = datetime.now().strftime('%Y-%m-%d')
    if spam_data.get('updated') == today and spam_data.get('source') == 'daily_expansion':
        print(f'今天已经扩充过了 ({today})')
        return

    print(f'拉取论坛帖子...')
    posts = fetch_forum_posts(key, limit=30)
    if not posts:
        print('没有拉到帖子，跳过')
        return

    print(f'拉到 {len(posts)} 个帖子，用LLM分析...')
    new_items = expand_spam_words(posts, list(existing))

    if not new_items:
        print('没有发现新的spam词')
        return

    # 去重追加
    added = 0
    for item in new_items:
        if item not in existing:
            if len(item.split()) > 2:
                spam_data.setdefault('phrases', []).append(item)
            else:
                spam_data.setdefault('words', []).append(item)
            existing.add(item)
            added += 1

    spam_data['source'] = 'daily_expansion'
    save_spam(spam_data)
    print(f'扩充完成: 新增 {added} 个spam词/句式，总计 {len(spam_data.get(\"words\", []))} 词 + {len(spam_data.get(\"phrases\", []))} 句式')


if __name__ == '__main__':
    main()
