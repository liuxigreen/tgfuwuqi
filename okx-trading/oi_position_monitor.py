#!/usr/bin/env python3
"""
OKX 仓位监控 + 自动平仓
每分钟运行：检查持仓是否触发 SL/TP，触发则市价平仓
"""
import subprocess, json, time, sys, os, requests
from datetime import datetime

OKX_PROFILE = "demo"
TG_BOT_TOKEN=os.getenv("AGENTHANSA_TELEGRAM_TOKEN", "")
TG_CHAT_ID = os.getenv("AGENTHANSA_TELEGRAM_CHAT_ID", "")
TRADE_HISTORY = "/root/.hermes/agenthansa/trade_history.json"
LOG_FILE = "/root/.hermes/agenthansa/logs/oi_position_monitor.log"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def tg_notify(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            'chat_id': TG_CHAT_ID,
            'text': text,
            'parse_mode': 'Markdown'
        }, timeout=10)
        if resp.status_code != 200:
            requests.post(url, json={'chat_id': TG_CHAT_ID, 'text': text}, timeout=10)
    except Exception as e:
        log(f"[TG] 失败: {e}")

def run_okx(args, timeout=15):
    cmd = ["okx", "--json"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "OKX_PROFILE": OKX_PROFILE})
        out = r.stdout.strip()
        try:
            parsed = json.loads(out)
            if isinstance(parsed, list):
                return {"data": parsed}
            return parsed
        except:
            return {"raw": out, "ok": "(OK)" in out or "closed" in out.lower()}
    except Exception as e:
        return {"error": str(e)}

def get_positions():
    result = run_okx(["--demo", "swap", "positions"])
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    if isinstance(result, dict) and "error" in result:
        log(f"  [OKX错误] {result['error']}")
    return []

def get_current_price(instId):
    result = run_okx(["--demo", "market", "ticker", instId])
    if isinstance(result, dict) and "data" in result and result["data"]:
        return float(result["data"][0]["last"])
    return None

def close_position(instId, posSide, mgnMode="cross"):
    result = run_okx(["--demo", "swap", "close", "--instId", instId, "--mgnMode", mgnMode, "--posSide", posSide])
    return result

def update_trade(symbol, updates):
    try:
        history = []
        if os.path.exists(TRADE_HISTORY):
            with open(TRADE_HISTORY, "r") as f:
                history = json.load(f)
        for i in range(len(history)-1, -1, -1):
            t = history[i]
            if t.get("symbol") == symbol and t.get("status") == "open":
                history[i].update(updates)
                break
        with open(TRADE_HISTORY, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"更新记录失败: {e}")

def monitor():
    log("=== 仓位监控 ===")
    positions = get_positions()
    if not positions:
        log("无持仓")
        return

    for pos in positions:
        instId = pos.get("instId", "")
        posSide = pos.get("posSide", "")
        avail = pos.get("availPos", "0")
        if not avail or float(avail) <= 0:
            continue

        history = []
        if os.path.exists(TRADE_HISTORY):
            with open(TRADE_HISTORY, "r") as f:
                history = json.load(f)

        trade = None
        for t in reversed(history):
            if t.get("symbol") == instId and t.get("status") == "open":
                trade = t
                break

        if not trade:
            log(f"  {instId} 持仓中，但无对应开仓记录")
            continue

        sl = trade.get("sl")
        tp = trade.get("tp")
        entry = trade.get("entry_price")
        side = trade.get("side")
        strategy = trade.get("strategy", "?")

        price = get_current_price(instId)
        if price is None:
            log(f"  获取 {instId} 价格失败")
            continue

        log(f"  {instId} {side} 持仓: 入场={entry} 当前={price} SL={sl} TP={tp}")

        triggered = False
        reason = ""
        if side == "buy":
            if sl and price <= float(sl):
                triggered = True
                reason = f"触发止损 SL={sl}"
            elif tp and price >= float(tp):
                triggered = True
                reason = f"触发止盈 TP={tp}"
        elif side == "sell":
            if sl and price >= float(sl):
                triggered = True
                reason = f"触发止损 SL={sl}"
            elif tp and price <= float(tp):
                triggered = True
                reason = f"触发止盈 TP={tp}"

        if triggered:
            log(f"  🚨 {reason}，市价平仓...")
            tg_notify(f"🚨 {strategy}信号\n{instId}\n{reason}\n当前价: {price}")
            result = close_position(instId, posSide)
            if isinstance(result, dict):
                ok = False
                if result.get("data") and isinstance(result["data"], list):
                    ok = True
                elif result.get("ok"):
                    ok = True

                if ok:
                    pnl = None
                    pnl_pct = None
                    if entry:
                        size = float(trade.get("size", "0.01"))
                        if side == "buy":
                            pnl = (price - float(entry)) * size
                        else:
                            pnl = (float(entry) - price) * size
                        leverage = trade.get("lever", 10)
                        margin = float(entry) * size / leverage
                        pnl_pct = round(pnl / margin * 100, 2) if margin else None
                    log(f"  ✅ 平仓成功 盈亏={pnl} 盈亏率={pnl_pct}%")
                    update_trade(instId, {
                        "status": "closed",
                        "close_price": price,
                        "pnl": round(pnl, 4) if pnl else None,
                        "pnl_pct": pnl_pct,
                        "close_time": datetime.now().isoformat()
                    })
                    tg_notify(f"✅ 平仓成功\n{instId} {reason}\n盈亏: {pnl:.4f} USDT ({pnl_pct}%)")
                else:
                    err = result.get("raw", result.get("error", "?"))
                    log(f"  ❌ 平仓失败: {err}")
                    tg_notify(f"❌ 平仓失败\n{instId}: {err}")
            else:
                log(f"  ✅ 平仓成功 (纯文本)")
                update_trade(instId, {"status": "closed", "close_price": price, "close_time": datetime.now().isoformat()})

if __name__ == "__main__":
    monitor()
