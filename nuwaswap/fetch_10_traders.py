import os
import sys
import json
import time
from serpapi import GoogleSearch

# 精选 10 位最具代表性的顶级交易员 (涵盖不同流派)
TOP_10_TRADERS = [
    "GCRClassic",     # 宏观/逆向/做空
    "cobie",          # 周期/元叙事
    "HsakaTrades",    # 动量/清算猎杀/资金费率
    "blknoiz06",      # Ansem: Solana生态/早期Alpha
    "DonAlt",         # 极简Price Action/右侧突破
    "Pentosh1",       # 宏观图表/趋势跟踪
    "CredibleCrypto", # 波浪理论/长期结构
    "Bluntz_Capital", # 波浪/底背离/ABC调整
    "lightcrypto",    # 大资金/微观结构/自营
    "CryptoKaleo"     # 斜向趋势突破/高频进攻
]

def fetch_trader_alpha(handle):
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        print("❌ 错误: 找不到 SERPAPI_API_KEY 环境变量。")
        return []

    print(f"\n🔍 正在检索 @{handle} 的高价值策略推文与复盘...")
    
    # 构造高级搜索查询：寻找他们分享的干货 (long, short, thesis, target, PNL, strategy)
    query = f'site:twitter.com/{handle} ("long" OR "short" OR "thesis" OR "target" OR "strategy" OR "setup")'
    
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": 10  # 每个交易员拉取前 10 条最高权重的策略推文
    }

    trader_data = {
        "handle": handle,
        "alpha_tweets": []
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "organic_results" in results:
            for r in results["organic_results"]:
                trader_data["alpha_tweets"].append({
                    "title": r.get("title", ""),
                    "content": r.get("snippet", ""),
                    "url": r.get("link", "")
                })
        
        print(f"✅ 成功提取 @{handle} 的 {len(trader_data['alpha_tweets'])} 条核心策略。")
        
    except Exception as e:
        print(f"❌ 提取 @{handle} 数据时发生错误: {e}")
        
    return trader_data

def main():
    all_traders_data = []
    
    for trader in TOP_10_TRADERS:
        data = fetch_trader_alpha(trader)
        all_traders_data.append(data)
        time.sleep(1.5) # 频率控制，防止被 SerpApi 封禁
        
    # 归档保存
    output_dir = "/workspace/.claude/skills/crypto-trader-framework/references/sources/tweets"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "top_10_traders_alpha.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_traders_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 批量拉取完成！共收集 {len(TOP_10_TRADERS)} 位顶级交易员的干货数据。")
    print(f"📂 数据已归档至: {output_file}")

if __name__ == "__main__":
    main()
