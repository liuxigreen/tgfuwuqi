import os
import json
import requests
import pandas as pd
import numpy as np
import random
import time

# ---------------------------------------------------------
# 1. 极速读取本地语料库 (Zero API Latency)
# ---------------------------------------------------------
DB_FILE = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database.json"

def load_offline_corpus():
    if not os.path.exists(DB_FILE):
        print(f"❌ 找不到本地语料库 {DB_FILE}！请先运行 ETL 脚本。")
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------
# 2. 快速 K 线拉取 (缓存到内存)
# ---------------------------------------------------------
def fetch_klines_fast(symbol="BTCUSDT", interval="30m", pages=20):
    print(f"📥 正在缓存 {symbol} [{interval}] 历史 K 线 (目标: {pages * 1500} 根)...")
    url = "https://fapi.binance.com/fapi/v1/klines"
    all_data = []
    end_time = None
    
    for i in range(pages):
        params = {"symbol": symbol, "interval": interval, "limit": 1500}
        if end_time: params["endTime"] = end_time
        try:
            res = requests.get(url, params=params).json()
            if not res or type(res) != list: break
            all_data = res + all_data
            end_time = res[0][0] - 1
            time.sleep(0.1) # 内存拉取，稍微快一点
        except: break
            
    cols = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 
            'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
    df = pd.DataFrame(all_data, columns=cols)
    df.drop_duplicates(subset=['Open_time'], inplace=True)
    df.sort_values('Open_time', inplace=True)
    for col in ['Open', 'High', 'Low', 'Close']: df[col] = df[col].astype(float)
    return df

# ---------------------------------------------------------
# 3. NUMPY 核心回测引擎 (毫秒级)
# ---------------------------------------------------------
def fast_backtest_numpy(open_prices, high_prices, low_prices, close_prices, signals, sl_pct, tp_pct):
    capital = 10000.0
    position = 0
    entry_price = 0.0
    trades_count = 0
    wins = 0
    
    op = open_prices.values
    hi = high_prices.values
    lo = low_prices.values
    sig = signals.values
    
    for i in range(1, len(sig)):
        s = sig[i-1]
        c_op, c_hi, c_lo = op[i], hi[i], lo[i]
        
        if position != 0:
            if position == 1:
                if c_lo <= entry_price * (1 - sl_pct):
                    capital *= (1 - sl_pct)
                    position = 0; trades_count += 1
                elif c_hi >= entry_price * (1 + tp_pct):
                    capital *= (1 + tp_pct)
                    position = 0; trades_count += 1; wins += 1
            elif position == -1:
                if c_hi >= entry_price * (1 + sl_pct):
                    capital *= (1 - sl_pct)
                    position = 0; trades_count += 1
                elif c_lo <= entry_price * (1 - tp_pct):
                    capital *= (1 + tp_pct)
                    position = 0; trades_count += 1; wins += 1
                    
        if position == 0 and s != 0:
            position = s; entry_price = c_op
            
    return capital, trades_count, wins

