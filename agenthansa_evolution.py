#!/usr/bin/env python3
"""
AgentHansa Self-Evolution 机制
每日分析 → 自动调参 → 策略进化
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

EVOLUTION_FILE = Path('/root/.hermes/agenthansa/memory/evolution.json')
TASK_SUMMARY_FILE = Path('/root/.hermes/agenthansa/memory/agenthansa-task-summary.jsonl')


def load_evolution():
    if EVOLUTION_FILE.exists():
        try:
            return json.loads(EVOLUTION_FILE.read_text())
        except Exception:
            pass
    return {
        'daily_stats': [],
        'blacklisted_patterns': [
            'daily feedback quest', 'rate and review fellow agents',
            'quick feedback', 'simple review', 'short answer', 'shoutout'
        ],
        'winning_angles': [],
        'current_params': {
            'quality_threshold': 55,
            'max_auto_quests': 2,
            'angle_dedup_days': 7,
            'min_reward_usdc': 5
        },
        'angle_history': {}
    }


def save_evolution(evo):
    EVOLUTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    EVOLUTION_FILE.write_text(json.dumps(evo, indent=2, ensure_ascii=False))


def analyze_today():
    """分析今天的 task summary，生成统计"""
    if not TASK_SUMMARY_FILE.exists():
        return None

    today = datetime.now().strftime('%Y-%m-%d')
    stats = {
        'date': today,
        'quests_submitted': 0,
        'quests_accepted': 0,
        'quests_spam_flagged': 0,
        'redpackets_won': 0,
        'redpackets_failed': 0,
        'failure_reasons': {},
        'top_angles_used': [],
        'spam_patterns': [],
        'strategy_adjustments': []
    }

    for line in TASK_SUMMARY_FILE.read_text().splitlines():
        try:
            entry = json.loads(line)
        except Exception:
            continue
        ts = entry.get('ts', '')
        if not ts.startswith(today):
            continue

        status = entry.get('status', '')
        if status == 'submitted':
            stats['quests_submitted'] += 1
        elif status == 'accepted':
            stats['quests_accepted'] += 1
        elif status == 'spam_flagged':
            stats['quests_spam_flagged'] += 1
            reason = entry.get('reason', 'unknown')
            stats['spam_patterns'].append(reason)
        elif status == 'redpacket_success':
            stats['redpackets_won'] += 1
        elif status == 'redpacket_fail':
            stats['redpackets_failed'] += 1
            reason = entry.get('reason', 'unknown')
            stats['failure_reasons'][reason] = stats['failure_reasons'].get(reason, 0) + 1

    return stats


def evolve(evo=None):
    """执行进化：分析数据 → 调整参数"""
    if evo is None:
        evo = load_evolution()

    stats = analyze_today()
    if not stats:
        return evo

    params = evo['current_params']
    adjustments = []

    # 分析最近 3 天数据
    recent = evo['daily_stats'][-3:] if len(evo['daily_stats']) >= 3 else evo['daily_stats']

    if recent:
        # 连续 3 天 spam 率 > 20% → quality_threshold += 5
        spam_rates = []
        for d in recent:
            total = d.get('quests_submitted', 0)
            spam = d.get('quests_spam_flagged', 0)
            if total > 0:
                spam_rates.append(spam / total)
        if len(spam_rates) >= 3 and all(r > 0.2 for r in spam_rates):
            params['quality_threshold'] = min(params.get('quality_threshold', 55) + 5, 80)
            adjustments.append('quality_threshold += 5 (spam率高)')

        # 连续 3 天成功率 > 80% → max_auto_quests += 1
        success_rates = []
        for d in recent:
            total = d.get('quests_submitted', 0)
            accepted = d.get('quests_accepted', 0)
            if total > 0:
                success_rates.append(accepted / total)
        if len(success_rates) >= 3 and all(r > 0.8 for r in success_rates):
            params['max_auto_quests'] = min(params.get('max_auto_quests', 2) + 1, 5)
            adjustments.append('max_auto_quests += 1 (成功率高)')

    # 更新统计数据
    evo['daily_stats'].append(stats)
    # 保留最近 30 天
    evo['daily_stats'] = evo['daily_stats'][-30:]

    if adjustments:
        stats['strategy_adjustments'] = adjustments

    save_evolution(evo)
    return evo


def get_angle_key(title: str) -> str:
    """生成角度指纹"""
    import re
    words = re.findall(r'[a-z]{3,}', title.lower())
    # 取前 3 个关键词
    return ' '.join(words[:3])


def is_angle_duplicate(title: str, evo=None) -> bool:
    """检查角度是否在去重窗口内用过"""
    if evo is None:
        evo = load_evolution()
    key = get_angle_key(title)
    history = evo.get('angle_history', {})
    if key not in history:
        return False
    used_date = history[key]
    try:
        used_dt = datetime.fromisoformat(used_date)
        dedup_days = evo['current_params'].get('angle_dedup_days', 7)
        return datetime.now() - used_dt < timedelta(days=dedup_days)
    except Exception:
        return False


def mark_angle_used(title: str, evo=None):
    """标记角度已使用"""
    if evo is None:
        evo = load_evolution()
    key = get_angle_key(title)
    evo.setdefault('angle_history', {})[key] = datetime.now().isoformat()
    save_evolution(evo)


def daily_report_text(stats: dict) -> str:
    """生成每日报告文本"""
    lines = [
        f'📊 AgentHansa 日报 [{stats.get("date", "today")}]',
        f'  Quest: {stats.get("quests_submitted", 0)}提/{stats.get("quests_accepted", 0)}过',
        f'  红包: {stats.get("redpackets_won", 0)}抢/{stats.get("redpackets_failed", 0)}次',
    ]
    if stats.get('quests_spam_flagged'):
        lines.append(f'  ⚠️ Spam: {stats["quests_spam_flagged"]}个')
    if stats.get('failure_reasons'):
        reasons = ', '.join(f'{k}({v})' for k, v in stats['failure_reasons'].items())
        lines.append(f'  失败原因: {reasons}')
    if stats.get('strategy_adjustments'):
        for adj in stats['strategy_adjustments']:
            lines.append(f'  🔧 {adj}')
    return '\n'.join(lines)


if __name__ == '__main__':
    evo = evolve()
    stats = analyze_today()
    if stats:
        print(daily_report_text(stats))
    else:
        print('No data for today')
    print(f"\nCurrent params: {json.dumps(evo['current_params'], indent=2)}")
