import requests
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# V17 主流币 (BTC/ETH/SOL) 真实合约每日盈亏测算引擎
# ---------------------------------------------------------

def fetch_recent_klines(symbol="BTCUSDT", interval="4h", limit=1500):
    """拉取最近 1500 根 4h K线（约 250 天，8个月的最新行情）"""
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    res = requests.get(url, params=params).json()
    
    cols = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
            'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
    df = pd.DataFrame(res, columns=cols)
    for col in ['Open', 'High', 'Low', 'Close']: df[col] = df[col].astype(float)
    return df

def backtest_mainstream_contracts(df, symbol, leverage=10):
    """
    应用 V12 中最强的 4h 级别【宏观微观剥头皮】策略。
    对于主流币，我们不需要扛单，我们需要高频、极低止损的确定性利润。
    参数：EMA8 顺势，RSI 35/65 震荡入场。
    止损：0.38% (加10倍杠杆后是 3.8% 回撤)
    止盈：2.13% (加10倍杠杆后是 21.3% 利润)
    """
    capital = 10000.0  # 初始本金 $10000
    position = 0
    entry_price = 0.0
    trades_count = 0
    wins = 0
    
    sl_pct = 0.0038
    tp_pct = 0.0213
    fee = 0.0004 # 万四合约手续费
    
    op = df['Open'].values
    hi = df['High'].values
    lo = df['Low'].values
    cl = df['Close'].values
    
    # 指标计算
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

    # 回测主循环
    for i in range(1, len(sig)):
        s = sig[i-1]
        c_op, c_hi, c_lo = op[i], hi[i], lo[i]

        if position != 0:
            if position == 1:
                # 止损：跌破 0.38%
                if c_lo <= entry_price * (1 - sl_pct):
                    loss = sl_pct * leverage
                    capital *= (1 - loss - fee)
                    position = 0; trades_count += 1
                # 止盈：涨破 2.13%
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
            
    # 数据统计
    days_tested = len(df) * 4 / 24 # 4h klines
    net_profit = capital - 10000
    daily_profit = net_profit / days_tested
    win_rate = (wins / trades_count) * 100 if trades_count > 0 else 0
    
    print(f"🔹 {symbol:>8} | {leverage}x杠杆 | 回测天数: {days_tested:.0f}天 | 总开单: {trades_count} 次")
    print(f"   胜率: {win_rate:.1f}% | 最终本金: ${capital:.2f} (净赚 ${net_profit:.2f})")
    print(f"   💰 平均每天躺赚: ${daily_profit:.2f} (日化收益: {(daily_profit/10000)*100:.2f}%)")
    print("-" * 60)

if __name__ == "__main__":
    print("="*60)
    print("🏢 [V17] 主流币 (BTC/ETH/SOL) 真实合约每日收益测算")
    print("本金: $10,000 | 策略: 4h宏观剥头皮 (SL:0.38%, TP:2.13%)")
    print("="*60)
    
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    for sym in symbols:
        df = fetch_recent_klines(sym)
        # 主流币流动性极佳，我们使用安全的 10倍 杠杆（单次止损仅亏总仓位的 3.8%）
        backtest_mainstream_contracts(df, sym, leverage=10)