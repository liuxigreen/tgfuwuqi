import os
import json
import time
from serpapi import GoogleSearch

# 第十批 100 个真实加密账号 (千人大圆满：重点覆盖 AI 交易机器人、量化极客、黑客、MEV 搜索者以及最前沿的加密原生领袖)
NEW_100_TRADERS_V10 = [
    "bertcmiller", "thegostep", "fubuloubu", "lightclients", "libevm",
    "pcaversaccio", "samczsun", "transmissions11", "Zac_Aztec", "haydenzadams",
    "RuneKek", "StaniKulechov", "kaiynne", "Arthur_0x", "ki_young_ju",
    "WillyWoo", "ToneVays", "PeterLBrandt", "woonomic", "100trillionUSD",
    "cobie", "ThinkingMACRO", "RaoulGMI", "hasufl", "zhusu",
    "KyleLDavies", "AlamedaTrabucco", "EvgenyGaevoy", "SBF_FTX", "carolinecapital",
    "GCRClassic", "Pentosh1", "CredibleCrypto", "Bluntz_Capital", "lightcrypto",
    "CryptoHayes", "justinsuntron", "cz_binance", "brian_armstrong", "SatoshiLite",
    "VitalikButerin", "elonmusk", "CathieDWood", "saylor", "BarrySilbert",
    "michael_saylor", "jack", "TimDraper", "Chamath", "MarkCuban",
    "KevinOLeary", "RayDalio", "PaulTudorJones", "ChrisBurniske", "MikeNovogratz",
    "DanMorehead", "RaoulPal", "Melt_Dem", "CoinSharesCo", "BitwiseInvest",
    "Grayscale", "Fidelity", "MicroStrategy", "BlockFi", "PanteraCapital",
    "Polychain", "1confirmation", "DragonflyCap", "a16z", "Sequoia",
    "BessemerVP", "FoundersFund", "USVC", "CumberlandSays", "B2C2Group",
    "GSR_io", "JumpTrading", "JaneStreetGroup", "SusquehannaInt", "OptiverUS",
    "DRWTrading", "VirtuFinancial", "TowerResearch", "GalaxyDigital", "GenesisTrading",
    "NYDIG", "OspreyFunds", "ValkyrieFunds", "ProShares", "VanEck_US",
    "WisdomTreeFunds", "InvescoUS", "GlobalXUS", "Direxion", "FirstTrust",
    "StateStreet", "BlackRock", "Vanguard_Group", "MorganStanley", "GoldmanSachs"
]

NEW_100_TRADERS_V10 = list(set(NEW_100_TRADERS_V10))[:100]

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def build_offline_database_v10():
    api_key = os.getenv("SERPAPI_API_KEY")
    all_extracted_tweets = []
    
    chunks = list(chunk_list(NEW_100_TRADERS_V10, 30))
    print(f"🚀 开始执行【第十批（千人大圆满）离线打包】(Batch 10 ETL)，将最后 100 个极客/MEV/AI大V分为 {len(chunks)} 批进行极限搜索...")
    
    for i, batch in enumerate(chunks):
        sites = " OR ".join([f"site:twitter.com/{handle}" for handle in batch])
        # 强化 MEV、AI、黑客、量化算法词汇
        query = f'({sites}) ("MEV" OR "algorithm" OR "AI" OR "bot" OR "arbitrage" OR "frontrun" OR "smart contract")'
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 20
        }
        
        try:
            print(f"\n[Batch {i+1}/{len(chunks)}] 发送请求，包含 {len(batch)} 个极客大V账号...")
            res = GoogleSearch(params).get_dict()
            if "organic_results" in res:
                results = res["organic_results"]
                print(f"✅ 成功命中 {len(results)} 条顶级极客干货！")
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

    db_file = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v10.json"
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 第十批离线数据库构建完成！屯下了 {len(all_extracted_tweets)} 条极客/AI/MEV级的推文。")
    print(f"💾 数据已保存在: {db_file}")

if __name__ == "__main__":
    build_offline_database_v10()
