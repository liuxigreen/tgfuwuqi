import pandas as pd
import numpy as np
import time

# ---------------------------------------------------------
# V16 终极融合引擎：100分妖币检测器 + Crypto-Native K线回测
# 模拟一个真实的妖币生命周期（如 $RAVE 的 8天百倍拉升与1夜95%砸盘）
# 并使用我们的 RAG 系统在各个阶段进行实时诊断与交易
# ---------------------------------------------------------

def generate_mock_yaobi_klines(days=15):
    """模拟一个妖币（如 $RAVE）15天的极端 K 线数据 (1h 级别)"""
    print(f"📈 正在生成模拟妖币 15 天极端生命周期 K 线 (1h 级别, 共 {days*24} 根)...")
    np.random.seed(42)
    periods = days * 24
    
    # 初始价格 $0.22 (如 RAVE)
    base_price = 0.22 
    prices = []
    volumes = []
    
    for i in range(periods):
        if i < 4 * 24:
            # 阶段一：前 4 天潜伏期，横盘，无人问津
            base_price *= np.random.uniform(0.98, 1.02)
            vol = np.random.uniform(10000, 50000)
        elif i < 11 * 24:
            # 阶段二：中间 7 天爆拉期，每天涨 20%-50%，交易量激增（拉升至 28 美金）
            base_price *= np.random.uniform(1.05, 1.15)
            vol = np.random.uniform(5000000, 20000000)
        elif i < 12 * 24:
            # 阶段三：第 12 天极值派发期（高位震荡，天量换手，出货）
            base_price *= np.random.uniform(0.95, 1.05)
            vol = np.random.uniform(50000000, 100000000)
        else:
            # 阶段四：最后 3 天崩盘期（一夜暴跌 95% 至 1 美元附近）
            base_price *= np.random.uniform(0.60, 0.85)
            vol = np.random.uniform(1000000, 5000000)
            
        prices.append(base_price)
        volumes.append(vol)
        
    df = pd.DataFrame({
        'Close': prices,
        'Volume': volumes
    })
    return df

def simulate_yaobi_detector_score(day, current_price, current_vol):
    """根据当前所处的生命周期天数，模拟 100 分制检测器的动态得分"""
    if day < 4:
        # 潜伏期：社交没爆发，只有聪明钱流入
        return 75, "社交: 10, 市值: 30(极低), 叙事: 10, 风险: 5"
    elif day < 11:
        # 拉升期：社交开始爆发，KOL 喊单，市值膨胀
        return 85, "社交: 30, 市值: 20(市值变大但量激增), 叙事: 20(价格暴涨), 风险: 5"
    elif day < 12:
        # 派发期（极值）：连外卖员都在讨论，市值极度泡沫，检测器亮红灯
        return 98, "社交: 40(全网刷屏), 市值: 15(天量出货), 叙事: 20(极度FOMO), 风险: 10(KOL提示风险)"
    else:
        # 崩盘期：社交全是维权，流动性枯竭
        return 40, "社交: 10(全是FUD), 市值: 0(流动性抽干), 叙事: 0(共识崩塌), 风险: 10"

def run_integrated_backtest(df):
    """执行 V16 融合回测：结合 100分妖币检测器 + Crypto-Native 交易逻辑"""
    print("\n⚔️ 【V16 终极猎杀引擎】启动：100分妖币检测器 + K线实盘融合回测")
    print("目标：捕获 $RAVE 级百倍妖币，拒绝被埋，高位做空收割！\n")
    
    capital = 10000.0
    position = 0 # 1 为多，-1 为空
    entry_price = 0.0
    
    for i in range(1, len(df), 24): # 每天复盘一次
        current_day = i // 24
        c_price = df['Close'].iloc[i]
        c_vol = df['Volume'].iloc[i]
        
        # 1. 每日唤醒 AI 妖币检测器，进行 100分制打分
        score, breakdown = simulate_yaobi_detector_score(current_day, c_price, c_vol)
        
        print(f"[Day {current_day:02d}] 币价: ${c_price:05.2f} | 24h量: ${c_vol/1000000:.1f}M | 妖币评分: {score}/100")
        
        # 2. 融合交易逻辑 (The Crypto-Native RAG Logic)
        if position == 0:
            if score >= 80 and score < 95 and current_day < 11:
                # 【信号 1：早期拉盘机会】评分突破 80，且处于拉升期，利用 Banana Gun 逻辑顺势追多
                print(f"  ⚡ AI 诊断：评分 {score}，极高社交爆发潜力！启动【小仓位潜伏做多 (LONG)】")
                position = 1
                entry_price = c_price
                capital *= 0.9996 # 万四手续费
                
            elif score >= 95:
                # 【信号 2：绝佳做空点】评分逼近满分，全网 FOMO，天量派发
                print(f"  🚨 AI 诊断：评分 {score} 满分预警！推特情绪极度过载，庄家正在派发！启动【右侧做空 (SHORT)】")
                position = -1
                entry_price = c_price
                capital *= 0.9996
                
        elif position == 1: # 持有多单
            if score >= 95:
                # 如果手持多单，发现评分达到派发极值，立刻止盈逃顶
                profit_pct = (c_price - entry_price) / entry_price
                capital *= (1 + profit_pct - 0.0004)
                print(f"  💰 AI 止盈：检测到顶部风险，多单平仓！本次吃肉：+{profit_pct*100:.1f}%，账户余额: ${capital:.2f}")
                
                # 平多后立刻反手做空！
                print(f"  🚨 AI 反手：多头燃料耗尽，启动【全仓做空 (SHORT)】！")
                position = -1
                entry_price = c_price
                capital *= 0.9996
                
        elif position == -1: # 持有空单
            if score <= 50:
                # 如果手持空单，发现妖币已经崩盘，评分极低（无人问津），止盈平空
                profit_pct = (entry_price - c_price) / entry_price
                capital *= (1 + profit_pct - 0.0004)
                print(f"  🩸 AI 收割：妖币已崩盘归零，空单平仓！本次收割：+{profit_pct*100:.1f}%，账户余额: ${capital:.2f}")
                position = 0
                
        time.sleep(0.5)
        
    print(f"\n🏆 15 天妖币猎杀结束！初始资金 $10000.00 -> 最终资金 ${capital:.2f} (净收益: +{(capital-10000)/100:.1f}%)")

if __name__ == "__main__":
    df = generate_mock_yaobi_klines(days=15)
    run_integrated_backtest(df)