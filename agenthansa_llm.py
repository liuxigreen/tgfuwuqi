#!/usr/bin/env python3
"""便宜模型解题 - Edgefn DeepSeek 免费优先，OpenRouter 兜底"""
import json
import os
from pathlib import Path

from openai import OpenAI

OPENCLAW_CONFIG = Path('/root/.openclaw/openclaw.json')


def get_llm_clients():
    """返回可用的 LLM 客户端列表，按优先级：免费 Edgefn → openrouter"""
    clients = []
    try:
        cfg = json.loads(OPENCLAW_CONFIG.read_text())
        for name in ['edgefn', 'edgefn3', 'edgefn4', 'openrouter']:
            provider = cfg.get('models', {}).get('providers', {}).get(name, {})
            base_url = provider.get('baseUrl')
            api_key = provider.get('apiKey')
            if base_url and api_key:
                clients.append((name, OpenAI(base_url=base_url, api_key=api_key)))
    except Exception:
        pass
    return clients


def answer_question_with_cheap_model(question: str):
    """用便宜模型答题，返回 (answer, meta) 或 (None, error_meta)"""
    clients = get_llm_clients()
    if not clients:
        return None, {'error': 'no_llm_clients'}

    for name, client in clients:
        model = 'DeepSeek-V3.2' if 'edgefn' in name else 'gpt-5.4'
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'Answer with ONLY the number. No explanation, no units, no punctuation. Just the number.'},
                    {'role': 'user', 'content': question},
                ],
                max_tokens=20,
                temperature=0.0,
            )
            answer = resp.choices[0].message.content.strip()
            # 提取纯数字
            import re
            nums = re.findall(r'-?\d+\.?\d*', answer)
            if nums:
                return nums[0], {'provider': name, 'model': model, 'endpoint': 'chat'}
            return answer, {'provider': name, 'model': model, 'endpoint': 'chat'}
        except Exception as e:
            continue

    return None, {'error': 'all_providers_failed'}
