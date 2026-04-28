#!/usr/bin/env python3
"""
热度做多雷达 v2 — 热度+费率+OI 三维扫描

核心逻辑（拉哪模式）：
1. 热度先行 → CG热搜+放量=资金涌入信号
2. 负费率=空头燃料，庄家拉盘爆空单
3. OI暴涨=大资金建仓=即将拉盘

单策略：发现热度→小仓做多→严格止损→拿住赢家

数据源：币安合约API + CoinGecko Trending（零成本）
"""

import json
import os
import sys
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from square_heat import get_square_heat

# === 加载 .env ===
env_file = Path(__file__).parent / ".env.oi"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# === 配置 ===
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "YOUR_CHAT_ID")
FAPI = "https://fapi.binance.com"

# 热度历史记录（用于检测首次上榜）
HEAT_HISTORY_FILE = Path(__file__).parent / "heat_history.json"

# 热度参数
VOL_SURGE_MULT = 2.5     # 成交量放大2.5倍以上=放量
MIN_VOL_USD = 20_000_000  # 日均成交>$20M才检测放量

# OI异动参数
MIN_OI_DELTA_PCT = 3.0    # OI变化至少3%
MIN_OI_USD = 2_000_000    # 最低OI门槛 $2M


def api_get(endpoint, params=None):
    """币安API请求"""
    url = f"{FAPI}{endpoint}"
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                time.sleep(2)
            else:
                return None
        except:
            time.sleep(1)
    return None


def format_usd(v):
    if v >= 1e9: return f"${v/1e9:.1f}B"
    if v >= 1e6: return f"${v/1e6:.1f}M"
    if v >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def mcap_str(v):
    if v >= 1e9: return f"${v/1e9:.1f}B"
    if v >= 1e6: return f"${v/1e6:.0f}M"
    if v >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def send_telegram(text):
    """发送TG消息"""
    if not TG_BOT_TOKEN:
        print("\n[TG] No token, stdout:\n")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

    # 分段发送（TG限制4096字）
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > 3800:
            chunks.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        chunks.append(current)

    for chunk in chunks:
        try:
            resp = requests.post(url, json={
                "chat_id": TG_CHAT_ID,
                "text": chunk,
                "parse_mode": "Markdown"
            }, timeout=10)
            if resp.status_code == 200:
                print(f"[TG] Sent ✓ ({len(chunk)} chars)")
            else:
                # Markdown失败就用纯文本
                resp2 = requests.post(url, json={
                    "chat_id": TG_CHAT_ID,
                    "text": chunk.replace("*", "").replace("_", ""),
                }, timeout=10)
                print(f"[TG] Sent plain ({'✓' if resp2.status_code == 200 else '✗'})")
        except Exception as e:
            print(f"[TG] Error: {e}")
        time.sleep(0.5)


def main():
    print(f"🔥 热度做多雷达 v2 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 全市场行情+费率
    tickers_raw = api_get("/fapi/v1/ticker/24hr")
    premiums_raw = api_get("/fapi/v1/premiumIndex")

    if not tickers_raw or not premiums_raw:
        print("❌ API失败")
        return

    ticker_map = {}
    for t in tickers_raw:
        if t["symbol"].endswith("USDT"):
            ticker_map[t["symbol"]] = {
                "px_chg": float(t["priceChangePercent\