import os
import time
import pandas as pd
import numpy as np
import requests
from serpapi import GoogleSearch

# ---------------------------------------------------------
# 1. THE 1000 TRADERS FILTERING STRATEGY (Conceptual Pool)
# ---------------------------------------------------------
"""
如果我们要从 1000 个人中选出每天交易 20 次的 Scalpers (剥头皮交易员)，筛选漏斗如下：
Filter 1: Signal-to-Noise Ratio (SNR). 剔除营销号、只喊单现货的 KOL。
Filter 2: Timeframe Keywords. 提取推文中含有 "1m", "5m", "15m", "scalp", "orderflow", "tick" 的账号。
Filter 3: Survivorship. 必须穿越过 2022 年大熊市且依然活跃。
"""

# 精选 40 位通过了 Filter 2 (高频/短线/剥头皮/订单流) 标签的交易员
# 每次抽取 2 位，进行 20 轮进化
SCALPER_POOL = [
    "HsakaTrades", "CryptoKaleo", "gainzy222", "trader1sz", "RookieXBT",
    "Trader_XO", "ColdBloodShill", "TheCryptoDog", "inmortalcrypto", "CryptoTony__",
    "ByzGeneral", "AltcoinGordon", "crypto_birb", "CryptoCapo_", "MacnBTC",
    "SatoshiFlippin", "cryptCred", "LomahCrypto", "Crypto_Ed_NL", "CryptoMichNL",
    "CryptoGodJohn", "devchart", "Nebraskangooner", "TheCryptoCactus", "CryptoNewton",
    "IncomeSharks", "CanteringClark", "CryptoDonAlt", "CryptoCobain", "AngeloBTC",
    "ThinkingCrypto1", "KoroushAK", "rektcapital", "SmartContracter", "CryptoGainz1",
    "Crypto_Chase", "Crypto_McKenna", "Crypto_Macro", "Crypto_BULL_", "Crypto_Core_"
]

# ---------------------------------------------------------
# 2. DATA INGESTION: 5m Klines (15 days = 4320 candles)
# ---------------------------------------------------------
def fetch_5m_klines():
    print("📥 正在拉取 Binance 5m 级别 K线数据 (高频绞肉机战场)...")
    url = "https://fapi.binance.com/fapi/v1/klines"
    all_data = []
    end_time = None
    
    for _ in range(3):
        params = {"symbol": "BTCUSDT", "interval": "5m", "limit": 1500}
        if end_time:
            params["endTime"] = end_time
        try:
            data = requests.get(url, params=params).json()
            if not data: break
            all_data = data + all_data
            end_time = data[0][0] - 1
            time.sleep(0.5)
        except:
            break
            
    cols = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 
            'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
    df = pd.DataFrame(all_data, columns=cols)
    df.drop_duplicates(subset=['Open_time'], inplace=True)
    df.sort_values('Open_time', inplace=True)
    df['Date'] = pd.to_datetime(df['Open_time'], unit='ms')
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = df[col].astype(float)
    return df[['Date', 'Open', 'High', 'Low', 'Close']]

