import os
import json
import time

# ---------------------------------------------------------
# V15 RAG 大模型情绪做空引擎 (The 100-Point Detector)
# 新增功能：引入用户提供的《妖币检测器设计》100分制系统
# 综合社交 Mindshare、市值、叙事与代币风险，对代币进行打分诊断。
# ---------------------------------------------------------

KNOWLEDGE_BASE_PATH = "/workspace/.claude/skills/crypto-trader-framework/references/knowledge_base/yaobi_patterns.md"

def load_yaobi_knowledge_base():
    """读取本地 Obsidian 知识库"""
    if os.path.exists(KNOWLEDGE_BASE_PATH):
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "未找到妖币知识库。"

def fetch_mock_coin_data(coin_symbol):
    """模拟：从推特、Surf DB、Tokenomics 等接口抓取代币的全维数据"""
    print(f"📡 正在扫描全网数据，提取 {coin_symbol} 的 Mindshare、市值、流动性与叙事标签...")
    time.sleep(1)
    
    if coin_symbol == "NEET":
        return {
            "symbol": "NEET",
            "twitter_followers": 250000, # > 20w
            "mindshare_rank": 2,         # Top 10
            "market_cap_usd": 27180000,  # < 5000w
            "volume_24h_ratio": 0.45,    # > 10%
            "tags": ["Meme", "Solana", "Anti-work"],
            "price_change_24h": 0.35,    # > 20%
            "vesting_transparent": True
        }
    elif coin_symbol == "RIVER":
        return {
            "symbol": "RIVER",
            "twitter_followers": 208000, # > 20w
            "mindshare_rank": 150,       # 非 Top 30
            "market_cap_usd": 125000000, # > 1亿
            "volume_24h_ratio": 0.14,    # > 10%
            "tags": ["Stablecoin", "Yield", "DeFi"],
            "price_change_24h": -0.02,   # < 0
            "vesting_transparent": True
        }
    elif coin_symbol == "RAVE":
        return {
            "symbol": "RAVE",
            "twitter_followers": 80000,  
            "mindshare_rank": 10,        
            "market_cap_usd": 223000000, # 高市值
            "volume_24h_ratio": 0.22,    
            "tags": ["DAO"],
            "price_change_24h": -0.04,   
            "vesting_transparent": False # 有巨大解锁悬崖
        }
    else:
        return {"symbol": coin_symbol, "market_cap_usd": 500000000, "tags": ["Unknown"]}

def calculate_yaobi_score(data):
    """根据知识库中的 100 分制检测器规则计算妖币得分"""
    score = 0
    breakdown = []
    
    # 1. 社交 Mindshare (40%)
    social_score = 0
    if data.get("twitter_followers", 0) > 200000: social_score += 20
    if data.get("mindshare_rank", 999) <= 30: social_score += 20
    score += social_score
    breakdown.append(f"社交 Mindshare: {social_score}/40")
    
    # 2. 市值与流动性 (30%)
    liq_score = 0
    if data.get("market_cap_usd", 999999999) < 50000000: liq_score += 15
    if data.get("volume_24h_ratio", 0) > 0.10: liq_score += 15
    score += liq_score
    breakdown.append(f"市值与流动性: {liq_score}/30")
    
    # 3. 叙事与变化标签 (20%)
    narrative_score = 0
    if "Meme" in data.get("tags", []): narrative_score += 10
    if data.get("price_change_24h", 0) > 0.20: narrative_score += 10
    score += narrative_score
    breakdown.append(f"叙事与变化标签: {narrative_score}/20")
    
    # 4. 风险控制 (10%)
    risk_score = 0
    if data.get("vesting_transparent", False): risk_score += 5
    # 假设这里模拟无 rug 史
    risk_score += 5 
    score += risk_score
    breakdown.append(f"风险控制: {risk_score}/10")
    
    return score, breakdown

