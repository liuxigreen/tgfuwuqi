import requests
import pandas as pd
import numpy as np
import time

# ---------------------------------------------------------
# 女娲终极定海神针测试：3年全周期横向对比 (1H vs 4H)
# 策略A：V17 宏观剥头皮 (EMA趋势+RSI回踩+极窄止损)
# 策略B：V20 清算猎杀 (极度超卖+天量插针+均值回归)
# ---------------------------------------------------------

def fetch_long_term_klines(symbol, interval, chunks=8):
    """
    为了绕过单次 1500 根的限制，循环拉取更长时间的数据。
    chunks=8: 对于 4H 相当于 8*1000 = 8000根 (约 1333天，近3.6年)
              对于 1H 相当于 8*1000 = 8000根 (约 333天，近1年)
    """
    df_list = []
    end_time = None
    url = "https://fapi.binance.com/fapi/v1/klines"
    
    for _ in range(chunks):
        params = {"symbol": symbol, "interval": interval, "limit": 1000}
        if end_time:
            params['endTime'] = end_time
        try:
            res = requests.get(url, params=params, timeout=5).json()
            if not res: break
            cols = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
                    'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
            df_temp = pd.DataFrame(res, columns=cols)
            df_list.append(df_temp)
            # 获取最早一根 K 线的开盘时间，减 1 毫秒作为下一次请求的 endTime
            end_time = res[0][0] - 1
            time.sleep(0.2)
        except Exception:
            break
            
    if not df_list: return None
    
    # 倒序拼接并去重
    df_final = pd.concat(df_list[::-1]).drop_duplicates(subset=['Open_time']).reset_index(drop=True)
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df_final[col] = df_final[col].astype(float)
    return df_final

def backtest_strategy_A_trend_scalp(df, interval, leverage=10):
    """策略 A: 顺大势，逆小势，极窄止损 0.38%，止盈 2.13%"""
    capital = 10000.0
    position = 0; entry_price = 0.0
    trades_count = 0; wins = 0
    sl_pct = 0.0038; tp_pct = 0.0213; fee = 0.0004
    
    op, hi, lo, cl = df['Open'].values, df['High'].values, df['Low'].values, df['Close'].values
    
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
        if position == 1:
            if c_lo <= entry_price * (1 - sl_pct):
                capital *= (1 - sl_pct*leverage - fee); position = 0; trades_count += 1
            elif c_hi >= entry_price * (1 + tp_pct):
                capital *= (1 + tp_pct*leverage - fee); position = 0; trades_count += 1; wins += 1
        elif position == -1:
            if c_hi >= entry_price * (1 + sl_pct):
                capital *= (1 - sl_pct*leverage - fee); position = 0; trades_count += 1
            elif c_lo <= entry_price * (1 - tp_pct):
                capital *= (1 + tp_pct*leverage - fee); position = 0; trades_count += 1; wins += 1
        if position == 0 and s != 0:
            position = s; entry_price = c_op; capital *= (1 - fee)
        if capital <= 100: capital = 0; break

    wr = (wins / trades_count * 100) if trades_count > 0 else 0
    return capital, trades_count, wr

def backtest_strategy_B_liquidity_sweep(df, interval, leverage=3):
    """策略 B: 不看趋势，只看血迹。RSI<20 + 2.5倍天量。止损 2%，止盈 3%"""
    capital = 10000.0
    position = 0; entry_price = 0.0
    trades_count = 0; wins = 0
    sl_pct = 0.02; tp_pct = 0.03; fee = 0.0004
    
    op, hi, lo, cl, vol = df['Open'].values, df['High'].values, df['Low'].values, df['Close'].values, df['Volume'].values
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    
    vol_ma = df['Volume'].rolling(window=20).mean()
    buy_signals = (rsi < 20) & (df['Volume'] > vol_ma * 2.5)
    sigs = buy_signals.values

    for i in range(1, len(sigs)):
        c_op, c_hi, c_lo = op[i], hi[i], lo[i]
        if position == 1:
            if c_lo <= entry_price * (1 - sl_pct):
                capital *= (1 - sl_pct*leverage - fee); position = 0; trades_count += 1
            elif c_hi >= entry_price * (1 + tp_pct):
                capital *= (1 + tp_pct*leverage - fee); position = 0; trades_count += 1; wins += 1
        if position == 0 and sigs[i-1]:
            position = 1; entry_price = c_op; capital *= (1 - fee)
        if capital <= 100: capital = 0; break

    wr = (wins / trades_count * 100) if trades_count > 0 else 0
    return capital, trades_count, wr

if __name__ == "__main__":
    print("="*80)
    print("🏆 [终极海量回测] 策略A(趋势剥头皮) vs 策略B(清算猎杀) 在 1H/4H 的三年长跑")
    print("="*80)
    
    symbols = ["BTCUSDT", "ETHUSDT"]
    intervals = {"1h": 16, "4h": 8} # 1h拉取约16000根(约1.8年), 4h拉取约8000根(约3.6年)
    
    for sym in symbols:
        print(f"\n📊 测试标的: {sym}")
        print("-" * 80)
        for iv, chunks in intervals.items():
            df = fetch_long_term_klines(sym, iv, chunks=chunks)
            if df is None or df.empty: continue
            
            days = (len(df) * {"1h":1, "4h":4}[iv]) / 24
            print(f"🕒 时间级别: {iv:<2} | 成功获取 K线数量: {len(df):<5} 根 (约 {days:.1f} 天历史)")
            
            # 运行策略 A
            cap_a, tr_a, wr_a = backtest_strategy_A_trend_scalp(df, iv)
            daily_tr_a = tr_a / days if days > 0 else 0
            
            # 运行策略 B
            cap_b, tr_b, wr_b = backtest_strategy_B_liquidity_sweep(df, iv)
            daily_tr_b = tr_b / days if days > 0 else 0
            
            print(f"  🟢 策略A (趋势剥头皮): 胜率 {wr_a:4.1f}% | 频率 {daily_tr_a:4.2f}次/天 | 最终资金: ${cap_a:10,.2f}")
            print(f"  🩸 策略B (清算猎杀)  : 胜率 {wr_b:4.1f}% | 频率 {daily_tr_b:4.2f}次/天 | 最终资金: ${cap_b:10,.2f}")
