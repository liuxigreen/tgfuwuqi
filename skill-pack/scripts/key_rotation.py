#!/usr/bin/env python3
"""
AgentHansa LLM 调用模块
自动检测可用 API key，轮换使用
支持: newapi (Sonnet/Haiku) / bankofai.io (GPT-5.4)
"""
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

# 加载 .env.agenthansa
ENV_FILE = Path("/root/.hermes/agenthansa/.env.agenthansa")
if ENV_FILE.exists():
    for _line in ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if '=' in _line and not _line.startswith('#'):
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

STATE_FILE = Path("/root/.hermes/agenthansa/memory/key-rotation.json")


def _load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _openai_call(base, key, model, messages, max_tokens=400, temperature=0.7):
    """通用 openai-compatible 调用"""
    if not base or not key or not model:
        return None, 0
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    })
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=payload.encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        body = json.loads(r.read().decode())
    text = ((body.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
    tokens = ((body.get("usage") or {}).get("completion_tokens") or 0)
    return text, tokens


# ===== 从环境变量读取配置 =====
def _get_providers():
    """返回可用 provider 列表，按优先级排序"""
    providers = []

    # newapi Sonnet (免费, 主力)
    sonnet_key = os.getenv('FREE_SONNET_KEY', '')
    sonnet_base = os.getenv('FREE_SONNET_BASE', '')
    sonnet_model = os.getenv('FREE_SONNET_MODEL', '')
    if sonnet_key and sonnet_base:
        providers.append({
            'name': 'sonnet',
            'base': sonnet_base,
            'model': sonnet_model or 'claude-sonnet-4-5-20250929',
            'keys': [sonnet_key],
            'type': 'single',
        })

    # newapi Haiku (免费, 快速)
    haiku_key = os.getenv('FREE_HAIKU_KEY', '')
    haiku_base = os.getenv('FREE_HAIKU_BASE', '')
    haiku_model = os.getenv('FREE_HAIKU_MODEL', '')
    if haiku_key and haiku_base:
        providers.append({
            'name': 'haiku',
            'base': haiku_base,
            'model': haiku_model or 'claude-haiku-4-5-20251001',
            'keys': [haiku_key],
            'type': 'single',
        })

    # bankofai.io GPT-5.4 (多 key 轮换)
    bankofai_keys_raw = os.getenv('BANKOFAI_API_KEYS', '')
    bankofai_keys = [k.strip() for k in bankofai_keys_raw.replace('\n', ',').split(',') if k.strip()]
    if bankofai_keys:
        providers.append({
            'name': 'bankofai',
            'base': os.getenv('BANKOFAI_BASE', 'https://api.bankofai.io/v1'),
            'model': os.getenv('BANKOFAI_MODEL', 'gpt-5.4'),
            'keys': bankofai_keys,
            'type': 'multi_key',
        })

    # edgefn (如果配置了)
    edgefn_key = os.getenv('EDGEFN_API_KEY', '')
    if edgefn_key:
        providers.append({
            'name': 'edgefn',
            'base': os.getenv('EDGEFN_BASE', 'https://api.edgefn.net/v1'),
            'model': os.getenv('EDGEFN_MODEL', 'DeepSeek-V3.2'),
            'keys': [edgefn_key],
            'type': 'single',
        })

    return providers


def llm_generate(messages, max_tokens=400, temperature=0.7, preferred=None):
    """
    通用 LLM 调用，自动轮换 key 和 provider
    messages: [{"role": "user", "content": "..."}]
    preferred: 优先使用哪个 provider name
    """
    providers = _get_providers()
    if not providers:
        raise RuntimeError("无可用 LLM provider")

    # 按优先级排序
    if preferred:
        providers.sort(key=lambda p: 0 if p['name'] == preferred else 1)

    last_err = None
    for provider in providers:
        keys = provider['keys']
        for idx, key in enumerate(keys):
            try:
                text, tokens = _openai_call(
                    provider['base'], key, provider['model'],
                    messages, max_tokens, temperature
                )
                if text:
                    return text
            except urllib.error.HTTPError as e:
                last_err = e
                try:
                    body = e.read().decode()[:200]
                except Exception:
                    body = str(e)
                # 认证错误/额度不足 → 跳到下一个 key
                if e.code in (401, 403, 429) or 'quota' in body.lower() or 'balance' in body.lower():
                    continue
                raise
            except Exception as e:
                last_err = e
                continue

    if last_err:
        raise last_err
    raise RuntimeError("所有 LLM provider 调用失败")


# ===== 便捷接口 =====
def sonnet_generate(prompt, max_tokens=400, temperature=0.7):
    """用 Sonnet 生成内容"""
    return llm_generate(
        [{'role': 'user', 'content': prompt}],
        max_tokens=max_tokens, temperature=temperature, preferred='sonnet'
    )


def haiku_generate(prompt, max_tokens=20, temperature=0):
    """用 Haiku 快速生成"""
    return llm_generate(
        [{'role': 'user', 'content': prompt}],
        max_tokens=max_tokens, temperature=temperature, preferred='haiku'
    )


def gpt_generate(prompt, max_tokens=400, temperature=0.7):
    """用 GPT-5.4 生成"""
    return llm_generate(
        [{'role': 'user', 'content': prompt}],
        max_tokens=max_tokens, temperature=temperature, preferred='bankofai'
    )


# ===== 兼容旧接口 =====
def bankofai_chat(messages, max_tokens=400, temperature=0.7):
    return llm_generate(messages, max_tokens, temperature, preferred='bankofai')


def free_sonnet_chat(messages, max_tokens=400, temperature=0.7):
    return llm_generate(messages, max_tokens, temperature, preferred='sonnet')


def free_haiku_chat(messages, max_tokens=400, temperature=0.7):
    return llm_generate(messages, max_tokens, temperature, preferred='haiku')
