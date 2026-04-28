import requests
import pandas as pd
import numpy as np
import random
import time

# ---------------------------------------------------------
# V18 随机 30 币种回测引擎：将主流币的“极窄止损”丢进山寨币绞肉机
# ---------------------------------------------------------

def get_random_futures_symbols(n=30):
    """从币安获取所有活跃的 USDT 永续合约，并随机抽取 30 个"""
    print("📡 正在获取币安合约市场活跃币种列表...")
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    res = requests.get(url).json()
    
    # 过滤掉 BTC, ETH, SOL（刚才测过了），并排除 1000 开头的合并合约
    symbols = [s['symbol'] for s in res['symbols'] 
               if s['status'] == 'TRADING' 
               and s['quoteAsset'] == 'USDT' 
               and s['symbol'] not in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
               and not s['symbol'].startswith("1000")]
    
    selected = random.sample(symbols, min(n, len(symbols)))
    print(f"🎲 随机抽取了 {len(selected)} 个山寨/妖币合约进行回测。")
    return selected

def fetch_recent_klines(symbol, interval="4h", limit=1500):
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

def backtest_mainstream_strategy_on_altcoins(df, symbol, leverage=10):
    """
    完全复用 V17 主流币剥头皮策略（4h级别, SL:0.38%, TP:2.13%, 10x杠杆）
    测试这种“安全参数”在随机山寨币上的死活。
    """
    capital = 10000.0  
    position = 0
    entry_price = 0.0
    trades_count = 0
    wins = 0
    
    sl_pct = 0.0038
    tp_pct = 0.0213
    fee = 0.0004
    
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
                    loss = sl_pct * leverage
                    capital *= (1 - loss - fee)
                    position = 0; trades_count += 1
                elif c_hi >= entry_price * (1 + tp_pct):
                    profit = tp_pct * leverage
                    capital *= (1 + profit - fee)
                    position = 0; trades_count += 1; wins += 1
            elif position == -1:
                if c_hi >= entry_price * (1 + sl_pct):
                    loss = sl_pct * leverage
                    capital *= (1 - loss - fee)
                    position = 0; trades_count += 1
                elif c_lo <= entry_price * (1 - tp_pct):
                    profit = tp_pct * leverage
                    capital *= (1 + profit - fee)
                    position = 0; trades_count += 1; wins += 1

        if position == 0 and s != 0:
            position = s; entry_price = c_op
            capital *= (1 - fee)
            
        if capital <= 100: # 跌破 100 美金算爆仓归零
            capital = 0
            break

    net_profit = capital - 10000
    win_rate = (wins / trades_count) * 100 if trades_count > 0 else 0
    return capital, trades_count, win_rate

if __name__ == "__main__":
    print("="*70)
    print("🎢 [V18] 随机 30 币种绞肉机测试 (将主流币策略丢进山寨场)")
    print("本金: $10,000 | 策略: 4h宏观剥头皮 (SL:0.38%, TP:2.13%, 10x杠杆)")
    print("="*70)
    
    symbols = get_random_symbols = get_random_futures_symbols(30)
    
    results = []
    total_bankrupt = 0
    total_profitable = 0
    
    print("\n⏳ 开始逐个回测 (约需 10 秒)...\n")
    for sym in symbols:
        df = fetch_recent_klines(sym)
        if df is None or len(df) < 500:
            continue
            
        cap, trades, wr = backtest_mainstream_strategy_on_altcoins(df, sym)
        results.append((sym, cap, trades, wr))
        
        if cap == 0:
            total_bankrupt += 1
            print(f"💀 {sym:>10} | 爆仓归零! (频繁被上下插针扫损)")
        elif cap > 10000:
            total_profitable += 1
            print(f"✅ {sym:>10} | 盈利 | 胜率: {wr:04.1f}% | 最终资金: ${cap:,.2f}")
        else:
            print(f"📉 {sym:>10} | 亏损 | 胜率: {wr:04.1f}% | 最终资金: ${cap:,.2f}")
            
        time.sleep(0.1) # 防限频
        
    print("="*70)
    print("📊 随机 30 币种终极测试报告")
    print("="*70)
    print(f"总测试币种: {len(results)} 个")
    print(f"盈利币种数: {total_profitable} 个 (占比 {total_profitable/len(results)*100:.1f}%)")
    print(f"亏损币种数: {len(results) - total_profitable - total_bankrupt} 个")
    print(f"爆仓归零数: {total_bankrupt} 个 (占比 {total_bankrupt/len(results)*100:.1f}%)")
    
    avg_cap = sum([r[1] for r in results]) / len(results)
    print(f"\n💡 如果你把资金均分给这 {len(results)} 个币种，你的平均最终单账号资金为: ${avg_cap:,.2f}")
    if avg_cap < 10000:
        print("💥 结论: 主流币的【极窄止损微观剥头皮策略】在山寨币上完全失效，沦为手续费燃料！")
    else:
        print("🏆 结论: 策略通用性极强，在山寨币上依然能保持盈利！")