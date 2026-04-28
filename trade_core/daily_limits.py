from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def _date_key(date_str: str | None = None):
    return date_str or datetime.now(timezone.utc).date().isoformat()


def _file(base='data/daily_limits_state.json'):
    p = Path(base)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("{}", encoding='utf-8')
    return p


def load_limits_state(path='data/daily_limits_state.json') -> Dict:
    return json.loads(_file(path).read_text(encoding='utf-8'))


def save_limits_state(state: Dict, path='data/daily_limits_state.json'):
    _file(path).write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')


def check_daily_limits(symbol: str, action: str, config: Dict, path='data/daily_limits_state.json') -> Dict:
    cfg = config.get('daily_limits', {})
    state = load_limits_state(path)
    day = _date_key()
    item = state.get(day, {"trades": 0, "losses": 0, "consecutive_losses": 0, "symbol_count": defaultdict(int)})
    # normalize defaultdict serialization
    if not isinstance(item.get('symbol_count', {}), dict):
        item['symbol_count'] = {}
    blocked = False; reasons = []
    if action in {'open_long','open_short','small_probe'}:
        if item.get('trades',0) >= int(cfg.get('max_trades_per_day', 8)):
            blocked=True; reasons.append('max_trades_per_day_hit')
        if item.get('consecutive_losses',0) >= int(cfg.get('max_consecutive_losses',3)):
            blocked=True; reasons.append('max_consecutive_losses_hit')
        if item.get('symbol_count',{}).get(symbol,0) >= int(cfg.get('max_same_symbol_trades_per_day',2)):
            blocked=True; reasons.append('symbol_cooldown_hit')
    return {"passed": not blocked, "blocked_reasons": reasons, "day": day, "state": item}


def record_trade(symbol: str, pnl_usdt: float, path='data/daily_limits_state.json'):
    st = load_limits_state(path); day = _date_key(); item = st.get(day, {"trades":0,"losses":0,"consecutive_losses":0,"symbol_count":{}})
    item['trades']=item.get('trades',0)+1
    item['symbol_count'][symbol]=item.get('symbol_count',{}).get(symbol,0)+1
    if pnl_usdt < 0:
        item['losses']=item.get('losses',0)+1; item['consecutive_losses']=item.get('consecutive_losses',0)+1
    else:
        item['consecutive_losses']=0
    st[day]=item; save_limits_state(st,path)


def limits_status(path='data/daily_limits_state.json'):
    st=load_limits_state(path); day=_date_key(); return {"date": day, "state": st.get(day, {})}


def limits_reset(date: str, path='data/daily_limits_state.json'):
    st=load_limits_state(path); st.pop(date, None); save_limits_state(st,path); return {"ok":True,"date":date}
