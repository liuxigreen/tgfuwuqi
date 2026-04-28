import requests
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# V23 SMC 聪明钱结构 (Liquidity Sweep + CHoCH + OB) 回测引擎
# 模拟长周期（3年/最大数据量）在 1h 和 4h 级别上的表现
# ---------------------------------------------------------

def fetch_klines(symbol, interval, limit=1500):
    """由于币安单次 API 限制，我们最多拉取 1500 根 K 线。
       对于 4h 相当于 250 天，对于 1h 相当于 62 天。
       为了模拟更长的效果，我们只验证这套逻辑在最大数据集上的表现分布。
    """
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

def backtest_smc_strategy(df, symbol, interval, leverage=5):
    """
    极简版 SMC 算法逻辑：
    1. 寻找局部流动性池 (前高/前低 Swing High/Low) - 周期设为 20 根 K 线。
    2. 流动性猎杀 (Sweep)：价格刺穿了前低 (跌破 Swing Low)。
    3. 特性改变 (CHoCH)：扫损后，价格迅速反弹，突破了最近的一个小高点。
    4. 入场 (Entry)：在突破后回踩时入场。
    风控：因为 SMC 讲究极高盈亏比，止损设在扫损的最低点下方一点（约 0.5%），止盈设在上方对面的流动性池（约 2%~3%）。
    """
    capital = 10000.0
    position = 0
    entry_price = 0.0
    trades_count = 0
    wins = 0
    fee = 0.0004
    
    sl_pct = 0.005 # 极窄止损 0.5% (寻找订单块下沿)
    tp_pct = 0.025 # 盈亏比 1:5 的止盈目标 2.5%
    
    # 提取序列
    hi = df['High'].values
    lo = df['Low'].values
    cl = df['Close'].values
    
    # 1. 寻找局部的 Swing High / Low (粗略模拟流动性池)
    # 为了增加交易频率，缩小周期
    swing_lows = df['Low'].rolling(window=10, center=True).min()
    
    # 记录是否发生了 Sweep 和 CHoCH 的状态
    sweep_flag = False
    sweep_low_price = 0.0
    
    for i in range(10, len(cl)-1):
        c_hi, c_lo, c_cl = hi[i], lo[i], cl[i]
        
        # 仓位管理
        if position == 1:
            if c_lo <= entry_price * (1 - sl_pct):
                loss_amt = sl_pct * leverage
                capital *= (1 - loss_amt - fee)
                position = 0; trades_count += 1
            elif c_hi >= entry_price * (1 + tp_pct):
                profit_amt = tp_pct * leverage
                capital *= (1 + profit_amt - fee)
                position = 0; trades_count += 1; wins += 1
                
            if capital <= 100:
                capital = 0; break
            continue # 持仓时不寻找新信号
            
        # 寻找入场信号：
        # 2. Liquidity Sweep: 当前价格跌破了周期内的最低点 (扫损散户)
        if not sweep_flag and c_lo <= swing_lows.iloc[i-1]:
            # 放宽条件，只要有相对放量就视为 Sweep
            if df['Volume'].iloc[i] > df['Volume'].iloc[i-10:i].mean() * 0.8:
                sweep_flag = True
                sweep_low_price = c_lo
                continue
                
        # 超时重置 Sweep 标志 (如果扫损后一直没有反转)
        if sweep_flag and (c_lo < sweep_low_price):
            sweep_flag = False # 扫损失败，继续下跌
            
        # 3. CHoCH: 扫损后，价格反转，突破最近3根K线高点
        if sweep_flag and position == 0:
            recent_high = np.max(hi[i-3:i])
            if c_cl > recent_high:
                # 确认特性改变，机构入场，女娲跟随挂单做多
                position = 1
                entry_price = c_cl # 模拟回踩入场
                capital *= (1 - fee)
                # 信号消耗完毕，重置
                sweep_flag = False

    hours_per_candle = {"1h": 1, "4h": 4}[interval]
    days_tested = (len(df) * hours_per_candle) / 24
    daily_trades = trades_count / days_tested if days_tested > 0 else 0
    net_profit = capital - 10000
    win_rate = (wins / trades_count) * 100 if trades_count > 0 else 0
    
    print(f"[{interval:>3}] {symbol:<8} | 测试天数: {days_tested:5.1f}天 | 总开单: {trades_count:3d}次 -> 日均: {daily_trades:4.2f}次")
    print(f"      胜率: {win_rate:4.1f}% | 盈亏比 1:5 | 最终资金: ${capital:10,.2f} (净利 ${net_profit:8,.2f})")
    return win_rate, daily_trades

if __name__ == "__main__":
    print("="*75)
    print("🧠 [V23] SMC 聪明钱订单流 (Liquidity Sweep + CHoCH) 实盘回测")
    print("策略逻辑：只在散户爆仓点(前低)扫损后，出现机构反转(CHoCH)时入场。")
    print("风控：0.5%极窄止损(挂在扫损针尖下), 2.5%宽止盈(1:5超高盈亏比), 5x杠杆")
    print("="*75)
    
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    intervals = ["1h", "4h"]

    for sym in symbols:
        print(f"\n💎 猎杀标的: {sym}")
        print("-" * 75)
        for iv in intervals:
            df = fetch_klines(sym, iv, limit=1500) 
            if df is not None and not df.empty:
                backtest_smc_strategy(df, sym, iv)