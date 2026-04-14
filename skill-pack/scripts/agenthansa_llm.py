#!/usr/bin/env python3
"""便宜模型解题 — Haiku免费优先，Sonnet兜底"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from key_rotation import llm_generate


def answer_question_with_cheap_model(question: str):
    """用便宜模型答题，返回 (answer, meta) 或 (None, error_meta)

    优先级: Haiku(免费快) → Sonnet(免费) → GPT-5.4(付费)
    """
    system_msg = 'Answer with ONLY the number. No explanation, no units, no punctuation. Just the number.'
    messages = [
        {'role': 'system', 'content': system_msg},
        {'role': 'user', 'content': question},
    ]

    # 优先 Haiku（免费+快）
    for provider, label in [('haiku', 'haiku'), ('sonnet', 'sonnet'), ('bankofai', 'gpt-5.4')]:
        try:
            answer = llm_generate(messages, max_tokens=20, temperature=0.0, preferred=provider)
            if answer:
                answer = answer.strip()
                nums = re.findall(r'-?\d+\.?\d*', answer)
                if nums:
                    return nums[0], {'provider': label, 'model': provider}
                return answer, {'provider': label, 'model': provider}
        except Exception:
            continue

    return None, {'error': 'all_providers_failed'}
