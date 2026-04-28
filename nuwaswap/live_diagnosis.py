import requests
import pandas as pd
import numpy as np

def get_live_diagnosis(symbol="BTCUSDT", interval="30m"):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 100}
    res = requests.get(url, params=params).json()
    
    cols = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
            'Quote_volume', 'Trades', 'Taker_buy_base', 'Taker_buy_quote', 'Ignore']
    df = pd.DataFrame(res, columns=cols)
    for col in ['Open', 'High', 'Low', 'Close']: 
        df[col] = df[col].astype(float)
        
    # V2 Apex DNA for 30m
    ema_f_period = 21
    ema_s_period = 50
    rsi_period = 14
    sl_pct = 0.0167
    tp_pct = 0.0460
    
    df['EMA_F'] = df['Close'].ewm(span=ema_f_period, adjust=False).mean()
    df['EMA_S'] = df['Close'].ewm(span=ema_s_period, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    latest = df.iloc[-1]
    
    current_price = latest['Close']
    ema_f = latest['EMA_F']
    ema_s = latest['EMA_S']
    rsi = latest['RSI']
    
    trend = "多头趋势 (Bullish)" if ema_f > ema_s else "空头趋势 (Bearish)"
    
    signal = "等待猎物 (Wait)"
    reason = "未满足极端入场条件"
    if ema_f > ema_s and rsi < 30:
        signal = "🟢 准许做多 (LONG ENTRY)"
        reason = "处于多头趋势，且RSI进入超卖区，存在均值回归的爆发点"
    elif ema_f < ema_s and rsi > 70:
        signal = "🔴 准许做空 (SHORT ENTRY)"
        reason = "处于空头趋势，且RSI进入超买区，存在多头衰竭的做空点"
    elif ema_f > ema_s and rsi >= 30:
        reason = "顺势多头，但当前RSI未达到超卖极值(<30)，追高易遭插针扫损"
    elif ema_f < ema_s and rsi <= 70:
        reason = "顺势空头，但当前RSI未达到超买极值(>70)，追空易遭轧空反抽"
        
    long_sl = current_price * (1 - sl_pct)
    long_tp = current_price * (1 + tp_pct)
    
    short_sl = current_price * (1 + sl_pct)
    short_tp = current_price * (1 - tp_pct)
    
    print(f"=== 🪙 {symbol} 30m 级别实盘诊断 (V2 Apex DNA) ===")
    print(f"当前价格 (Price) : {current_price:.2f}")
    print(f"快线 EMA(21)     : {ema_f:.2f}")
    print(f"慢线 EMA(50)     : {ema_s:.2f}")
    print(f"动量 RSI(14)     : {rsi:.2f}")
    print(f"--------------------------------------------------")
    print(f"当前大势 (Trend) : {trend}")
    print(f"操作指令 (Signal): {signal}")
    print(f"裁决逻辑 (Reason): {reason}")
    print(f"--------------------------------------------------")
    print(f"⚔️ 若当前市价强行开单，系统强制要求的风控位：")
    print(f"  [做多 LONG]  止损位: {long_sl:.2f} (-1.67%) | 止盈位: {long_tp:.2f} (+4.60%)")
    print(f"  [做空 SHORT] 止损位: {short_sl:.2f} (+1.67%) | 止盈位: {short_tp:.2f} (-4.60%)")

if __name__ == "__main__":
    get_live_diagnosis("BTCUSDT", "30m")
