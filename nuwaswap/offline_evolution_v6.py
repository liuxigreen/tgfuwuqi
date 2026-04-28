import os
import json
import requests
import pandas as pd
import numpy as np
import random
import time

# ---------------------------------------------------------
# 1. 极速读取本地语料库 (合并 V1 到 V5 共 500 人)
# ---------------------------------------------------------
DB_FILE_V1 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database.json"
DB_FILE_V2 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v2.json"
DB_FILE_V3 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v3.json"
DB_FILE_V4 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v4.json"
DB_FILE_V5 = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v5.json"

def load_offline_corpus():
    corpus = []
    for f in [DB_FILE_V1, DB_FILE_V2, DB_FILE_V3, DB_FILE_V4, DB_FILE_V5]:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                corpus.extend(json.load(file))
            
    print(f"📚 成功加载【V6 终极大统一语料库】！共计 {len(corpus)} 条顶级实战策略（包含 500 名交易员/机构基因）")
    return corpus

# ---------------------------------------------------------
# 2. 快速 K 线拉取 (缓存到内存) - 5m, 15m, 30m, 1h, 4h
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
# 4. V6 大逃杀引擎 (500名交易员, 500轮演化)
# ---------------------------------------------------------
class OfflineEvolutionEngineV6:
    def __init__(self, dfs, corpus):
        self.dfs = dfs
        self.corpus = corpus

        # 继承 V5 的终极宇宙基因起点
        self.dna = {
            "5m":  {"ema_f": 7,  "ema_s": 100, "rsi_os": 30, "rsi_ob": 70, "sl": 0.0093, "tp": 0.0107},
            "15m": {"ema_f": 5,  "ema_s": 100, "rsi_os": 30, "rsi_ob": 70, "sl": 0.0030, "tp": 0.0100},
            "30m": {"ema_f": 20, "ema_s": 50,  "rsi_os": 30, "rsi_ob": 70, "sl": 0.0162, "tp": 0.0386},
            "1h":  {"ema_f": 5,  "ema_s": 200, "rsi_os": 30, "rsi_ob": 70, "sl": 0.0030, "tp": 0.0100},
            "4h":  {"ema_f": 5,  "ema_s": 100, "rsi_os": 35, "rsi_ob": 65, "sl": 0.0030, "tp": 0.0484}
        }
        self.best_pnl = {"5m": -999, "15m": -999, "30m": -999, "1h": -999, "4h": -999}
        self.best_dna = {k: v.copy() for k, v in self.dna.items()}

    def distill_from_corpus(self):
        """每轮从 500 人语料库中随机抽取 15 条进行多维解读，引发衍生品/现货参数漂移"""
        sample = random.sample(self.corpus, min(15, len(self.corpus)))
        mutation = {"derivatives_hedge": 0, "spot_trend": 0}

        for item in sample:
            txt = (item.get("snippet", "") + item.get("title", "")).lower()
            if "options" in txt or "funding" in txt or "liquidations" in txt or "squeeze" in txt or "arbitrage" in txt: 
                mutation["derivatives_hedge"] += 1
            if "trend" in txt or "hold" in txt or "invest" in txt or "macro" in txt or "swing" in txt: 
                mutation["spot_trend"] += 1

        for tf in self.dna.keys():
            p = self.dna[tf]
            noise_sl = random.uniform(-0.001, 0.001)
            noise_tp = random.uniform(-0.003, 0.003)

            # 衍生品思维：极端防守，吃小波段或者轧空
            if mutation["derivatives_hedge"] >= mutation["spot_trend"]:
                p["sl"] = max(0.002, p["sl"] - 0.001 + noise_sl)
                p["tp"] = max(0.008, p["tp"] - 0.002 + noise_tp)
                p["ema_f"] = max(3, p["ema_f"] - 1)
            # 现货趋势思维：宽止损，大止盈，慢均线
            else:
                p["sl"] = min(0.18, p["sl"] + 0.002 + noise_sl)
                p["tp"] = min(0.50, p["tp"] + 0.005 + noise_tp)
                p["ema_f"] = min(150, p["ema_f"] + 2)

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
        elif random.random() > 0.3: # 70%概率回退到历史最优，保留来之不易的极值
            self.dna[tf] = self.best_dna[tf].copy()

        return cap, trades, win_rate, pnl

    def run_500_rounds(self):
        print(f"\n⚔️ 【V6 终极大一统搏杀启动】5大时间级别 | 500名交易员/机构/衍生品大佬基因 | 500轮极限碰撞")

        for r in range(1, 501):
            self.distill_from_corpus()

            if r % 50 == 0 or r == 1:
                print(f"\n  [Round {r:03d}/500]")
                for tf in self.dna.keys():
                    _, trades, wr, pnl = self.eval_timeframe(tf)
                    best_pnl = self.best_pnl[tf]
                    sl, tp = self.dna[tf]['sl']*100, self.dna[tf]['tp']*100
                    print(f"    - {tf:>3} | 胜率: {wr*100:05.1f}% | 本轮盈亏: {pnl:06.1f}% | 历史最高: {best_pnl:06.1f}% | SL/TP: {sl:05.2f}%/{tp:05.2f}% | 交易数: {trades}")

        print("\n🏆 500 轮终极进化结束！500人智慧结晶的【V6 大一统神之基因】(The Omega DNA)：")
        for tf in self.dna.keys():
            best = self.best_dna[tf]
            print(f"   [{tf:>3}] 极值收益: {self.best_pnl[tf]:.1f}% -> SL: {best['sl']*100:.2f}%, TP: {best['tp']*100:.2f}%, EMA快线: {best['ema_f']}")

if __name__ == "__main__":
    corpus = load_offline_corpus()
    if corpus:
        dfs = {
            "5m": fetch_klines_fast("BTCUSDT", "5m", pages=20),
            "15m": fetch_klines_fast("BTCUSDT", "15m", pages=20),
            "30m": fetch_klines_fast("BTCUSDT", "30m", pages=20),
            "1h": fetch_klines_fast("BTCUSDT", "1h", pages=20),
            "4h": fetch_klines_fast("BTCUSDT", "4h", pages=20)
        }

        engine = OfflineEvolutionEngineV6(dfs, corpus)
        engine.run_500_rounds()
