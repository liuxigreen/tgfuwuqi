import requests
import pandas as pd
import numpy as np
import time

def fetch_klines(symbol="BTCUSDT", interval="1h", limit=1500):
    print(f"正在从 Binance Futures 拉取 {symbol} {interval} 历史数据...")
    url = "https://fapi.binance.com/fapi/v1/klines"
    
    # 为了拉取更多数据，进行 3 次分页 (约 4500 小时 / 半年高频数据)
    all_data = []
    end_time = None
    
    for _ in range(3):
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if end_time:
            params["endTime"] = end_time
            
        res = requests.get(url, params=params)
        data = res.json()
        if not data:
            break
            
        all_data = data + all_data
        end_time = data[0][0] - 1 # 下一次请求的结束时间是这批最早的一根线之前
        time.sleep(0.5)
        
    columns = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 
               'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
    df = pd.DataFrame(all_data, columns=columns)
    df.drop_duplicates(subset=['Open_time'], inplace=True)
    df.sort_values('Open_time', inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    df['Date'] = pd.to_datetime(df['Open_time'], unit='ms')
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = df[col].astype(float)
        
    return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

def apply_unified_multi_strategy(df):
    print("正在将 200 位顶级交易员的多种策略融合成「单一评分模型」...")
    
    # 策略 1: 动量与趋势跟踪 (Momentum / Trend) -> 权重: 1分
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['Trend_Score'] = np.where(df['EMA20'] > df['EMA50'], 1, -1)
    
    # 策略 2: 均值回归与超买超卖 (Mean Reversion / RSI Extreme) -> 权重: 2分 (逆向猎杀)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Reversion_Score'] = 0
    df.loc[df['RSI'] < 30, 'Reversion_Score'] = 2  # 极度超卖，强烈看多
    df.loc[df['RSI'] > 70, 'Reversion_Score'] = -2 # 极度超买，强烈看空
    
    # 策略 3: 波动率突破 (Bollinger Bands Breakout) -> 权重: 1分
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['EMA20'] + (df['STD20'] * 2)
    df['BB_Lower'] = df['EMA20'] - (df['STD20'] * 2)
    
    df['Volatility_Score'] = 0
    df.loc[df['Close'] < df['BB_Lower'], 'Volatility_Score'] = 1  # 跌破下轨，准备反弹
    df.loc[df['Close'] > df['BB_Upper'], 'Volatility_Score'] = -1 # 突破上轨，准备回调
    
    # 统一大脑裁决 (Unified Brain Scoring)
    # 总分 = 趋势分(1/-1) + 回归分(2/-2/0) + 波动分(1/-1/0)
    df['Total_Score'] = df['Trend_Score'] + df['Reversion_Score'] + df['Volatility_Score']
    
    df['Final_Signal'] = 0
    # 当总分 >= 2 时，多重共振（如：趋势向上且触碰下轨，或者趋势向下但极度超卖） -> 做多
    df.loc[df['Total_Score'] >= 2, 'Final_Signal'] = 1
    # 当总分 <= -2 时，多重共振 -> 做空
    df.loc[df['Total_Score'] <= -2, 'Final_Signal'] = -1
    
    return df

def run_backtest(df):
    print("正在执行 30m 级别高频实战回测...")
    initial_capital = 10000
    capital = initial_capital
    position = 0  # 0: 空仓, 1: 做多, -1: 做空
    entry_price = 0
    
    trades = []
    
    for i in range(1, len(df)):
        signal = df['Final_Signal'].iloc[i-1]
        current_price = df['Open'].iloc[i]
        
        # 止盈止损逻辑 (极高频短线：由于周期变短，波动变小，止损缩紧到 1.5%，止盈 4.5% -> 1:3 盈亏比)
        if position != 0:
            pnl_pct = (current_price - entry_price) / entry_price * position
            
            # 触发止盈/止损 或 信号反转
            if pnl_pct <= -0.015 or pnl_pct >= 0.045 or (signal != 0 and signal != position):
                # 记录这笔交易
                capital = capital * (1 + pnl_pct)
                trades.append(pnl_pct)
                position = 0 # 先平仓
                
        # 开仓逻辑
        if position == 0 and signal != 0:
            position = signal
            entry_price = current_price

    total_trades = len(trades)
    winning_trades = len([t for t in trades if t > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    total_return = (capital - initial_capital) / initial_capital * 100
    
    print("\n" + "="*50)
    print("🧠 统一大脑 (单脑多策略) 30分钟级别回测报告")
    print("="*50)
    print(f"数据量: {len(df)} 根 30m K线 (约 {len(df)//48} 天)")
    print(f"初始资金: ${initial_capital}")
    print(f"最终资金: ${capital:.2f}")
    print(f"总收益率: {total_return:.2f}% (现货无杠杆)")
    print(f"交易次数: {total_trades} 次 (极高频剥头皮)")
    print(f"胜率: {win_rate*100:.2f}%")
    print("="*50)

if __name__ == "__main__":
    df = fetch_klines(symbol="BTCUSDT", interval="30m", limit=1500)
    df = apply_unified_multi_strategy(df)
    run_backtest(df)
