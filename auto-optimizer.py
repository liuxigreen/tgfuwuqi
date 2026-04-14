#!/usr/bin/env python3
"""
V6 自动优化器 — 根据提交历史动态调整参数 + 输出脚本修改方案

分析维度:
1. 成功率 (accepted vs rejected/spam) — 24h滚动窗口
2. 最佳人格 (哪个人格通过率最高)
3. 最佳字数区间 (哪个word range通过率最高)
4. 最佳时段 (哪个时段通过率最高)
5. 最佳间隔 (根据当前成功率动态调整)
6. Proof URL 权重 (有URL自动过spam检测)
7. 递增封禁追踪 (5min→10→20→40→80...最高8h)
8. Elite豁免 (100+ rep豁免bot farm自动封禁)
9. 报告后输出脚本修改方案

每12轮自动运行一次（由auto-loop.sh控制）
"""
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

HISTORY_FILE = Path('/root/.hermes/agenthansa/memory/submission-history.jsonl')
OPTIMIZER_STATE = Path('/root/.hermes/agenthansa/memory/optimizer-state.json')
STRATEGY_OVERRIDES = Path('/root/.hermes/agenthansa/memory/strategy-overrides.json')
LOG_PREFIX = '[optimizer]'


def log(msg):
    print(f"{LOG_PREFIX} {msg}")


def load_history(days=3):
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


def load_state():
    if OPTIMIZER_STATE.exists():
        try:
            return json.loads(OPTIMIZER_STATE.read_text())
        except Exception:
            pass
    return {
        'interval_multiplier': 1.0,
        'last_analysis': 0,
        'total_analyzed': 0,
        'ban_level': 0,  # 0=正常, 1=5min, 2=10min, 3=20min, 4=40min, 5=80min, 6=160min(2.7h), 7=480min(8h)
        'ban_until': 0,  # unix timestamp, 0=未封禁
        'spam_24h_count': 0,
        'spam_24h_window_start': 0,
    }


def save_state(state):
    OPTIMIZER_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def calc_24h_spam_rate(history):
    """计算24h滚动窗口的spam率 — 官方规则: 50%+spam率=封禁"""
    now_ts = int(time.time())
    cutoff_24h = now_ts - 86400
    recent = [e for e in history if e.get('ts', 0) >= cutoff_24h]
    if not recent:
        return 0.0, 0, 0
    total = len(recent)
    # 优先用spam_flag字段，fallback到error关键词
    spam = sum(1 for e in recent if e.get('spam_flag', False) or
               (e.get('status') == 'failed' and
                any(x in str(e.get('error', '')).lower() for x in ['spam', '400', '429', 'blocked'])))
    return spam / total, spam, total


def calc_proof_url_rate(history):
    """计算有proof URL的提交比例 — 有URL自动过spam检测"""
    recent_24h = [e for e in history if e.get('ts', 0) >= int(time.time()) - 86400]
    if not recent_24h:
        return 0.0
    with_url = sum(1 for e in recent_24h if e.get('has_proof_url', False))
    return with_url / len(recent_24h)


def get_ban_duration(ban_level):
    """递增封禁时长 — 官方规则: 5min→10→20→40→80...最高8h"""
    if ban_level <= 0:
        return 0
    durations = [0, 300, 600, 1200, 2400, 4800, 9600, 19200, 28800]  # 5min到8h
    idx = min(ban_level, len(durations) - 1)
    return durations[idx]


def check_ban_status(state):
    """检查当前是否在封禁中"""
    ban_until = state.get('ban_until', 0)
    if ban_until > 0 and ban_until > time.time():
        remaining = int(ban_until - time.time())
        return True, remaining
    elif ban_until > 0:
        # 封禁已过期，重置
        state['ban_until'] = 0
        state['ban_level'] = max(0, state.get('ban_level', 0) - 1)  # 每次封禁结束降一级
        save_state(state)
    return False, 0


def apply_ban(state, reason="spam_rate_exceeded"):
    """应用递增封禁"""
    new_level = min(state.get('ban_level', 0) + 1, 7)
    duration = get_ban_duration(new_level)
    state['ban_level'] = new_level
    state['ban_until'] = int(time.time()) + duration
    save_state(state)
    log(f"🚫 封禁等级{new_level}: {duration//60}min (原因: {reason})")
    return duration


