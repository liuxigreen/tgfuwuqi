import os
import json
import requests
import pandas as pd
import numpy as np
import random
import time

# ---------------------------------------------------------
# 1. 极速读取本地语料库 (Zero API Latency, 合并 V1, V2 和 V3 共 300 人)
# ---------------------------------------------------------
DB_FILE_V1 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database.json"
DB_FILE_V2 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v2.json"
DB_FILE_V3 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v3.json"

def load_offline_corpus():
    corpus = []
    if os.path.exists(DB_FILE_V1):
        with open(DB_FILE_V1, "r", encoding="utf-8") as f:
            corpus.extend(json.load(f))
    if os.path.exists(DB_FILE_V2):
        with open(DB_FILE_V2, "r", encoding="utf-8") as f:
            corpus.extend(json.load(f))
    if os.path.exists(DB_FILE_V3):
        with open(DB_FILE_V3, "r", encoding="utf-8") as f:
            corpus.extend(json.load(f))
            
    print(f"📚 成功加载终极合并语料库！共计 {len(corpus)} 条顶级交易员策略（包含 300 名交易员基因）")
    return corpus

# ---------------------------------------------------------
# 2. 快速 K 线拉取 (缓存到内存) - 重点获取 30m, 1h, 4h
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
            time.sleep(0.1) 
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
# 4. V4 大逃杀引擎 (30m, 1h, 4h 宏观狙击)
# ---------------------------------------------------------
class OfflineEvolutionEngineV4:
    def __init__(self, dfs, corpus):
        self.dfs = dfs
        self.corpus = corpus

        # 初始基因，放弃 5m 和 15m，专注大周期
        # 4h 周期初始参数给得更宽，以适应宏观波动
        self.dna = {
            "30m": {"ema_f": 22, "ema_s": 50, "rsi_os": 30, "rsi_ob": 70, "sl": 0.0175, "tp": 0.0465},
            "1h":  {"ema_f": 51, "ema_s": 200, "rsi_os": 30, "rsi_ob": 70, "sl": 0.0516, "tp": 0.1501},
            "4h":  {"ema_f": 20, "ema_s": 100, "rsi_os": 35, "rsi_ob": 65, "sl": 0.0800, "tp": 0.2500}
        }
        self.best_pnl = {"30m": -999, "1h": -999, "4h": -999}
        self.best_dna = {k: v.copy() for k, v in self.dna.items()}

    def distill_from_corpus(self):
        """每轮从 300 人语料库中随机抽取 10 条进行宏观解读，引发参数漂移"""
        sample = random.sample(self.corpus, min(10, len(self.corpus)))
        mutation = {"macro": 0, "micro": 0}

        for item in sample:
            txt = (item.get("snippet", "") + item.get("title", "")).lower()
            # 强化宏观、趋势词汇的提取
            if "macro" in txt or "trend" in txt or "hold" in txt or "invest" in txt or "cycle" in txt or "long" in txt: 
                mutation["macro"] += 1
            if "scalp" in txt or "fast" in txt or "stop" in txt or "short" in txt or "day" in txt: 
                mutation["micro"] += 1

        for tf in self.dna.keys():
            p = self.dna[tf]
            noise_sl = random.uniform(-0.002, 0.002)
            noise_tp = random.uniform(-0.005, 0.005)

            if mutation["micro"] >= mutation["macro"]:
                # 偏短线思维，收紧止损止盈，加快均线
                p["sl"] = max(0.005, p["sl"] - 0.002 + noise_sl)
                p["tp"] = max(0.015, p["tp"] - 0.005 + noise_tp)
                p["ema_f"] = max(5, p["ema_f"] - 2)
            else:
                # 偏宏观思维，放宽止损止盈，放慢均线以过滤噪音
                p["sl"] = min(0.15, p["sl"] + 0.002 + noise_sl)
                p["tp"] = min(0.40, p["tp"] + 0.005 + noise_tp)
                p["ema_f"] = min(100, p["ema_f"] + 2)

    def eval_timeframe(self, tf):
        df = self.dfs[tf]
        p = self.dna[tf]

        ema_f_series = df['Close'].ewm(span=p["ema_f"], adjust=False).mean()
        ema_s_series = df['Close'].ewm(span=p["ema_s"], adjust=False).mean()
        trend = np.where(ema_f_series > ema_s_series, 1, -1)

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

        if pnl > self.best_pnl[tf]:
            self.best_pnl[tf] = pnl
            self.best_dna[tf] = p.copy()
        elif random.random() > 0.5: # 50%概率回退到历史最优，避免进化崩溃
            self.dna[tf] = self.best_dna[tf].copy()

        return cap, trades, win_rate, pnl

    def run_300_rounds(self):
        print(f"\n⚔️ 【V4 宏观大逃杀启动】专注 30m, 1h, 4h | 300名顶级交易员基因碰撞")

        for r in range(1, 301):
            self.distill_from_corpus()

            if r % 30 == 0 or r == 1:
                print(f"\n  [Round {r:03d}/300]")
                for tf in self.dna.keys():
                    _, trades, wr, pnl = self.eval_timeframe(tf)
                    best_pnl = self.best_pnl[tf]
                    sl, tp = self.dna[tf]['sl']*100, self.dna[tf]['tp']*100
                    print(f"    - {tf:>3} | 胜率: {wr*100:05.1f}% | 本轮盈亏: {pnl:06.1f}% | 历史最高: {best_pnl:06.1f}% | SL/TP: {sl:05.2f}%/{tp:05.2f}% | 交易数: {trades}")

        print("\n🏆 300 轮宏观进化结束！300名交易员智慧结晶的终极大周期基因 (The Macro Apex DNA)：")
        for tf in self.dna.keys():
            best = self.best_dna[tf]
            print(f"   [{tf:>3}] 极值收益: {self.best_pnl[tf]:.1f}% -> SL: {best['sl']*100:.2f}%, TP: {best['tp']*100:.2f}%, EMA快线: {best['ema_f']}")

if __name__ == "__main__":
    corpus = load_offline_corpus()
    if corpus:
        dfs = {
            "30m": fetch_klines_fast("BTCUSDT", "30m", pages=20),
            "1h": fetch_klines_fast("BTCUSDT", "1h", pages=20),
            "4h": fetch_klines_fast("BTCUSDT", "4h", pages=20) # 4h 级别，20页约 3 万根K线，跨越非常长的宏观周期
        }

        engine = OfflineEvolutionEngineV4(dfs, corpus)
        engine.run_300_rounds()