# ---------------------------------------------------------
# 3. THE 20-ROUND EVOLUTION ENGINE
# ---------------------------------------------------------
class ScalperEngine:
    def __init__(self):
        # 初始默认的高频参数
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.ema_fast = 9
        self.ema_slow = 21
        self.sl_pct = 0.005 # 高频默认止损 0.5%
        self.tp_pct = 0.015 # 高频默认止盈 1.5%
        self.best_pnl = -999
        self.api_key = os.getenv("SERPAPI_API_KEY", "")

    def distill_traders_nlp(self, trader1, trader2):
        """
        真实调用 SerpApi，提取这两位交易员最近关于高频/剥头皮的关键词，
        并用来微调（Distill）引擎参数。
        """
        keywords = {"tight": 0, "trend": 0, "bounce": 0, "breakout": 0, "fast": 0}
        
        if self.api_key:
            for t in [trader1, trader2]:
                params = {
                    "engine": "google",
                    "q": f'site:twitter.com/{t} ("scalp" OR "5m" OR "tp" OR "sl" OR "tight")',
                    "api_key": self.api_key,
                    "num": 3
                }
                try:
                    res = GoogleSearch(params).get_dict()
                    if "organic_results" in res:
                        for r in res["organic_results"]:
                            text = (r.get("snippet", "") + r.get("title", "")).lower()
                            if "tight" in text or "sl" in text: keywords["tight"] += 1
                            if "trend" in text or "ema" in text: keywords["trend"] += 1
                            if "bounce" in text or "rsi" in text: keywords["bounce"] += 1
                            if "breakout" in text: keywords["breakout"] += 1
                            if "fast" in text or "scalp" in text: keywords["fast"] += 1
                except Exception as e:
                    pass
        
        # 微调逻辑 (Distillation into Math)
        # 如果提到 tight/fast，缩紧止损止盈，降低均线周期以提高频率
        if keywords["tight"] > keywords["trend"]:
            self.sl_pct = max(0.002, self.sl_pct - 0.001)
            self.tp_pct = max(0.006, self.tp_pct - 0.002)
        else:
            self.sl_pct = min(0.01, self.sl_pct + 0.001)
            self.tp_pct = min(0.03, self.tp_pct + 0.002)
            
        if keywords["fast"] > 0:
            self.ema_fast = max(5, self.ema_fast - 2)
            self.ema_slow = max(13, self.ema_slow - 2)
            
        if keywords["bounce"] > keywords["breakout"]:
            self.rsi_oversold = min(40, self.rsi_oversold + 2)
            self.rsi_overbought = max(60, self.rsi_overbought - 2)

    def run_backtest(self, df):
        # 1. 动量 (EMA)
        df['EMA_F'] = df['Close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['EMA_S'] = df['Close'].ewm(span=self.ema_slow, adjust=False).mean()
        df['Trend'] = np.where(df['EMA_F'] > df['EMA_S'], 1, -1)
        
        # 2. 均值回归 (RSI)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 3. 极高频开仓信号
        df['Signal'] = 0
        df.loc[(df['Trend'] == 1) & (df['RSI'] < self.rsi_oversold), 'Signal'] = 1
        df.loc[(df['Trend'] == -1) & (df['RSI'] > self.rsi_overbought), 'Signal'] = -1
        
        capital = 10000
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(1, len(df)):
            sig = df['Signal'].iloc[i-1]
            price = df['Open'].iloc[i]
            
            if position != 0:
                pnl_pct = (price - entry_price) / entry_price * position
                if pnl_pct <= -self.sl_pct or pnl_pct >= self.tp_pct:
                    capital *= (1 + pnl_pct)
                    trades.append(pnl_pct)
                    position = 0
                    
            if position == 0 and sig != 0:
                position = sig
                entry_price = price
                
        return capital, len(trades), [t for t in trades if t > 0]

# ---------------------------------------------------------
# 4. EXECUTE 20 ROUNDS
# ---------------------------------------------------------
def main():
    df = fetch_5m_klines()
    days = len(df) / 288 # 5m candles per day
    print(f"📊 数据准备完毕: {len(df)} 根 5m K线 (约 {days:.1f} 天)")
    
    engine = ScalperEngine()
    print("\n⚔️ 开始 20 轮『蒸馏 -> 高频回测 -> 参数进化』大逃杀...")
    
    for round_num in range(20):
        t1 = SCALPER_POOL[round_num * 2]
        t2 = SCALPER_POOL[round_num * 2 + 1]
        
        print(f"\n[Round {round_num+1}/20] 蒸馏交易员: @{t1} & @{t2}")
        engine.distill_traders_nlp(t1, t2)
        
        # 跑回测
        final_cap, total_trades, wins = engine.run_backtest(df)
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        pnl = (final_cap - 10000) / 100
        tpd = total_trades / days if days > 0 else 0
        
        print(f"   ⚙️ 进化参数: EMA({engine.ema_fast}/{engine.ema_slow}), RSI({engine.rsi_oversold}/{engine.rsi_overbought}), SL: {engine.sl_pct*100:.1f}%, TP: {engine.tp_pct*100:.1f}%")
        print(f"   📈 战报: 交易 {total_trades} 次 (频率: {tpd:.1f}次/天), 胜率: {win_rate*100:.1f}%, 盈亏: {pnl:.2f}%")

if __name__ == "__main__":
    main()
