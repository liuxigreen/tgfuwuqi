import os
import sys
import json
from serpapi import GoogleSearch

def fetch_crypto_twitter_sentiment(coin_symbol):
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        print("Error: SERPAPI_API_KEY not found.")
        sys.exit(1)

    print(f"--- 正在使用 SerpApi 搜索推特上关于 {coin_symbol} 的情绪数据 ---")
    
    params = {
        "engine": "google",
        "q": f'"{coin_symbol}" (buy OR moon OR bull OR pump OR sell OR dump OR short) site:twitter.com',
        "api_key": api_key,
        "tbs": "qdr:d",  # 过去24小时
        "hl": "en",
        "gl": "us"
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # 提取推文卡片数据
        if "twitter_results" in results:
            print("\n[发现推特卡片 - 高权重情绪源]")
            tweets = results["twitter_results"].get("tweets", [])
            for t in tweets[:3]:
                print(f"- 推文: {t.get('snippet')}")
        
        # 提取常规搜索结果
        print("\n[近期全网讨论热度]")
        organic_results = results.get("organic_results", [])
        for res in organic_results[:5]:
            print(f"- {res.get('title')}: {res.get('snippet')}")
            
        print(f"\n✅ 成功拉取到 {len(organic_results)} 条高相关搜索结果 (24h内)。")
        
    except Exception as e:
        print(f"API 请求失败: {e}")

if __name__ == "__main__":
    fetch_crypto_twitter_sentiment("SOL")