# ---------------------------------------------------------
# 4. 100 轮达尔文大逃杀引擎 (The 100-Round Local Crucible)
# ---------------------------------------------------------
class OfflineEvolutionEngine:
    def __init__(self, df_5m, df_15m, df_30m, corpus):
        self.dfs = {"5m": df_5m, "15m": df_15m, "30m": df_30m}
        self.corpus = corpus
        
        # 初始基因 (第 0 轮)
        self.dna = {
            "5m":  {"ema_f": 9, "ema_s": 21, "rsi_os": 30, "rsi_ob": 70, "sl": 0.005, "tp": 0.015},
            "15m": {"ema_f": 13, "ema_s": 34, "rsi_os": 30, "rsi_ob": 70, "sl": 0.010, "tp": 0.030},
            "30m": {"ema_f": 20, "ema_s": 50, "rsi_os": 30, "rsi_ob": 70, "sl": 0.015, "tp": 0.045}
        }
        self.best_pnl = {"5m": -999, "15m": -999, "30m": -999}
        self.best_dna = {k: v.copy() for k, v in self.dna.items()}

    def distill_from_corpus(self):
        """每轮从本地 37 条真实语料中随机抽取 3 条进行解读，引发参数漂移"""
        sample = random.sample(self.corpus, 3)
        mutation = {"tight": 0, "wide": 0}
        
        for item in sample:
            txt = (item.get("snippet", "") + item.get("title", "")).lower()
            if "tight" in txt or "scalp" in txt or "fast" in txt or "stop" in txt: mutation["tight"] += 1
            if "wide" in txt or "swing" in txt or "patient" in txt or "target" in txt: mutation["wide"] += 1
            
        for tf in ["5m", "15m", "30m"]:
            p = self.dna[tf]
            # 引入极小的随机变异，模拟市场的不可测性 (Noise)
            noise_sl = random.uniform(-0.001, 0.001)
            noise_tp = random.uniform(-0.002, 0.002)
            
            if mutation["tight"] >= mutation["wide"]:
                p["sl"] = max(0.002, p["sl"] - 0.001 + noise_sl)
                p["tp"] = max(0.006, p["tp"] - 0.002 + noise_tp)
                p["ema_f"] = max(5, p["ema_f"] - 1)
            else:
                p["sl"] = min(0.03, p["sl"] + 0.001 + noise_sl)
                p["tp"] = min(0.09, p["tp"] + 0.002 + noise_tp)
                p["ema_f"] = min(30, p["ema_f"] + 1)

    def eval_timeframe(self, tf):
        df = self.dfs[tf]
        p = self.dna[tf]
        
        ema_f = df['Close'].ewm(span=p["ema_f"], adjust=False).mean()
        ema_s = df['Close'].ewm(span=p["ema_s"], adjust=False).mean()
        trend = np.where(ema_f > ema_s, 1, -1)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        signals = pd.Series(0, index=df.index)
        signals[(trend == 1) & (rsi < p["rsi_os"])] = 1
        signals[(trend == -1) & (rsi > p["rsi_ob"])] = -1
        
        cap, trades, wins = fast_backtest_numpy(df['Open'], df['High'], df['Low'], df['Close'], signals, p["sl"], p["tp"])
        win_rate = wins / trades if trades > 0 else 0
        pnl = (cap - 10000) / 100
        
        # 优胜劣汰：只有产生了更高 PnL 的基因才会被保留
        if pnl > self.best_pnl[tf]:
            self.best_pnl[tf] = pnl
            self.best_dna[tf] = p.copy()
            
        # 回退机制：如果本轮变异导致大亏，有 50% 概率退回历史最优基因
        elif random.random() > 0.5:
            self.dna[tf] = self.best_dna[tf].copy()
            
        return cap, trades, win_rate, pnl

    def run_100_rounds(self):
        print(f"\n⚔️ 【离线极速进化启动】0 API 延迟 | 3 大时间级别 | 100 轮大逃杀")
        
        for r in range(1, 101):
            self.distill_from_corpus()
            
            # 每 10 轮打印一次战报（避免刷屏）
            if r % 10 == 0 or r == 1:
                print(f"\n  [Round {r:03d}/100]")
                for tf in ["5m", "15m", "30m"]:
                    _, trades, wr, pnl = self.eval_timeframe(tf)
                    # 打印这轮的实时成绩，以及该级别历史打出的最高 PnL
                    best_pnl = self.best_pnl[tf]
                    sl, tp = self.dna[tf]['sl']*100, self.dna[tf]['tp']*100
                    print(f"    - {tf} | 胜率: {wr*100:05.1f}% | 本轮盈亏: {pnl:06.1f}% | 历史最高: {best_pnl:06.1f}% | SL/TP: {sl:04.1f}%/{tp:04.1f}% | 交易数: {trades}")
                    
        print("\n🏆 100 轮进化结束！以下是存活下来的最强基因 (The Apex DNA)：")
        for tf in ["5m", "15m", "30m"]:
            best = self.best_dna[tf]
            print(f"   [{tf}] 极值收益: {self.best_pnl[tf]:.1f}% -> SL: {best['sl']*100:.1f}%, TP: {best['tp']*100:.1f}%, EMA快线: {best['ema_f']}")

if __name__ == "__main__":
    corpus = load_offline_corpus()
    if corpus:
        # 为了极速，我们各拉取 20 页 (约 30000 根 K线)
        df_5m = fetch_klines_fast("BTCUSDT", "5m", pages=20)
        df_15m = fetch_klines_fast("BTCUSDT", "15m", pages=20)
        df_30m = fetch_klines_fast("BTCUSDT", "30m", pages=20)
        
        engine = OfflineEvolutionEngine(df_5m, df_15m, df_30m, corpus)
        engine.run_100_rounds()
