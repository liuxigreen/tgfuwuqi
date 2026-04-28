import requests
import pandas as pd
import numpy as np

# ==========================================
# 1. 数据获取层 (Data Ingestion)
# ==========================================
def fetch_binance_futures_klines(symbol="BTCUSDT", interval="1d", limit=1000):
    print(f"正在从 Binance Futures 拉取 {symbol} {interval} 历史数据 (最近 {limit} 天)...")
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # 转换为 DataFrame
    columns = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 
               'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
    df = pd.DataFrame(data, columns=columns)
    
    # 清洗数据
    df['Date'] = pd.to_datetime(df['Open_time'], unit='ms')
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = df[col].astype(float)
        
    return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

# ==========================================
# 2. 策略量化层 (Distillation -> Math)
# 模拟 200 位交易员的“双脑系统”
# ==========================================
def calculate_dual_brain_signals(df):
    print("正在将 200 位顶级交易员的心智模型量化为技术指标...")
    
    # 🧠 左脑 (Left Brain): 逆向思维、情绪极值 (用 RSI 和 布林带偏离度模拟极度恐慌/贪婪)
    # RSI > 75 视为散户极度贪婪(做空信号)，RSI < 30 视为极度恐慌(做多信号)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Left_Brain_Signal'] = 0  # 1: Long, -1: Short
    df.loc[df['RSI'] < 30, 'Left_Brain_Signal'] = 1
    df.loc[df['RSI'] > 75, 'Left_Brain_Signal'] = -1
    
    # 🧠 右脑 (Right Brain): 顺势动量、趋势跟踪 (用 EMA 均线交叉模拟右侧追随)
    # EMA20 上穿 EMA50 看多，下穿看空
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    df['Right_Brain_Signal'] = 0
    df.loc[df['EMA20'] > df['EMA50'], 'Right_Brain_Signal'] = 1
    df.loc[df['EMA20'] < df['EMA50'], 'Right_Brain_Signal'] = -1
    
    # ⚖️ 裁决机制 (The Arbiter)
    # 规则 1: 双脑共振 (极度恐慌且趋势开始反转) -> 强力做多
    # 规则 2: 右脑优先 (趋势极强时，忽略左脑的"超买"做空建议，防止轧空)
    df['Final_Signal'] = 0
    
    for i in range(1, len(df)):
        lb = df['Left_Brain_Signal'].iloc[i]
        rb = df['Right_Brain_Signal'].iloc[i]
        
        if lb == 1 and rb == 1:
            df.loc[df.index[i], 'Final_Signal'] = 1 # 强力做多
        elif lb == -1 and rb == -1:
            df.loc[df.index[i], 'Final_Signal'] = -1 # 强力做空
        elif lb == -1 and rb == 1:
            df.loc[df.index[i], 'Final_Signal'] = 0 # 左脑想空，但右脑趋势是多 -> 听右脑，禁止做空，观望
        elif lb == 1 and rb == -1:
            # 趋势是空，但左脑提示极度恐慌（超卖），尝试左侧抢反弹
            df.loc[df.index[i], 'Final_Signal'] = 1 
            
    return df

# ==========================================
# 3. 行为与优化层 (Backtesting / Optimization)
# ==========================================
def run_backtest(df):
    print("正在执行历史回测 (单执行验证)...")
    initial_capital = 10000
    capital = initial_capital
    position = 0  # 0: 空仓, 1: 做多, -1: 做空
    entry_price = 0
    
    trades = []
    
    for i in range(1, len(df)):
        signal = df['Final_Signal'].iloc[i-1] # 昨天收盘后的信号
        current_price = df['Open'].iloc[i]    # 今天开盘价执行
        
        # 简单止损止盈逻辑 (模拟交易员的截断亏损)
        if position != 0:
            pnl_pct = (current_price - entry_price) / entry_price * position
            # 止损 5%，止盈 15% (1:3 盈亏比)
            if pnl_pct <= -0.05 or pnl_pct >= 0.15 or signal != position:
                capital = capital * (1 + pnl_pct)
                trades.append(pnl_pct)
                position = 0 # 平仓
                
        # 开仓逻辑
        if position == 0 and signal != 0:
            position = signal
            entry_price = current_price

    # 统计结果
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    total_return = (capital - initial_capital) / initial_capital * 100
    
    print("\n" + "="*40)
    print("🧠 双脑交易系统 回测报告 (基于 200+ 交易员共识)")
    print("="*40)
    print(f"回测天数: {len(df)} 天")
    print(f"初始资金: ${initial_capital}")
    print(f"最终资金: ${capital:.2f}")
    print(f"总收益率: {total_return:.2f}%")
    print(f"交易次数: {total_trades}")
    print(f"胜率: {win_rate*100:.2f}%")
    print("="*40)

if __name__ == "__main__":
    df = fetch_binance_futures_klines(symbol="BTCUSDT", interval="1d", limit=1000)
    df = calculate_dual_brain_signals(df)
    run_backtest(df)
