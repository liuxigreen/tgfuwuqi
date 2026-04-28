#!/usr/bin/env python3
"""
OI×OKX 自动下单脚本
运行模式：OI信号直下（scanner调用，--oi-only）：无确认，直接市价开仓+TP/SL
"""
import subprocess, json, time, sys, os, requests, argparse
from datetime import datetime

# ========== 配置 ==========
OKX_PROFILE = "demo"
OKX_LEVERAGE = "10"
TG_BOT_TOKEN=os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID   = os.getenv("TG_CHAT_ID", "[TG_CHAT_ID_REDACTED]")
LOG_FILE     = "/root/.hermes/agenthansa/logs/oi_okx_auto_trade.log"
TRADE_HISTORY = "/root/.hermes/agenthansa/trade_history.json"

# ========== 工具函数 ==========
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def tg_notify(text):
    pass  # TG 通知已禁用

def save_trade(record):
    """写入交易记录"""
    try:
        history = []
        if os.path.exists(TRADE_HISTORY):
            try:
                history = json.loads(open(TRADE_HISTORY).read())
            except:
                history = []
        record["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "open_time" not in record:
            record["open_time"] = datetime.now().isoformat()
        history.append(record)
        # 保留最近200条
        history = history[-200:]
        with open(TRADE_HISTORY, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"保存交易记录失败: {e}")

SYMBOL_SIZE_MAP = {
    "BTCUSDT": "0.01",
    "ETHUSDT": "0.01",
    "SOLUSDT": "0.01",
    "DOGEUSDT": "0.01",
    "XRPUSDT": "0.01",
    "ADAUSDT": "0.1",
    "AVAXUSDT": "0.1",
    "BNBUSDT": "1",
    "DOTUSDT": "1",
    "LINKUSDT": "0.1",
}

def run_okx(args, timeout=15):
    cmd = ["okx", "--json"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "OKX_PROFILE": OKX_PROFILE})
        out = r.stdout.strip()
        # 去掉 npm update 提示，提取 JSON
        json_start = -1
        for i, ch in enumerate(out):
            if ch in ('{', '['):
                json_start = i
                break
        if json_start >= 0:
            try:
                parsed = json.loads(out[json_start:])
                if isinstance(parsed, list):
                    return {"data": parsed}
                return parsed
            except json.JSONDecodeError:
                pass
        # 非 JSON 成功响应
        if "Order placed" in out or "(OK)" in out or "closed" in out.lower():
            return {"raw": out, "ok": True}
        return {"raw": out, "stderr": r.stderr, "rc": r.returncode}
    except Exception as e:
        return {"error": str(e)}

# ========== OKX仓位/下单 ==========
def get_positions(instId=None):
    result = run_okx(["swap", "positions", "--instId", instId] if instId else ["swap", "positions"])
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return []

def set_leverage(instId, lever=OKX_LEVERAGE):
    run_okx(["swap", "leverage", "--instId", instId, "--lever", lever, "--mgnMode", "cross"])

def place_order(instId, side, size="0.01", sl_pct=0.0038, tp_pct=0.0213):
    """市价开仓+TP/SL"""
    posSide = "long" if side == "buy" else "short"
    # 先查当前价格
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={instId.replace('-SWAP','')}"
        price = float(requests.get(url, timeout=5).json()['price'])
    except:
        price = None

    sl = price * (1 - sl_pct) if price else None
    tp = price * (1 + tp_pct) if price else None

    args = [
        "swap", "place",
        "--instId", instId,
        "--side", side,
        "--ordType", "market",
        "--sz", size,
        "--tdMode", "cross",
        "--posSide", posSide,
    ]
    if sl:
        args += ["--slTriggerPx", str(sl), "--slOrdPx=-1"]
    if tp:
        args += ["--tpTriggerPx", str(tp), "--tpOrdPx=-1"]

    result = run_okx(args)
    return result, price, sl, tp

# ========== OI信号直下 ==========
def oi_direct_trade(instId, side, size):
    log(f"=== OI直下 {instId} {side} ===")
    set_leverage(instId)
    result, price, sl, tp = place_order(instId, side, size)
    if isinstance(result, dict):
        # JSON格式
        if "data" in result:
            data = result.get("data", [])
            if data and data[0].get("sCode") == "0":
                ordId = data[0].get("ordId", "?")
                log(f"  ✅ OI开仓成功 {instId} {side} @ {price}  SL:{sl}  TP:{tp}  ordId={ordId}")
                save_trade({
                    "strategy": "OI",
                    "symbol": instId,
                    "side": side,
                    "entry_price": price,
                    "sl": sl,
                    "tp": tp,
                    "size": size,
                    "status": "open",
                    "ordId": ordId,
                })
                return True
            else:
                err = (data[0].get("sMsg") if data else result.get("raw", "?"))
                log(f"  ❌ OI开仓失败: {err}")
        # 纯文本OK响应
        elif result.get("ok"):
            log(f"  ✅ OI开仓成功 {instId} {side} (纯文本响应)")
            save_trade({
                "strategy": "OI",
                "symbol": instId,
                "side": side,
                "entry_price": price,
                "sl": sl,
                "tp": tp,
                "size": size,
                "status": "open",
                "ordId": "manual",
            })
            return True
        else:
            log(f"  ❌ OI开仓失败: {result.get('raw', result)}")
    return False

# ========== 主入口 ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--oi-only", action="store_true",
                        help="OI信号直下模式（scanner调用）")
    parser.add_argument("--instId", default="", help="合约如 BTC-USDT-SWAP")
    parser.add_argument("--side", default="buy", help="buy/sell")
    parser.add_argument("--size", default="0.01", help="仓位大小")
    args = parser.parse_args()

    if args.oi_only:
        if not args.instId:
            log("模式1需要 --instId")
            sys.exit(1)
        oi_direct_trade(args.instId, args.side, args.size)
    else:
        log("请使用 --oi-only 模式")
        sys.exit(1)
