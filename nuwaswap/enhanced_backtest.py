import requests
import pandas as pd
import numpy as np
import time

def fetch_klines(symbol="BTCUSDT", interval="4h", limit=1500):
    print(f"正在从 Binance Futures 拉取 {symbol} {interval} 历史数据...")
    url = "https://fapi.binance.com/fapi/v1/klines"
    
    # 获取两批数据 (约 3000 根 4H K线，合 500 天，跨越牛熊震荡)
    all_data = []
    end_time = None
    
    for _ in range(2):
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if end_time:
            params["endTime"] = end_time
            
        res = requests.get(url, params=params)
        data = res.json()
        if not data:
            break
            
        all_data = data + all_data
        end_time = data[0][0] - 1
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

def apply_enhanced_unified_strategy(df):
    print("正在引入『大级别趋势滤网 (HTF Filter)』和『波动率自适应 (ATR)』，深度修改模型...")
    
    # ==========================================
    # 核心改造 1: 大级别趋势滤网 (High Time Frame Filter)
    # 不再盲目捕捉小周期的反弹，只做与大级别 (EMA200) 同向的交易。
    # 这是顶级波段交易员（如 @Pentosh1）的右侧铁律。
    # ==========================================
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['HTF_Trend'] = np.where(df['Close'] > df['EMA200'], 1, -1) # 1 为大多头，-1 为大空头
    
    # ==========================================
    # 核心改造 2: 真实波动幅度 (ATR - Average True Range)
    # 用来动态计算合理的止损和止盈，而不是写死 1.5% 或 5%。
    # 避免在低波动时设置过宽止损，在高波动时被无意义插针打掉。
    # ==========================================
    df['TR'] = np.maximum(df['High'] - df['Low'], 
                          np.maximum(abs(df['High'] - df['Close'].shift(1)), 
                                     abs(df['Low'] - df['Close'].shift(1))))
    df['ATR'] = df['TR'].rolling(window=14).mean()
    
    # 策略 1: 短期动量 (EMA20 vs EMA50)
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['Momentum_Score'] = np.where(df['EMA20'] > df['EMA50'], 1, -1)
    
    # 策略 2: RSI 均值回归 (仅寻找顺势的回踩，不做逆势的接刀)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Pullback_Score'] = 0
    # 在大多头中 (HTF=1)，寻找 RSI<40 的超卖机会 (顺势回踩)
    df.loc[(df['RSI'] < 40) & (df['HTF_Trend'] == 1), 'Pullback_Score'] = 2
    # 在大空头中 (HTF=-1)，寻找 RSI>60 的超买机会 (顺势反弹做空)
    df.loc[(df['RSI'] > 60) & (df['HTF_Trend'] == -1), 'Pullback_Score'] = -2
    
    # 最终打分
    df['Final_Signal'] = 0
    
    # 必须大级别滤网、短期动量、回踩指标三者共振，才能开仓
    for i in range(1, len(df)):
        htf = df['HTF_Trend'].iloc[i]
        mom = df['Momentum_Score'].iloc[i]
        pb = df['Pullback_Score'].iloc[i]
        
        # 极度严苛的开仓条件：
        # 大级别是多头，短期动量向上，且刚经历了一波 RSI 超卖回踩
        if htf == 1 and mom == 1 and pb == 2:
            df.loc[df.index[i], 'Final_Signal'] = 1
        # 大级别空头，短期动量向下，且刚经历了一波 RSI 超买反抽
        elif htf == -1 and mom == -1 and pb == -2:
            df.loc[df.index[i], 'Final_Signal'] = -1
            
    return df

def run_backtest(df):
    print("正在执行 4h 级别『大滤网+动态ATR』实战回测...")
    initial_capital = 10000
    capital = initial_capital
    position = 0
    entry_price = 0
    stop_loss_price = 0
    take_profit_price = 0
    
    trades = []
    
    for i in range(1, len(df)):
        signal = df['Final_Signal'].iloc[i-1]
        current_price = df['Open'].iloc[i]
        atr = df['ATR'].iloc[i-1]
        
        # 止盈止损逻辑 (动态 ATR)
        if position != 0:
            # 检查是否触及止损或止盈
            if (position == 1 and (df['Low'].iloc[i] <= stop_loss_price or df['High'].iloc[i] >= take_profit_price)) or \
               (position == -1 and (df['High'].iloc[i] >= stop_loss_price or df['Low'].iloc[i] <= take_profit_price)):
                
                # 简单计算（假设触碰价格即成交，略去精细的开盘跳空等）
                if position == 1:
                    exit_price = take_profit_price if df['High'].iloc[i] >= take_profit_price else stop_loss_price
                else:
                    exit_price = take_profit_price if df['Low'].iloc[i] <= take_profit_price else stop_loss_price
                    
                pnl_pct = (exit_price - entry_price) / entry_price * position
                capital = capital * (1 + pnl_pct)
                trades.append(pnl_pct)
                position = 0
                
        # 严格开仓逻辑
        if position == 0 and signal != 0:
            position = signal
            entry_price = current_price
            # 根据 2 倍 ATR 设置止损，6 倍 ATR 设置止盈 (1:3 的绝佳 R:R)
            if position == 1:
                stop_loss_price = entry_price - (2 * atr)
                take_profit_price = entry_price + (6 * atr)
            else:
                stop_loss_price = entry_price + (2 * atr)
                take_profit_price = entry_price - (6 * atr)

    total_trades = len(trades)
    winning_trades = len([t for t in trades if t > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    total_return = (capital - initial_capital) / initial_capital * 100
    
    print("\n" + "="*50)
    print("🧠 增强版统一大脑 (HTF大级别滤网 + 动态ATR风控)")
    print("="*50)
    print(f"数据量: {len(df)} 根 4h K线 (约 {len(df)//6} 天)")
    print(f"初始资金: ${initial_capital}")
    print(f"最终资金: ${capital:.2f}")
    print(f"总收益率: {total_return:.2f}% (现货无杠杆)")
    print(f"交易次数: {total_trades} 次 (严苛出手)")
    print(f"胜率: {win_rate*100:.2f}%")
    print("="*50)

if __name__ == "__main__":
    df = fetch_klines(symbol="BTCUSDT", interval="4h", limit=1500)
    df = apply_enhanced_unified_strategy(df)
    run_backtest(df)