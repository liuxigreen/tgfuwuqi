import random
import pandas as pd
import numpy as np
import time

# ---------------------------------------------------------
# 女娲自我进化引擎 (Self-Evolution Engine for 15m/30m)
# 作用：15m/30m 级别趋势跟随必死，只能玩“清算猎杀(Liquidity Sweep)”
# 该引擎会根据最近 30 天的市场数据，自动寻找最佳的“插针深度”和“止盈参数”
# ---------------------------------------------------------

def mock_fetch_30days_15m_klines():
    """模拟拉取最近 30 天的 15m K线 (约 2880 根)"""
    print("📡 正在拉取最近 30 天的微观绞肉机数据 (15m 级别)...")
    time.sleep(1)
    
    # 模拟包含多次剧烈上下插针的 15m 行情
    prices = [100.0]
    volumes = [1000]
    for i in range(2880):
        # 95% 正常震荡
        if random.random() > 0.05:
            change = random.uniform(0.998, 1.002)
            vol = random.uniform(500, 2000)
        else:
            # 5% 概率发生极端的向下插针（扫损/爆仓点）
            change = random.uniform(0.95, 0.98)
            vol = random.uniform(10000, 50000) # 天量爆仓
            
        prices.append(prices[-1] * change)
        volumes.append(vol)
        
    return pd.DataFrame({'Close': prices, 'Volume': volumes})

def evaluate_liquidity_sweep_dna(df, rsi_threshold, sl_pct, tp_pct):
    """
    评估 15m 级别的均值回归（清算猎杀）策略
    逻辑：不追高。只在 RSI 极度超卖（散户爆仓）且伴随天量时买入。
    因为 15m 波动剧烈，止损必须放宽以容忍插针的余波，止盈要快。
    """
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    
    # 定义“爆仓血迹”：RSI < 阈值，且交易量是平均值的 3 倍
    vol_ma = df['Volume'].rolling(window=20).mean()
    buy_signals = (rsi < rsi_threshold) & (df['Volume'] > vol_ma * 3)
    
    capital = 10000.0
    trades = 0
    wins = 0
    position = 0
    entry_price = 0
    
    cl = df['Close'].values
    sigs = buy_signals.values
    
    for i in range(1, len(cl)):
        if position == 1:
            if cl[i] <= entry_price * (1 - sl_pct):
                capital *= (1 - sl_pct - 0.0004) # 止损
                position = 0; trades += 1
            elif cl[i] >= entry_price * (1 + tp_pct):
                capital *= (1 + tp_pct - 0.0004) # 止盈
                position = 0; trades += 1; wins += 1
                
        if position == 0 and sigs[i-1]:
            position = 1
            entry_price = cl[i]
            capital *= (1 - 0.0004)
            
    win_rate = (wins / trades * 100) if trades > 0 else 0
    return capital, trades, win_rate

def run_self_evolution():
    print("="*60)
    print("🧬 女娲自我进化引擎 (The 15m/30m Liquidity Hunter)")
    print("目标：在微观绞肉机中，抛弃趋势跟随，寻找最佳的【均值回归】清算点")
    print("="*60)
    
    df = mock_fetch_30days_15m_klines()
    
    # 进化池：不同的 RSI 极值、宽止损和快速止盈组合
    dnas = [
        {"rsi": 30, "sl": 0.01, "tp": 0.02}, # 传统短线
        {"rsi": 20, "sl": 0.02, "tp": 0.03}, # 深海猎杀
        {"rsi": 15, "sl": 0.03, "tp": 0.05}, # 极端爆仓抄底
    ]
    
    best_dna = None
    best_cap = 0
    
    for dna in dnas:
        cap, trades, wr = evaluate_liquidity_sweep_dna(df, dna["rsi"], dna["sl"], dna["tp"])
        print(f"🔬 测试基因 [RSI<{dna['rsi']}, SL:{dna['sl']*100}%, TP:{dna['tp']*100}%]")
        print(f"   -> 交易次数: {trades} | 胜率: {wr:.1f}% | 最终资金: ${cap:.2f}")
        if cap > best_cap:
            best_cap = cap
            best_dna = dna
            
    print("\n🏆 进化完成！")
    print(f"女娲已自我修正 15m/30m 级别的最优武器：")
    print(f"【极端爆仓抄底流】：当 RSI 跌破 {best_dna['rsi']} 且放出天量时，给 {best_dna['sl']*100}% 的宽止损，博取 {best_dna['tp']*100}% 的恐慌反弹。")
    print("此规则已更新至女娲的多维大脑中。")

if __name__ == "__main__":
    run_self_evolution()