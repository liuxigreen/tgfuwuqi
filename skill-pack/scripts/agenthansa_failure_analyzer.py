#!/usr/bin/env python3
"""
AgentHansa 红包失败分析器
- 分析失败原因
- 记录失败模式
- 自动调整策略
- 生成修复建议
"""
import json
import re
from datetime import datetime
from pathlib import Path

STATE_DIR = Path('/root/.hermes/agenthansa/memory')
FAILURE_LOG = STATE_DIR / 'failure-patterns.jsonl'
FAILURE_STATS = STATE_DIR / 'failure-stats.json'

# 失败类型分类
FAILURE_TYPES = {
    'wrong_answer': {
        'pattern': ['wrong answer', 'incorrect answer', 'answer is incorrect', 'invalid answer'],
        'severity': 'medium',
        'auto_fix': True,
        'description': '答案错误',
    },
    'ref_link_required': {
        'pattern': ['referral link first', 'generate a referral link', 'generate_ref', 'within the last 30 minutes'],
        'severity': 'high',
        'auto_fix': True,
        'description': '需要生成referral link',
    },
    'alliance_required': {
        'pattern': ['alliance war quest', '/alliance-war/quests', 'challenge not completed'],
        'severity': 'high',
        'auto_fix': True,
        'description': '需要提交alliance quest',
    },
    'forum_vote_required': {
        'pattern': ['upvote a forum post', '/forum/{post_id}/vote', 'forum post first'],
        'severity': 'high',
        'auto_fix': True,
        'description': '需要投票论坛帖子',
    },
    'question_not_solved': {
        'pattern': ['question_not_solved'],
        'severity': 'high',
        'auto_fix': False,
        'description': '无法解题（本地规则+LLM都失败）',
    },
    'no_offers_available': {
        'pattern': ['no offers available', 'no offers'],
        'severity': 'critical',
        'auto_fix': False,
        'description': '没有可用的offer（平台问题）',
    },
    'api_error': {
        'pattern': ['429', '503', 'rate limit', 'unavailable', 'timeout'],
        'severity': 'medium',
        'auto_fix': True,
        'description': 'API错误或限速',
    },
    'challenge_unavailable': {
        'pattern': ['challenge_unavailable'],
        'severity': 'high',
        'auto_fix': False,
        'description': 'Challenge不可用',
    },
    'already_joined': {
        'pattern': ['already joined', 'already participated', 'already_attempted'],
        'severity': 'low',
        'auto_fix': False,
        'description': '已经参与过',
    },
}

def classify_failure(error_text: str, reason: str = '') -> dict:
    """分类失败原因"""
    text = f"{error_text} {reason}".lower()
    
    for ftype, config in FAILURE_TYPES.items():
        for pattern in config['pattern']:
            if pattern.lower() in text:
                return {
                    'type': ftype,
                    'severity': config['severity'],
                    'auto_fix': config['auto_fix'],
                    'description': config['description'],
                    'matched_pattern': pattern,
                }
    
    return {
        'type': 'unknown',
        'severity': 'high',
        'auto_fix': False,
        'description': f'未知错误: {text[:100]}',
        'matched_pattern': None,
    }


def analyze_failure(entry: dict) -> dict:
    """分析单个失败记录"""
    error = entry.get('resp') or entry.get('error') or ''
    reason = entry.get('reason', '')
    question = entry.get('question', '')
    answer = entry.get('answer', '')
    
    classification = classify_failure(
        json.dumps(error, ensure_ascii=False) if isinstance(error, dict) else str(error),
        reason
    )
    
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'packet_id': entry.get('id'),
        'question': question,
        'answer': answer,
        'failure_type': classification['type'],
        'severity': classification['severity'],
        'auto_fixable': classification['auto_fix'],
        'description': classification['description'],
        'error_detail': error if isinstance(error, str) else json.dumps(error, ensure_ascii=False)[:300],
        'retried': {
            'ref': entry.get('retried_ref', False),
            'alliance': entry.get('retried_alliance', False),
            'forum': entry.get('retried_forum', False),
            'wrong': entry.get('retried_wrong', False),
        }
    }
    
    return analysis


