#!/usr/bin/env python3
"""
OI持续放大 + 费率由正转负 扫描器 + 自动跟单
- 每5分钟运行一次
- 检测: 费率由正转负 + OI在涨(>8%) + 成交量>5M
- 自动开0.01张多单，SL=-3%, TP=+10%
- 最大持仓3个，同一币种24h内不重复开仓
- 纯币安公开API零成本扫信号，OKX demo执行
"""

import requests
import json
import os
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ALERT_HISTORY_FILE = SCRIPT_DIR / "oi_funding_alerts.json"
FR_SNAPSHOT_FILE = SCRIPT_DIR / "fr_snapshot.json"
TRADE_HISTORY = SCRIPT_DIR / "trade_history.json"
LOG_FILE = SCRIPT_DIR / "logs/auto_signal_trader.log"

# TG 配置
TG_BOT_TOKEN = os.getenv("AGENTHANSA_TELEGRAM_TOKEN", "")
TG_CHAT_ID = os.getenv("AGENTHANSA_TELEGRAM_CHAT_ID", "")

# 信号参数
MIN_OI_CHANGE_PCT = 8
MIN_VOLUME_USDT = 5_000_000
DEDUP_HOURS = 24
MAX_POSITIONS = 3
LEVERAGE = 10
ORDER_SIZE = "0.01"
SL_PCT = 0.03
TP_PCT = 0.10

