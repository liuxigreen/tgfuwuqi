import os
import json
import requests
import pandas as pd
import numpy as np
import random
import time

# ---------------------------------------------------------
# 1. 极速读取本地语料库 (合并 V1 到 V9 共 900 人)
# ---------------------------------------------------------
DB_FILES = [
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v2.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v3.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v4.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v5.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v6.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v7.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v8.json",
    "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v9.json"
]

def load_offline_corpus():
    corpus = []
    for f in DB_FILES:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                corpus.extend(json.load(file))
            
    print(f"📚 成功加载【V10 华尔街降维打击语料库】！共计 {len(corpus)} 条顶级实战策略（包含 900 名大V/机构/巨鲸/Degen/华尔街宏观基金基因）")
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
# 3. NUMPY 核心回测引擎 (带严格的手续费摩擦)
# ---------------------------------------------------------
def fast_backtest_numpy_with_fees(open_prices, high_prices, low_prices, close_prices, signals, sl_pct, tp_pct, is_high_freq=False):
    capital = 10000.0
    position = 0
    entry_price = 0.0
    trades_count = 0
    wins = 0

    op = open_prices.values
    hi = high_prices.values
    lo = low_prices.values
    sig = signals.values

    # 严格模拟真实交易环境，万四手续费（对于高频极其致命）
    fee = 0.0004 if is_high_freq else 0.0002

    for i in range(1, len(sig)):
        s = sig[i-1]
        c_op, c_hi, c_lo = op[i], hi[i], lo[i]

        if position != 0:
            if position == 1:
                if c_lo <= entry_price * (1 - sl_pct):
                    capital *= (1 - sl_pct - fee)
                    position = 0; trades_count += 1
                elif c_hi >= entry_price * (1 + tp_pct):
                    capital *= (1 + tp_pct - fee)
                    position = 0; trades_count += 1; wins += 1
            elif position == -1:
                if c_hi >= entry_price * (1 + sl_pct):
                    capital *= (1 - sl_pct - fee)
                    position = 0; trades_count += 1
                elif c_lo <= entry_price * (1 - tp_pct):
                    capital *= (1 + tp_pct - fee)
                    position = 0; trades_count += 1; wins += 1

        if position == 0 and s != 0:
            position = s; entry_price = c_op
            capital *= (1 - fee)

    return capital, trades_count, wins

# ---------------------------------------------------------
# 4. V10 华尔街降维打击大逃杀引擎 (900名交易员, 900轮演化)
# ---------------------------------------------------------
class OfflineEvolutionEngineV10:
    def __init__(self, dfs, corpus):
        self.dfs = dfs
        self.corpus = corpus

        # 继承 V9 基因，并强行重启 5m 和 15m 的测试空间，看华尔街量化能否复活短线
        self.dna = {
            "5m":  {"ema_f": 10, "ema_s": 200, "rsi_os": 25, "rsi_ob": 75, "sl": 0.0050, "tp": 0.0150},
            "15m": {"ema_f": 10, "ema_s": 200, "rsi_os": 25, "rsi_ob": 75, "sl": 0.0050, "tp": 0.0200},
            "30m": {"ema_f": 22, "ema_s": 50,  "rsi_os": 30, "rsi_ob": 70, "sl": 0.0211, "tp": 0.0415},
            "1h":  {"ema_f": 191,"ema_s": 200, "rsi_os": 30, "rsi_ob": 70, "sl": 0.2040, "tp": 0.5285},
            "4h":  {"ema_f": 7,  "ema_s": 100, "rsi_os": 35, "rsi_ob": 65, "sl": 0.0090, "tp": 0.0531}
        }
        self.best_pnl = {"5m": -999, "15m": -999, "30m": -999, "1h": -999, "4h": -999}
        self.best_dna = {k: v.copy() for k, v in self.dna.items()}

    def distill_from_corpus(self):
        """每轮从 900 人语料库中随机抽取 27 条进行解读，引发华尔街宏观漂移"""
        sample = random.sample(self.corpus, min(27, len(self.corpus)))
        mutation = {"wall_street_macro": 0, "retail_degen": 0}

        for item in sample:
            txt = (item.get("snippet", "") + item.get("title", "")).lower()
            if "etf" in txt or "liquidity" in txt or "interest rate" in txt or "macro" in txt or "yield" in txt or "allocation" in txt: 
                mutation["wall_street_macro"] += 1
            if "sniper" in txt or "memecoin" in txt or "moonshot" in txt or "scalp" in txt: 
                mutation["retail_degen"] += 1

        for tf in self.dna.keys():
            p = self.dna[tf]
            noise_sl = random.uniform(-0.001, 0.001)
            noise_tp = random.uniform(-0.002, 0.002)

            # 华尔街宏观思维：大资金、大周期、低频次、高确定性
            if mutation["wall_street_macro"] >= mutation["retail_degen"]:
                p["sl"] = min(0.25, p["sl"] + 0.002 + noise_sl)
                p["tp"] = min(0.70, p["tp"] + 0.005 + noise_tp)
                p["ema_f"] = min(250, p["ema_f"] + 2)
            # 散户 Degen 思维：极高赔率，极大止盈，极速入场
            else:
                p["sl"] = max(0.001, p["sl"] - 0.001 + noise_sl)
                p["tp"] = max(0.010, p["tp"] - 0.001 + noise_tp)
                p["ema_f"] = max(2, p["ema_f"] - 1)

    def eval_timeframe(self, tf):
        df = self.dfs[tf]
        p = self.dna[tf]
        is_hf = tf in ["5m", "15m"]

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

        cap, trades, wins = fast_backtest_numpy_with_fees(df['Open'], df['High'], df['Low'], df['Close'], signals, p["sl"], p["tp"], is_high_freq=is_hf)
        win_rate = wins / trades if trades > 0 else 0
        pnl = (cap - 10000) / 100

        if pnl > self.best_pnl[tf]:
            self.best_pnl[tf] = pnl
            self.best_dna[tf] = p.copy()
        elif random.random() > 0.05: # 95%概率回退，华尔街资本极其厌恶波动，死守极值
            self.dna[tf] = self.best_dna[tf].copy()

        return cap, trades, win_rate, pnl

    def run_900_rounds(self):
        print(f"\n⚔️ 【V10 华尔街降维打击】华尔街宏观基金 vs 散户Degen | 900名大佬 | 900轮极限碰撞")

        for r in range(1, 901):
            self.distill_from_corpus()

            if r % 90 == 0 or r == 1:
                print(f"\n  [Round {r:03d}/900]")
                for tf in self.dna.keys():
                    _, trades, wr, pnl = self.eval_timeframe(tf)
                    best_pnl = self.best_pnl[tf]
                    sl, tp = self.dna[tf]['sl']*100, self.dna[tf]['tp']*100
                    print(f"    - {tf:>3} | 胜率: {wr*100:05.1f}% | 本轮盈亏: {pnl:06.1f}% | 历史最高: {best_pnl:06.1f}% | SL/TP: {sl:05.2f}%/{tp:05.2f}% | 交易数: {trades}")

        print("\n🏆 900 轮终极审判结束！华尔街顶级金融机构智慧结晶的【V10 华尔街之狼基因】(The Wall Street DNA)：")
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

        engine = OfflineEvolutionEngineV10(dfs, corpus)
        engine.run_900_rounds()
