import os
import json
import time
from serpapi import GoogleSearch

# 第九批 100 个真实加密账号 (重点覆盖华尔街宏观基金、传统金融(TradFi)转加密大佬、以及全球顶级经济分析师)
NEW_100_TRADERS_V9 = [
    "LynAldenContact", "CaitlinLong_", "PrestonPysh", "TraceMayer", "Excellion",
    "GaborGurbacs", "TaviCosta", "LukeGromen", "Crescat_Capital", "RealVision",
    "JimBiancoWT", "Steen_Jakobsen", "SvenHenrich", "DiMartinoBooth", "LJMakridis",
    "JulianMIne", "MacroAlf", "SantiagoAuFund", "DavidFellah", "BenHuntFund",
    "TashaARK", "YassineARK", "FrankChaparro", "NathanielWhittemore", "Melt_Dem",
    "CoinSharesCo", "BitwiseInvest", "Grayscale", "Fidelity", "MicroStrategy",
    "BlockFi", "PanteraCapital", "Polychain", "1confirmation", "DragonflyCap",
    "a16z", "Sequoia", "BessemerVP", "FoundersFund", "USVC",
    "CumberlandSays", "B2C2Group", "GSR_io", "JumpTrading", "JaneStreetGroup",
    "SusquehannaInt", "OptiverUS", "DRWTrading", "VirtuFinancial", "TowerResearch",
    "GalaxyDigital", "GenesisTrading", "NYDIG", "OspreyFunds", "ValkyrieFunds",
    "ProShares", "VanEck_US", "WisdomTreeFunds", "InvescoUS", "GlobalXUS",
    "Direxion", "FirstTrust", "StateStreet", "BlackRock", "Vanguard_Group",
    "MorganStanley", "GoldmanSachs", "JPMorgan", "Citi", "BofA",
    "WellsFargo", "BNPParibas", "Barclays", "UBS", "CreditSuisse",
    "DeutscheBank", "Nomura", "SocGen", "HSBC", "RBS",
    "StandardChartered", "NatWest", "LloydsBank", "SantanderBank", "ING",
    "BBVA", "UniCredit", "IntesaSanpaolo", "Commerzbank", "DZBANK",
    "ABNAMRO", "Rabobank", "Nordea", "DanskeBank", "SEBGroup",
    "Swedbank", "Handelsbanken", "DNB_Bank", "Nykredit", "JyskeBank"
]

NEW_100_TRADERS_V9 = list(set(NEW_100_TRADERS_V9))[:100]

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def build_offline_database_v9():
    api_key = os.getenv("SERPAPI_API_KEY")
    all_extracted_tweets = []
    
    chunks = list(chunk_list(NEW_100_TRADERS_V9, 30))
    print(f"🚀 开始执行【第九批离线打包】(Batch 9 ETL)，将新 100 个华尔街/传统金融/宏观大V分为 {len(chunks)} 批进行极限搜索...")
    
    for i, batch in enumerate(chunks):
        sites = " OR ".join([f"site:twitter.com/{handle}" for handle in batch])
        # 强化宏观经济、ETF、流动性、机构建仓词汇
        query = f'({sites}) ("ETF" OR "liquidity" OR "interest rate" OR "macro" OR "inflation" OR "yield" OR "allocation")'
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 20
        }
        
        try:
            print(f"\n[Batch {i+1}/{len(chunks)}] 发送请求，包含 {len(batch)} 个华尔街/宏观大V账号...")
            res = GoogleSearch(params).get_dict()
            if "organic_results" in res:
                results = res["organic_results"]
                print(f"✅ 成功命中 {len(results)} 条极高价值的宏观干货！")
                for r in results:
                    all_extracted_tweets.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "link": r.get("link", "")
                    })
            else:
                print("⚠️ 没有拿到 organic_results。")
        except Exception as e:
            print(f"❌ 批量请求失败: {e}")
            
        time.sleep(2) 

    db_file = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v9.json"
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 第九批离线数据库构建完成！屯下了 {len(all_extracted_tweets)} 条极高价值的华尔街宏观推文。")
    print(f"💾 数据已保存在: {db_file}")

if __name__ == "__main__":
    build_offline_database_v9()