# ============ 日志 ============
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ============ TG推送 ============
def send_tg(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        log(f"[TG] 未配置: token={'有' if TG_BOT_TOKEN else '无'} chat={'有' if TG_CHAT_ID else '无'}")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        try:
            resp = requests.post(url, json={
                'chat_id': TG_CHAT_ID,
                'text': chunk,
                'parse_mode': 'Markdown'
            }, timeout=10)
            if resp.status_code != 200:
                requests.post(url, json={'chat_id': TG_CHAT_ID, 'text': chunk}, timeout=10)
        except Exception as e:
            log(f"[TG] 发送失败: {e}")

# ============ 持仓管理 ============
def get_open_positions():
    """获取OKX当前持仓列表"""
    try:
        r = subprocess.run(
            ["okx", "--demo", "--json", "swap", "positions"],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(r.stdout.strip())
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return []
    except Exception as e:
        log(f"获取持仓失败: {e}")
        return []

def count_open_trades():
    """从trade_history.json统计open状态"""
    try:
        if TRADE_HISTORY.exists():
            with open(TRADE_HISTORY, "r") as f:
                history = json.load(f)
            return sum(1 for t in history if t.get("status") == "open")
    except:
        pass
    return 0

def get_open_symbols():
    """已有open持仓的币种集合"""
    symbols = set()
    try:
        if TRADE_HISTORY.exists():
            with open(TRADE_HISTORY, "r") as f:
                history = json.load(f)
            for t in history:
                if t.get("status") == "open":
                    symbols.add(t.get("symbol", ""))
    except:
        pass
    # 也检查OKX实际持仓
    for pos in get_open_positions():
        symbols.add(pos.get("instId", ""))
    return symbols

# ============ 自动开仓 ============
def auto_open(symbol, signal_data):
    """信号触发自动开多单"""
    instId = f"{symbol}-USDT-SWAP"
    
    # 检查是否已有持仓
    if instId in get_open_symbols():
        log(f"  {instId} 已有持仓，跳过")
        return False
    
    # 检查持仓上限
    open_count = count_open_trades()
    if open_count >= MAX_POSITIONS:
        log(f"  当前持仓 {open_count}/{MAX_POSITIONS}，已达上限，跳过 {instId}")
        return False
    
    # 获取当前价格（用于计算SL/TP）
    entry_price = signal_data.get("price", 0)
    if entry_price <= 0:
        try:
            r = subprocess.run(
                ["okx", "--demo", "--json", "market", "ticker", instId],
                capture_output=True, text=True, timeout=10
            )
            ticker = json.loads(r.stdout.strip())
            if isinstance(ticker, dict) and "data" in ticker and ticker["data"]:
                entry_price = float(ticker["data"][0]["last"])
        except Exception as e:
            log(f"  获取 {instId} 价格失败: {e}")
            return False
    
    sl = round(entry_price * (1 - SL_PCT), 4)
    tp = round(entry_price * (1 + TP_PCT), 4)
    
    # 执行开仓
    log(f"  🚀 自动开仓 {instId} 多 0.01张 @ {entry_price}, SL={sl}, TP={tp}")
    try:
        r = subprocess.run(
            ["okx", "--demo", "--json", "swap", "open",
             "--instId", instId, "--side", "buy", "--sz", ORDER_SIZE,
             "--lever", str(LEVERAGE)],
            capture_output=True, text=True, timeout=15
        )
        result = json.loads(r.stdout.strip())
        if isinstance(result, list):
            result = {"data": result}
        
        # 记录交易
        trade = {
            "symbol": instId,
            "side": "buy",
            "entry_price": entry_price,
            "size": ORDER_SIZE,
            "sl": sl,
            "tp": tp,
            "status": "open",
            "strategy": "oi_fr_signal",
            "open_time": datetime.now().isoformat(),
            "signal": signal_data
        }
        
        history = []
        if TRADE_HISTORY.exists():
            with open(TRADE_HISTORY, "r") as f:
                history = json.load(f)
        history.append(trade)
        with open(TRADE_HISTORY, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        # TG通知
        msg = (
            f"🚀 *OI+费率信号自动开仓*\n\n"
            f"`{instId}`\n"
            f"方向: 做多\n"
            f"数量: {ORDER_SIZE}张 ({LEVERAGE}x)\n"
            f"入场: {entry_price}\n"
            f"止损: {sl} (-3%)\n"
            f"止盈: {tp} (+10%)\n"
            f"OI涨幅: {signal_data.get('oi_change', 0):.1f}%\n"
            f"费率: {signal_data.get('prev_fr', 0):+.4%} → {signal_data.get('current_fr', 0):+.4%}\n"
            f"持仓: {open_count + 1}/{MAX_POSITIONS}"
        )
        send_tg(msg)
        log(f"  ✅ 开仓成功并已记录")
        return True
        
    except Exception as e:
        log(f"  ❌ 开仓失败: {e}")
        send_tg(f"❌ 自动开仓失败\n{instId}: {e}")
        return False

# ============ 去重 ============
def load_alert_history():
    if ALERT_HISTORY_FILE.exists():
        try:
            return json.loads(ALERT_HISTORY_FILE.read_text())
        except:
            return {}
    return {}

def save_alert_history(history):
    ALERT_HISTORY_FILE.write_text(json.dumps(history))

def is_duplicate(symbol, history):
    if symbol not in history:
        return False
    last_alert = datetime.fromisoformat(history[symbol])
    return (datetime.now() - last_alert).total_seconds() < DEDUP_HOURS * 3600

def mark_alerted(symbol, history):
    history[symbol] = datetime.now().isoformat()
    cutoff = datetime.now() - timedelta(hours=DEDUP_HOURS * 2)
    history = {k: v for k, v in history.items()
               if datetime.fromisoformat(v) > cutoff}
    return history

# ============ 费率快照 ============
def load_fr_snapshot():
    if FR_SNAPSHOT_FILE.exists():
        try:
            return json.loads(FR_SNAPSHOT_FILE.read_text())
        except:
            pass
    return {}

def save_fr_snapshot(snapshot):
    FR_SNAPSHOT_FILE.write_text(json.dumps(snapshot))

# ============ 核心扫描 ============
def scan():
    ts_start = time.time()
    
    try:
        info = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo', timeout=10).json()
        symbols = [s['symbol'] for s in info['symbols']
                   if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    except Exception as e:
        log(f"[ERROR] exchangeInfo: {e}")
        return []
    
    try:
        tickers = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr', timeout=10).json()
        ticker_map = {t['symbol']: t for t in tickers}
    except Exception as e:
        log(f"[ERROR] ticker: {e}")
        return []
    
    active = [s for s in symbols if float(ticker_map.get(s, {}).get('quoteVolume', 0)) > MIN_VOLUME_USDT]
    
    try:
        fr_all = requests.get('https://fapi.binance.com/fapi/v1/premiumIndex', timeout=10).json()
        fr_current = {item['symbol']: float(item['lastFundingRate']) for item in fr_all}
    except:
        fr_current = {}
    
    prev_snapshot = load_fr_snapshot()
    save_fr_snapshot(fr_current)
    
    if not prev_snapshot:
        log(f"首次运行，保存快照，下次开始对比")
        return []
    
    just_turned_negative = []
    for sym in active:
        prev_fr = prev_snapshot.get(sym)
        curr_fr = fr_current.get(sym)
        if prev_fr is None or curr_fr is None:
            continue
        if prev_fr >= 0 and curr_fr < 0:
            just_turned_negative.append(sym)
    
    if not just_turned_negative:
        elapsed = time.time() - ts_start
        log(f"扫描完成: {len(active)}币/{elapsed:.1f}s, 无新转负")
        return []
    
    log(f"发现 {len(just_turned_negative)} 个刚转负，查OI中...")
    
    signals = []
    for sym in just_turned_negative:
        try:
            oi_hist = requests.get('https://fapi.binance.com/futures/data/openInterestHist',
                params={'symbol': sym, 'period': '1h', 'limit': 48}, timeout=10).json()
            
            oi_chg = 0
            segs = []
            oi_rising = False
            if oi_hist and len(oi_hist) >= 12:
                oi_values = [float(x['sumOpenInterestValue']) for x in oi_hist]
                seg_len = len(oi_values) // 4
                if seg_len >= 3:
                    segs = [
                        sum(oi_values[:seg_len]) / seg_len,
                        sum(oi_values[seg_len:seg_len*2]) / seg_len,
                        sum(oi_values[seg_len*2:seg_len*3]) / seg_len,
                        sum(oi_values[seg_len*3:]) / max(1, len(oi_values[seg_len*3:]))
                    ]
                    oi_chg = (segs[3] - segs[0]) / segs[0] * 100 if segs[0] > 0 else 0
                    oi_rising = oi_chg > MIN_OI_CHANGE_PCT
            
            t = ticker_map.get(sym, {})
            signals.append({
                'symbol': sym,
                'price': float(t.get('lastPrice', 0)),
                'price_chg_24h': float(t.get('priceChangePercent', 0)),
                'volume': float(t.get('quoteVolume', 0)),
                'oi_change': oi_chg,
                'oi_segments': segs,
                'oi_rising': oi_rising,
                'current_fr': fr_current.get(sym, 0),
                'prev_fr': prev_snapshot.get(sym, 0),
            })
        except:
            continue
    
    elapsed = time.time() - ts_start
    strong = [s for s in signals if s['current_fr'] < 0 and s.get('oi_rising')]
    log(f"扫描完成: {len(active)}币/{elapsed:.1f}s, 转负{len(signals)}个, OI达标{len(strong)}个")
    return strong

# ============ 主逻辑 ============
def main():
    log("=== 信号扫描+自动跟单 ===")
    signals = scan()
    
    if not signals:
        log("无信号")
        return
    
    history = load_alert_history()
    opened = 0
    
    for s in signals:
        coin = s['symbol'].replace('USDT', '')
        if is_duplicate(coin, history):
            log(f"  {coin} 24h内已推送过，跳过")
            continue
        
        # 自动开仓
        success = auto_open(coin, s)
        if success:
            opened += 1
            history = mark_alerted(coin, history)
        
        if count_open_trades() >= MAX_POSITIONS:
            log(f"持仓已达上限，停止处理后续信号")
            break
    
    save_alert_history(history)
    log(f"本次共开仓 {opened} 个")

if __name__ == '__main__':
    main()
