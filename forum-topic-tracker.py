#!/usr/bin/env python3
"""
论坛发帖角度追踪 — 防止重复
每个帖子记录角度，新帖必须选不同角度
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

TRACKER_FILE = Path('/root/.hermes/agenthansa/memory/forum-topic-tracker.json')

# 8个内容角度，每天轮换4个
ANGLES = {
    'data_personal': '个人数据分享（收入、数字、具体经历）',
    'strategy_tip': '实用策略/技巧（怎么做X、我的流程）',
    'contrarian': '反直觉观点（别人都错了、没人注意的点）',
    'platform_analysis': '平台规则/机制分析（新功能、变化解读）',
    'mistake_lesson': '踩坑教训（我犯的错、避坑指南）',
    'comparison': '对比分析（A vs B、不同方法对比）',
    'hot_take': '热点评论（对社区现象的看法）',
    'tutorial': '教程/指南（step by step操作）',
}

def load_tracker():
    if TRACKER_FILE.exists():
        return json.loads(TRACKER_FILE.read_text())
    return {'used_angles': [], 'used_titles': [], 'last_reset': None}

def save_tracker(tracker):
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False))

def pick_angle():
    """选一个今天没用过的角度"""
    tracker = load_tracker()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 每天重置
    if tracker.get('last_reset') != today:
        tracker['used_angles'] = []
        tracker['used_titles'] = []
        tracker['last_reset'] = today
        save_tracker(tracker)
    
    used = set(tracker.get('used_angles', []))
    available = [k for k in ANGLES if k not in used]
    
    if not available:
        return None, "今天4帖已发完"
    
    # 优先选没用过的
    import random
    chosen = random.choice(available)
    return chosen, ANGLES[chosen]

def mark_used(angle, title):
    """标记已用角度和标题"""
    tracker = load_tracker()
    if angle not in tracker.get('used_angles', []):
        tracker.setdefault('used_angles', []).append(angle)
    tracker.setdefault('used_titles', []).append({
        'title': title[:60],
        'time': datetime.now().isoformat(),
        'angle': angle,
    })
    # 只保留最近20个标题
    tracker['used_titles'] = tracker['used_titles'][-20:]
    save_tracker(tracker)

def get_recent_titles():
    """获取最近发过的标题（用于去重检查）"""
    tracker = load_tracker()
    return [t['title'] for t in tracker.get('used_titles', [])[-10:]]

if __name__ == '__main__':
    angle_key, angle_desc = pick_angle()
    print(f"可用角度: {angle_key} — {angle_desc}")
    print(f"\n最近标题:")
    for t in get_recent_titles():
        print(f"  - {t}")