def generate_fix_suggestion(analysis: dict) -> dict:
    """生成修复建议"""
    ftype = analysis['failure_type']
    
    suggestions = {
        'wrong_answer': {
            'action': 'update_solver',
            'description': '答案错误，建议：1) 检查本地规则是否覆盖该题型 2) 增加LLM兜底权重',
            'code_change': '检查 solve_question_local() 是否遗漏该题型',
        },
        'ref_link_required': {
            'action': 'ensure_ref_preheat',
            'description': '需要referral link，确保预热成功',
            'code_change': '检查 ensure_recent_ref_link() 是否正常工作',
        },
        'alliance_required': {
            'action': 'ensure_alliance_preheat',
            'description': '需要alliance quest提交',
            'code_change': '检查 ensure_recent_alliance_submission()',
        },
        'forum_vote_required': {
            'action': 'ensure_forum_preheat',
            'description': '需要论坛投票',
            'code_change': '检查 ensure_recent_forum_vote()',
        },
        'no_offers_available': {
            'action': 'wait_or_skip',
            'description': '平台没有可用offer，无法生成referral link',
            'code_change': '等待平台恢复或跳过需要ref的红包',
        },
        'api_error': {
            'action': 'increase_backoff',
            'description': 'API错误，增加重试间隔',
            'code_change': '增加 retry_backoff_seconds',
        },
    }
    
    return suggestions.get(ftype, {
        'action': 'manual_review',
        'description': '需要人工检查',
        'code_change': '无自动修复方案',
    })


def log_failure_pattern(entry: dict, analysis: dict, suggestion: dict):
    """记录失败模式到日志"""
    record = {
        'timestamp': datetime.now().isoformat(),
        'packet_id': entry.get('id'),
        'failure_type': analysis['failure_type'],
        'severity': analysis['severity'],
        'question': (entry.get('question') or '')[:100],
        'answer': entry.get('answer'),
        'suggestion_action': suggestion['action'],
        'error_snippet': analysis['error_detail'][:200],
    }
    
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with FAILURE_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def update_failure_stats(analysis: dict):
    """更新失败统计"""
    stats = {}
    if FAILURE_STATS.exists():
        try:
            stats = json.loads(FAILURE_STATS.read_text())
        except Exception:
            stats = {}
    
    ftype = analysis['failure_type']
    if 'counts' not in stats:
        stats['counts'] = {}
    stats['counts'][ftype] = stats['counts'].get(ftype, 0) + 1
    stats['last_failure'] = datetime.now().isoformat()
    stats['total_failures'] = sum(stats['counts'].values())
    
    FAILURE_STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=2))


def get_failure_report() -> str:
    """生成失败报告"""
    if not FAILURE_STATS.exists():
        return "暂无失败记录"
    
    try:
        stats = json.loads(FAILURE_STATS.read_text())
    except Exception:
        return "读取失败统计出错"
    
    counts = stats.get('counts', {})
    total = stats.get('total_failures', 0)
    
    lines = [f"📊 红包失败统计 (共{total}次)"]
    
    # 按数量排序
    sorted_failures = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    for ftype, count in sorted_failures[:5]:
        desc = FAILURE_TYPES.get(ftype, {}).get('description', ftype)
        pct = (count / total * 100) if total > 0 else 0
        lines.append(f"  {desc}: {count}次 ({pct:.1f}%)")
    
    return '\n'.join(lines)


def process_failure(entry: dict) -> dict:
    """处理单个失败记录：分析、生成建议、记录"""
    analysis = analyze_failure(entry)
    suggestion = generate_fix_suggestion(analysis)
    log_failure_pattern(entry, analysis, suggestion)
    update_failure_stats(analysis)
    
    return {
        'analysis': analysis,
        'suggestion': suggestion,
    }


if __name__ == '__main__':
    # 测试
    print(get_failure_report())