def analyze(history):
    """分析提交历史，返回优化建议"""
    if not history:
        return None

    stats = {
        'total': len(history),
        'submitted': 0,
        'failed': 0,
        'spam': 0,
        'with_proof_url': 0,
        'without_proof_url': 0,
        'by_personality': {},
        'by_word_range': {},
        'by_hour': {},
        'by_grade': {},
        'proof_url_success_rate': 0.0,
        'no_proof_url_success_rate': 0.0,
    }

    proof_success = 0
    proof_total = 0
    no_proof_success = 0
    no_proof_total = 0

    for entry in history:
        status = entry.get('status', 'unknown')
        has_url = entry.get('has_proof_url', False)

        if status == 'submitted':
            stats['submitted'] += 1
            if has_url:
                proof_success += 1
                proof_total += 1
            else:
                no_proof_success += 1
                no_proof_total += 1
        elif status == 'failed':
            stats['failed'] += 1
            if has_url:
                proof_total += 1
            else:
                no_proof_total += 1
            # 优先用spam_flag字段
            if entry.get('spam_flag', False):
                stats['spam'] += 1
            else:
                err = str(entry.get('error', '')).lower()
                if any(x in err for x in ['spam', '400', '429', 'blocked']):
                    stats['spam'] += 1

        # proof URL统计
        if has_url:
            stats['with_proof_url'] += 1
        else:
            stats['without_proof_url'] += 1

        # AI评分统计
        grade = (entry.get('ai_grade') or '').upper()
        if grade and grade in 'ABCDF':
            stats['by_grade'][grade] = stats['by_grade'].get(grade, 0) + 1

        # 按人格统计
        persona = entry.get('personality', 'unknown')
        if persona not in stats['by_personality']:
            stats['by_personality'][persona] = {'total': 0, 'success': 0}
        stats['by_personality'][persona]['total'] += 1
        if status == 'submitted':
            stats['by_personality'][persona]['success'] += 1

        # 按字数区间统计
        words = entry.get('words', 0)
        if words < 100:
            range_key = '80-100'
        elif words < 130:
            range_key = '100-130'
        elif words < 170:
            range_key = '130-170'
        else:
            range_key = '170-200'
        if range_key not in stats['by_word_range']:
            stats['by_word_range'][range_key] = {'total': 0, 'success': 0}
        stats['by_word_range'][range_key]['total'] += 1
        if status == 'submitted':
            stats['by_word_range'][range_key]['success'] += 1

        # 按时段统计
        hour = datetime.fromtimestamp(entry['ts'], tz=timezone.utc).hour
        hour_key = f"{hour:02d}"
        if hour_key not in stats['by_hour']:
            stats['by_hour'][hour_key] = {'total': 0, 'success': 0}
        stats['by_hour'][hour_key]['total'] += 1
        if status == 'submitted':
            stats['by_hour'][hour_key]['success'] += 1

    # proof URL成功率
    stats['proof_url_success_rate'] = proof_success / proof_total if proof_total > 0 else 0
    stats['no_proof_url_success_rate'] = no_proof_success / no_proof_total if no_proof_total > 0 else 0

    return stats


