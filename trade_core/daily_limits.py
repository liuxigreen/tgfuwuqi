from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

ENTRY_ACTIONS = {"open_long", "open_short", "small_probe"}
EXIT_ACTIONS = {"reduce", "close"}


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
    item = state.get(day, {"trades": 0, "losses": 0, "consecutive_losses": 0, "symbol_count": {}, "last_loss_at": None, "last_symbol_trade_at": {}, "daily_pnl_pct": 0.0, "daily_pnl_usdt": 0.0})

    if action in EXIT_ACTIONS and cfg.get("allow_position_exit_when_disabled", True):
        return {"passed": True, "blocked_reasons": [], "day": day, "state": item}

    blocked = False
    reasons = []
    now = datetime.now(timezone.utc)
    if action in ENTRY_ACTIONS:
        if item.get('trades', 0) >= int(cfg.get('max_trades_per_day', 8)):
            blocked = True; reasons.append('max_trades_per_day_hit')
        if item.get('consecutive_losses', 0) >= int(cfg.get('max_consecutive_losses', 3)):
            blocked = True; reasons.append('max_consecutive_losses_hit')
        if item.get('losses', 0) >= int(cfg.get('max_losses_per_day', 3)):
            blocked = True; reasons.append('max_losses_per_day_hit')
        if abs(float(item.get('daily_pnl_pct', 0))) >= float(cfg.get('max_daily_loss_pct', 2.0)):
            blocked = True; reasons.append('max_daily_loss_pct_hit')
        if abs(float(item.get('daily_pnl_usdt', 0))) >= float(cfg.get('max_daily_loss_usdt', 100)):
            blocked = True; reasons.append('max_daily_loss_usdt_hit')
        if item.get('symbol_count', {}).get(symbol, 0) >= int(cfg.get('max_same_symbol_trades_per_day', 2)):
            blocked = True; reasons.append('max_same_symbol_trades_per_day_hit')
        last_symbol = item.get('last_symbol_trade_at', {}).get(symbol)
        if last_symbol:
            try:
                if now - datetime.fromisoformat(last_symbol) < timedelta(minutes=int(cfg.get('symbol_cooldown_minutes', 60))):
                    blocked = True; reasons.append('symbol_cooldown_hit')
            except Exception:
                pass
        last_loss = item.get('last_loss_at')
        if last_loss:
            try:
                if now - datetime.fromisoformat(last_loss) < timedelta(minutes=int(cfg.get('cooldown_after_loss_minutes', 30))):
                    blocked = True; reasons.append('cooldown_after_loss_active')
            except Exception:
                pass
    return {"passed": not blocked, "blocked_reasons": reasons, "day": day, "state": item}


def record_trade(symbol: str, pnl_usdt: float, pnl_pct: float = 0.0, path='data/daily_limits_state.json'):
    if isinstance(pnl_pct, str):
        path = pnl_pct
        pnl_pct = 0.0
    st = load_limits_state(path); day = _date_key(); item = st.get(day, {"trades":0,"losses":0,"consecutive_losses":0,"symbol_count":{},"last_symbol_trade_at":{},"daily_pnl_pct":0.0,"daily_pnl_usdt":0.0})
    now = datetime.now(timezone.utc).isoformat()
    item['trades'] = item.get('trades', 0) + 1
    item.setdefault('symbol_count', {})[symbol] = item.get('symbol_count', {}).get(symbol, 0) + 1
    item.setdefault('last_symbol_trade_at', {})[symbol] = now
    item['daily_pnl_usdt'] = float(item.get('daily_pnl_usdt', 0.0)) + float(pnl_usdt)
    item['daily_pnl_pct'] = float(item.get('daily_pnl_pct', 0.0)) + float(pnl_pct)
    if pnl_usdt < 0:
        item['losses'] = item.get('losses', 0) + 1
        item['consecutive_losses'] = item.get('consecutive_losses', 0) + 1
        item['last_loss_at'] = now
    else:
        item['consecutive_losses'] = 0
    st[day] = item
    save_limits_state(st, path)


def limits_status(path='data/daily_limits_state.json'):
    st = load_limits_state(path); day = _date_key(); return {"date": day, "state": st.get(day, {})}


def limits_reset(date: str, path='data/daily_limits_state.json'):
    st = load_limits_state(path); st.pop(date, None); save_limits_state(st, path); return {"ok": True, "date": date}
