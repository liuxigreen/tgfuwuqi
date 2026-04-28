import requests
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# V20 15m/30m 微观清算猎杀 (Liquidity Sweep) 真实回测引擎
# ---------------------------------------------------------

def fetch_klines(symbol, interval, limit=1500):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        res = requests.get(url, params=params, timeout=5).json()
        if type(res) == list and len(res) > 0:
            cols = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
                    'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
            df = pd.DataFrame(res, columns=cols)
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']: df[col] = df[col].astype(float)
            return df
    except Exception:
        pass
    return None

def backtest_liquidity_sweep(df, symbol, interval, rsi_th=20, vol_mult=2.5, sl_pct=0.02, tp_pct=0.03, leverage=3):
    """
    15m/30m 专属的“极端爆仓抄底流”：
    1. RSI 极度超卖 (< 20)
    2. 交易量是过去 20 根 K 线平均值的 2.5 倍以上 (散户被爆仓/强平的天量)
    3. 在这种插针点买入，带 2% 的宽止损(容忍针尖余震)，抢 3% 的快速反弹就跑。
    """
    capital = 10000.0
    position = 0
    entry_price = 0.0
    trades_count = 0
    wins = 0
    fee = 0.0004
    
    op = df['Open'].values
    hi = df['High'].values
    lo = df['Low'].values
    cl = df['Close'].values
    vol = df['Volume'].values
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    
    vol_ma = df['Volume'].rolling(window=20).mean()
    
    # 核心买入信号：RSI极低 + 天量爆仓
    buy_signals = (rsi < rsi_th) & (df['Volume'] > vol_ma * vol_mult)
    sigs = buy_signals.values

    for i in range(1, len(sigs)):
        c_op, c_hi, c_lo = op[i], hi[i], lo[i]

        if position == 1:
            if c_lo <= entry_price * (1 - sl_pct):
                loss_amt = sl_pct * leverage
                capital *= (1 - loss_amt - fee)
                position = 0; trades_count += 1
            elif c_hi >= entry_price * (1 + tp_pct):
                profit_amt = tp_pct * leverage
                capital *= (1 + profit_amt - fee)
                position = 0; trades_count += 1; wins += 1

        if position == 0 and sigs[i-1]:
            position = 1; entry_price = c_op
            capital *= (1 - fee)
            
        if capital <= 100:
            capital = 0
            break

    hours_per_candle = {"15m": 0.25, "30m": 0.5}[interval]
    days_tested = (len(df) * hours_per_candle) / 24
    net_profit = capital - 10000
    win_rate = (wins / trades_count) * 100 if trades_count > 0 else 0
    
    print(f"[{interval:>3}] {symbol:<8} | 测试天数: {days_tested:4.1f}天 | 总开单: {trades_count:3d}次")
    print(f"      胜率: {win_rate:4.1f}% | 最终本金: ${capital:10,.2f} (净赚 ${net_profit:8,.2f})")
    return win_rate, net_profit

if __name__ == "__main__":
    print("="*70)
    print("🩸 [V20] 15m/30m 微观清算猎杀 (Liquidity Sweep) 真实回测")
    print("策略：不追涨杀跌，专捡带血的筹码。RSI<20 + 天量插针买入。")
    print("风控：2%宽止损, 3%止盈, 3倍低杠杆 (防止被余震插死)")
    print("="*70)
    
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "WIFUSDT", "PEPEUSDT"]
    intervals = ["15m", "30m"]

    for sym in symbols:
        print(f"\n💎 猎杀标的: {sym}")
        print("-" * 70)
        for iv in intervals:
            df = fetch_klines(sym, iv, limit=1500) # 约 15-30 天的高频数据
            if df is not None and not df.empty:
                backtest_liquidity_sweep(df, sym, iv)