def generate_modification_plan(stats, state, spam_rate_24h, proof_url_rate):
    """根据分析结果生成脚本修改方案"""
    plans = []
    total = stats['total']
    success_rate = stats['submitted'] / total if total > 0 else 0

    # 1. Proof URL相关
    if proof_url_rate < 0.5 and stats['proof_url_success_rate'] > stats['no_proof_url_success_rate']:
        plans.append({
            'priority': 'HIGH',
            'target': 'agenthansa-auto.py',
            'action': '提交前检查proof_url字段，无URL时自动跳过需要proof的quest',
            'reason': f"有URL成功率{stats['proof_url_success_rate']:.0%} vs 无URL{stats['no_proof_url_success_rate']:.0%}",
        })

    # 2. Spam率相关 — 官方50%封禁线
    if spam_rate_24h > 0.3:
        plans.append({
            'priority': 'CRITICAL',
            'target': 'auto-loop.sh',
            'action': f"暂停自动提交{get_ban_duration(state['ban_level']+1)//60}min，spam率{spam_rate_24h:.0%}接近50%封禁线",
            'reason': '官方规则: 50%+spam率=禁止提交新quest',
        })

    # 3. AI评分相关
    low_grades = stats['by_grade'].get('D', 0) + stats['by_grade'].get('F', 0)
    low_grade_rate = low_grades / total if total > 0 else 0
    if low_grade_rate > 0.3:
        plans.append({
            'priority': 'HIGH',
            'target': 'agenthansa-auto.py',
            'action': '提高_content_quality_score阈值从3→4，减少D/F评分',
            'reason': f"AI低分率{low_grade_rate:.0%}过高，影响通过率",
        })

    # 4. 人格相关
    if stats['by_personality']:
        best_persona = max(stats['by_personality'].items(),
                          key=lambda x: x[1]['success']/max(x[1]['total'],1))
        worst_persona = min(stats['by_personality'].items(),
                           key=lambda x: x[1]['success']/max(x[1]['total'],1))
        if best_persona[1]['total'] >= 2:
            plans.append({
                'priority': 'MEDIUM',
                'target': 'agenthansa-auto.py',
                'action': f"优先使用{best_persona[0]}人格(成功率{best_persona[1]['success']/best_persona[1]['total']:.0%})，减少{worst_persona[0]}",
                'reason': f"人格通过率差异明显",
            })

    # 5. 间隔调整
    if success_rate < 0.5:
        plans.append({
            'priority': 'HIGH',
            'target': 'auto-loop.sh',
            'action': f"将提交间隔从当前{state.get('interval_multiplier',1.0):.1f}x拉长到{min(state.get('interval_multiplier',1.0)*1.5, 2.0):.1f}x",
            'reason': f"成功率{success_rate:.0%}过低，需要更长冷却",
        })

    # 6. 字数区间
    if stats['by_word_range']:
        best_range = max(stats['by_word_range'].items(),
                        key=lambda x: x[1]['success']/max(x[1]['total'],1))
        if best_range[1]['total'] >= 2:
            plans.append({
                'priority': 'LOW',
                'target': 'agenthansa-auto.py',
                'action': f"将字数目标调整到{best_range[0]}词区间(成功率{best_range[1]['success']/best_range[1]['total']:.0%})",
                'reason': f"该区间通过率最高",
            })

    return plans


