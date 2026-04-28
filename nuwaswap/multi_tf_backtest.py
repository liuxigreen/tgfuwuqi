import requests
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# V19 多时间级别（4h vs 1h vs 30m）绞肉机验证引擎
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
            for col in ['Open', 'High', 'Low', 'Close']: df[col] = df[col].astype(float)
            return df
    except Exception as e:
        pass
    return None

def backtest_multi_tf(df, symbol, interval):
    capital = 10000.0
    position = 0
    entry_price = 0.0
    trades_count = 0
    wins = 0
    
    sl_pct = 0.0038
    tp_pct = 0.0213
    fee = 0.0004
    leverage = 10
    
    op = df['Open'].values
    hi = df['High'].values
    lo = df['Low'].values
    cl = df['Close'].values
    
    ema_f = df['Close'].ewm(span=8, adjust=False).mean()
    ema_s = df['Close'].ewm(span=100, adjust=False).mean()
    trend = np.where(ema_f > ema_s, 1, -1)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    
    signals = pd.Series(0, index=df.index)
    signals[(trend == 1) & (rsi < 35)] = 1
    signals[(trend == -1) & (rsi > 65)] = -1
    sig = signals.values

    for i in range(1, len(sig)):
        s = sig[i-1]
        c_op, c_hi, c_lo = op[i], hi[i], lo[i]

        if position != 0:
            if position == 1:
                if c_lo <= entry_price * (1 - sl_pct):
                    loss_amt = sl_pct * leverage
                    capital *= (1 - loss_amt - fee)
                    position = 0; trades_count += 1
                elif c_hi >= entry_price * (1 + tp_pct):
                    profit_amt = tp_pct * leverage
                    capital *= (1 + profit_amt - fee)
                    position = 0; trades_count += 1; wins += 1
            elif position == -1:
                if c_hi >= entry_price * (1 + sl_pct):
                    loss_amt = sl_pct * leverage
                    capital *= (1 - loss_amt - fee)
                    position = 0; trades_count += 1
                elif c_lo <= entry_price * (1 - tp_pct):
                    profit_amt = tp_pct * leverage
                    capital *= (1 + profit_amt - fee)
                    position = 0; trades_count += 1; wins += 1

        if position == 0 and s != 0:
            position = s; entry_price = c_op
            capital *= (1 - fee)
            
        if capital <= 100:
            capital = 0
            break
            
    hours_per_candle = {"30m": 0.5, "1h": 1, "4h": 4}[interval]
    days_tested = (len(df) * hours_per_candle) / 24
    daily_trades = trades_count / days_tested if days_tested > 0 else 0
    net_profit = capital - 10000
    daily_profit = net_profit / days_tested if days_tested > 0 else 0
    win_rate = (wins / trades_count) * 100 if trades_count > 0 else 0
    
    print(f"[{interval:>3}] 测试天数: {days_tested:4.1f}天 | 总开单: {trades_count:4d}次 -> 每天开单: {daily_trades:4.1f} 次")
    print(f"      胜率: {win_rate:4.1f}% | 最终本金: ${capital:10,.2f} | 每日均利: ${daily_profit:8,.2f}")
    return daily_trades

if __name__ == "__main__":
    print("="*70)
    print("⏱️ [V19] 多时间级别开单频率与绞肉机真相测试")
    print("固定策略：0.38%止损, 2.13%止盈, 10倍杠杆, 万四手续费")
    print("="*70)
    
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    intervals = ["4h", "1h", "30m"]

    for sym in symbols:
        print(f"\n💎 标的: {sym}")
        print("-" * 70)
        for iv in intervals:
            df = fetch_klines(sym, iv, limit=1500)
            if df is not None and not df.empty:
                backtest_multi_tf(df, sym, iv)
