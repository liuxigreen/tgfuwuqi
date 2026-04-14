#!/usr/bin/env python3
"""
V5 排名追击 — 每天13:00/14:00检查排名
差距<100分 → 拉人工任务发TG通知
差距>100分 → 跳过不打扰
"""
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
import re

CONFIG = Path('/root/.hermes/agenthansa/config.json')
LOG_PREFIX = '[rank-chase]'

def log(msg):
    print(f"{LOG_PREFIX} {msg}")

def notify(msg):
    """发TG通知"""
    try:
        token = '8604975156:AAEiiua-WKjs0nyt3g3Itjy-eYEBfx-mmGI'
        chat_id = '6305628029'
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({'chat_id': chat_id, 'text': msg}).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

def load_cfg():
    return json.loads(CONFIG.read_text())

def api_get(path, key):
    req = urllib.request.Request(f'https://www.agenthansa.com/api{path}',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())

def get_my_rank(key):
    """获取我在绿色联盟的排名和积分"""
    data = api_get('/agents/alliance-daily-leaderboard', key)
    green = data.get('alliances', {}).get('green', {})
    leaderboard = green.get('leaderboard', [])
    
    # 拉更多排名（API可能只返回top10）
    try:
        data2 = api_get('/agents/alliance-daily-leaderboard?alliance=green&per_page=100', key)
        if isinstance(data2, dict) and 'leaderboard' in data2:
            leaderboard = data2['leaderboard']
    except Exception:
        pass
    
    # 找Xiami
    my_entry = None
    for entry in leaderboard:
        name = (entry.get('name') or '').lower()
        if 'xiami' in name:
            my_entry = entry
            break
    
    if not my_entry:
        # 不在榜上，返回top3信息
        top3 = []
        for e in leaderboard[:3]:
            top3.append({'rank': e['rank'], 'name': e['name'], 'pts': e['today_points']})
        return None, top3, green.get('members', 0)
    
    top3 = []
    for e in leaderboard[:3]:
        top3.append({'rank': e['rank'], 'name': e['name'], 'pts': e['today_points']})
    
    return my_entry, top3, green.get('members', 0)

def get_manual_quests(key):
    """拉需要人工操作的open quest"""
    data = api_get('/alliance-war/quests?per_page=50', key)
    quests = data.get('quests', [])
    
    manual = []
    for q in quests:
        if q.get('status') != 'open':
            continue
        title = q.get('title', '')
        desc = (q.get('description') or '') + ' ' + (q.get('requirements') or '')
        low = (title + ' ' + desc).lower()
        
        amounts = re.findall(r'\$(\d+(?:\.\d+)?)', title)
        usdc = float(amounts[0]) if amounts else 0
        if usdc < 20:
            continue
        
        need = []
        if 'video' in low or 'tiktok' in low: need.append('录视频')
        if 'twitter' in low or 'tweet' in low or 'x.com' in low: need.append('发推')
        if 'reddit' in low: need.append('发Reddit')
        if 'linkedin' in low: need.append('发LinkedIn')
        if 'youtube' in low: need.append('发YouTube')
        if 'screenshot' in low or 'photo' in low: need.append('截图')
        if 'follow' in low: need.append('涨粉')
        
        if need:
            manual.append({
                'usdc': usdc,
                'title': title[:60],
                'need': ' + '.join(need),
                'id': q['id'],
            })
    
    manual.sort(key=lambda x: x['usdc'], reverse=True)
    return manual[:5]

def check_and_notify():
    """主逻辑"""
    cfg = load_cfg()
    key = cfg.get('api_key')
    if not key:
        log('无API key')
        return
    
    # 检查时间 — 只在13:00-13:30和14:00-14:30 UTC运行
    now = datetime.now(timezone.utc)
    hour = now.hour
    if hour not in (13, 14):
        log(f'当前UTC {hour}:00，不在检查窗口(13-14)')
        return
    
    log('检查排名...')
    my_entry, top3, members = get_my_rank(key)
    
    if not top3:
        log('无法获取排名')
        return
    
    top1_pts = top3[0]['pts'] if top3 else 0
    top3_min_pts = top3[2]['pts'] if len(top3) >= 3 else top1_pts
    
    if my_entry:
        my_pts = my_entry['today_points']
        my_rank = my_entry['rank']
        gap_to_3 = top3_min_pts - my_pts
        gap_to_1 = top1_pts - my_pts
        log(f'我: #{my_rank} ({my_pts}pts) | Top1: {top1_pts}pts (差{gap_to_1}) | Top3: {top3_min_pts}pts (差{gap_to_3})')
    else:
        my_pts = 0
        my_rank = '?'
        gap_to_3 = top3_min_pts
        gap_to_1 = top1_pts
        log(f'未上榜 | Top1: {top1_pts}pts | Top3: {top3_min_pts}pts | 需要{top3_min_pts}分进前3')
    
    # 差距>100 → 不打扰
    if gap_to_3 > 100:
        log(f'差距{gap_to_3}pts > 100，不发通知')
        return
    
    # 差距<100 → 拉人工任务发通知
    log(f'差距{gap_to_3}pts ≤ 100，拉任务发通知')
    manual = get_manual_quests(key)
    
    if not manual:
        log('无可做的人工任务')
        return
    
    # 构建通知
    lines = [
        f'🏆 排名追击 | 差{gap_to_3}分进前3',
        f'当前: #{my_rank} ({my_pts}pts) | Top3: {top3_min_pts}pts',
        '',
        '可做任务:',
    ]
    for i, m in enumerate(manual[:3]):
        lines.append(f'{i+1}. ${m["usdc"]:.0f} {m["title"]}')
        lines.append(f'   需要: {m["need"]}')
    
    lines.append('')
    lines.append('做完发我链接秒提交!')
    
    msg = '\n'.join(lines)
    log(msg)
    notify(msg)

if __name__ == '__main__':
    check_and_notify()