def run_analysis():
    """完整分析 + 输出报告 + 生成修改方案"""
    history = load_history(days=3)
    if len(history) < 3:
        log(f"历史数据不足({len(history)}条)，跳过分析")
        return

    stats = analyze(history)
    if not stats:
        return

    state = load_state()
    total = stats['total']
    success_rate = stats['submitted'] / total if total > 0 else 0
    spam_rate_24h, spam_24h, total_24h = calc_24h_spam_rate(history)
    proof_url_rate = calc_proof_url_rate(history)
    is_banned, ban_remaining = check_ban_status(state)

    log(f"=== V6 分析报告 (24h窗口) ===")
    log(f"总计: {total} | 成功: {stats['submitted']}({success_rate:.0%}) | 失败: {stats['failed']}")
    log(f"24h窗口: {total_24h}次提交, spam率{spam_rate_24h:.0%}({spam_24h}/{total_24h})")
    log(f"Proof URL: {stats['with_proof_url']}有/{stats['without_proof_url']}无(有URL成功率{stats['proof_url_success_rate']:.0%})")
    if is_banned:
        log(f"🚫 当前封禁中，剩余{ban_remaining//60}min")

    # AI评分分布
    if stats['by_grade']:
        grade_str = ' '.join(f"{g}:{c}" for g, c in sorted(stats['by_grade'].items()))
        log(f"AI评分分布: {grade_str}")

    # 人格分析
    log("按人格:")
    best_persona = None
    best_rate = 0
    for persona, data in sorted(stats['by_personality'].items()):
        rate = data['success'] / data['total'] if data['total'] > 0 else 0
        log(f"  {persona}: {data['success']}/{data['total']} ({rate:.0%})")
        if rate > best_rate and data['total'] >= 2:
            best_rate = rate
            best_persona = persona

    # 字数分析
    log("按字数区间:")
    for wr, data in sorted(stats['by_word_range'].items()):
        rate = data['success'] / data['total'] if data['total'] > 0 else 0
        log(f"  {wr}词: {data['success']}/{data['total']} ({rate:.0%})")

    # 时段分析
    log("按UTC时段 (前5):")
    sorted_hours = sorted(stats['by_hour'].items(), key=lambda x: x[1]['success']/max(x[1]['total'],1), reverse=True)
    for hour, data in sorted_hours[:5]:
        rate = data['success'] / data['total'] if data['total'] > 0 else 0
        log(f"  {hour}:00: {data['success']}/{data['total']} ({rate:.0%})")

    # 动态调整间隔 — 官方规则: 50%+spam率=封提交
    if spam_rate_24h > 0.4:
        new_multiplier = min(state['interval_multiplier'] * 2.0, 3.0)
        duration = apply_ban(state, f"spam_rate_{spam_rate_24h:.0%}")
        log(f"🚨 Spam率{spam_rate_24h:.0%}接近封禁线(50%)！封禁{duration//60}min，间隔拉长至{new_multiplier:.1f}x")
    elif spam_rate_24h > 0.25:
        new_multiplier = min(state['interval_multiplier'] * 1.5, 2.0)
        log(f"⚠️ Spam率{spam_rate_24h:.0%}过高，间隔拉长至{new_multiplier:.1f}x")
    elif spam_rate_24h > 0.1:
        new_multiplier = min(state['interval_multiplier'] * 1.15, 1.5)
        log(f"⚠️ Spam率{spam_rate_24h:.0%}偏高，间隔微调至{new_multiplier:.1f}x")
    elif stats['by_grade']:
        low_grades = stats['by_grade'].get('D', 0) + stats['by_grade'].get('F', 0)
        low_grade_rate = low_grades / total if total > 0 else 0
        if low_grade_rate > 0.3:
            new_multiplier = min(state['interval_multiplier'] * 1.2, 1.8)
            log(f"📝 AI低分率{low_grade_rate:.0%}过高，间隔调整至{new_multiplier:.1f}x")
        elif success_rate > 0.8 and spam_rate_24h < 0.05:
            new_multiplier = max(state['interval_multiplier'] * 0.9, 0.7)
            log(f"✅ 成功率{success_rate:.0%}良好，间隔缩短至{new_multiplier:.1f}x")
        else:
            new_multiplier = state['interval_multiplier']
            log(f"📊 参数保持不变 ({new_multiplier:.1f}x)")
    else:
        new_multiplier = state['interval_multiplier']
        log(f"📊 参数保持不变 ({new_multiplier:.1f}x)")

    state['interval_multiplier'] = new_multiplier
    state['last_analysis'] = int(time.time())
    state['total_analyzed'] = total
    state['spam_24h_count'] = spam_24h
    state['spam_24h_window_start'] = int(time.time()) - 86400
    save_state(state)

    # 生成修改方案
    plans = generate_modification_plan(stats, state, spam_rate_24h, proof_url_rate)

    # 保存修改方案到文件
    if plans:
        plan_file = Path('/root/.hermes/agenthansa/memory/optimizer-plan.json')
        plan_data = {
            'timestamp': datetime.now().isoformat(),
            'stats_summary': {
                'total': total,
                'success_rate': success_rate,
                'spam_rate_24h': spam_rate_24h,
                'proof_url_rate': proof_url_rate,
                'best_persona': best_persona,
                'best_persona_rate': best_rate,
            },
            'plans': plans,
        }
        plan_file.write_text(json.dumps(plan_data, indent=2, ensure_ascii=False))
        log(f"📋 生成{len(plans)}条修改方案 → {plan_file}")

        for i, p in enumerate(plans, 1):
            log(f"  {i}. [{p['priority']}] {p['target']}: {p['action']}")

    # 发TG通知
    try:
        grade_str = ' '.join(f"{g}:{c}" for g, c in sorted(stats.get('by_grade', {}).items())) if stats.get('by_grade') else 'N/A'
        ban_str = f"🚫封禁{ban_remaining//60}min" if is_banned else "✅正常"
        plan_count = len(plans)
        notify_msg = (
            f"📊 V6自动优化报告\n"
            f"总计:{total} 成功:{success_rate:.0%} 24h-spam:{spam_rate_24h:.0%}\n"
            f"Proof-URL:{proof_url_rate:.0%} {ban_str}\n"
            f"评分:{grade_str}\n"
            f"最佳:{best_persona}({best_rate:.0%})\n"
            f"间隔:{new_multiplier:.1f}x\n"
            f"📋{plan_count}条修改方案"
        )
        _notify_tg(notify_msg)
    except Exception:
        pass


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


def get_adjusted_interval(base_interval):
    """动态调整间隔 — 被agenthansa-auto.py调用"""
    state = load_state()

    # 检查封禁状态
    is_banned, remaining = check_ban_status(state)
    if is_banned:
        return remaining + 60  # 封禁中返回剩余时间+1min

    multiplier = state.get('interval_multiplier', 1.0)

    # 检查策略覆盖文件
    if STRATEGY_OVERRIDES.exists():
        try:
            overrides = json.loads(STRATEGY_OVERRIDES.read_text())
            if 'interval_multiplier' in overrides:
                multiplier = overrides['interval_multiplier']
        except Exception:
            pass

    adjusted = int(base_interval * multiplier)
    # 保底: 最少25min，最多120min
    return max(1500, min(adjusted, 7200))


if __name__ == '__main__':
    run_analysis()