def generate_llm_rag_prompt(data, score, breakdown, knowledge_text):
    """构建发给大模型的 RAG Prompt"""
    breakdown_str = "\n".join([f"  - {b}" for b in breakdown])
    
    prompt = f"""
你现在是一台顶级的【妖币检测器 (YaoBi Detector)】。
请根据外部知识库的 100分制规则，对该代币进行诊断，并给出交易建议。

---
【检测数据面板】：
代币：{data['symbol']}
总评分：{score} / 100
得分明细：
{breakdown_str}
标签：{", ".join(data.get('tags', []))}
市值：${data.get('market_cap_usd', 0):,}

---
【判决阈值规则】：
- > 80 分：极度危险的妖币（做空候选）或极早期的拉盘机会（买入候选）。
- < 50 分：正常的 DeFi/基础设施，不具备妖币特征，建议忽略。

请输出你的判决报告：
1. 妖气评估（高/中/低）。
2. 诊断逻辑（基于得分明细和标签）。
3. 交易建议（SHORT / LONG / WAIT）。
"""
    return prompt

def simulate_llm_decision(prompt, score):
    """模拟大模型判决"""
    print("🧠 [LLM 正在结合 100 分制量化模型进行推理...]")
    time.sleep(1)
    
    if score > 80:
        return f"""
🚨 **[妖币检测器报告]** 🚨
**评分：{score}/100**
**1. 妖气评估**：【极高 (Highly Toxic/Explosive)】
**2. 诊断逻辑**：
   - 极低的市值与爆炸性的社交 Mindshare 完美契合妖币启动特征。
   - 带有强烈的 Meme 叙事，流动性换手率惊人，符合庄家高度控盘或极早期拉盘的迹象。
**3. 交易建议**：
   💥 **【LONG (早期埋伏) 或 SHORT (高位狙击)】** 
   - 如果处于启动初期（市值<3000万），可使用 Banana Gun 极小仓位潜伏。
   - 若已出现顶部天量，直接右侧做空，带 20% 宽止损。
"""
    elif score < 50:
        return f"""
💤 **[妖币检测器报告]** 💤
**评分：{score}/100**
**1. 妖气评估**：【极低 (Normal/Boring)】
**2. 诊断逻辑**：
   - 虽然有一定社交基础，但市值过大，缺乏爆发力。
   - 标签为基础设施/稳定币（如 Stablecoin/DeFi），且无明显的 24h 价格异动，庄家无法在此类盘面中实施高倍数拉砸。
**3. 交易建议**：
   ⏳ **【WAIT (忽略)】** 
   - 此代币为常规基建项目，不具备“妖币”特质，不符合本系统的猎杀标准。
"""
    else:
        return f"""
⚠️ **[妖币检测器报告]** ⚠️
**评分：{score}/100**
**1. 妖气评估**：【中等 (Risky/Uncertain)】
**2. 诊断逻辑**：
   - 存在一定的社交热度或流动性，但叙事或代币经济学存在缺陷（如巨大的解锁悬崖）。
**3. 交易建议**：
   ⏳ **【WAIT (高度观望)】** 
   - 警惕潜在的抛压，等待更明确的情绪极值出现。
"""

if __name__ == "__main__":
    print("="*60)
    print("🤖 [V15] AI 妖币检测器 (The 100-Point Mindshare Engine)")
    print("="*60)
    
    kb_text = load_yaobi_knowledge_base()
    
    # 测试案例 1: NEET (高分妖币)
    data_neet = fetch_mock_coin_data("NEET")
    score_neet, bd_neet = calculate_yaobi_score(data_neet)
    prompt_neet = generate_llm_rag_prompt(data_neet, score_neet, bd_neet, kb_text)
    print(f"\n>>> 诊断标的: $NEET")
    print(simulate_llm_decision(prompt_neet, score_neet))
    print("-" * 40)
    
    # 测试案例 2: RIVER (低分伪妖币)
    data_river = fetch_mock_coin_data("RIVER")
    score_river, bd_river = calculate_yaobi_score(data_river)
    prompt_river = generate_llm_rag_prompt(data_river, score_river, bd_river, kb_text)
    print(f"\n>>> 诊断标的: $RIVER")
    print(simulate_llm_decision(prompt_river, score_river))
