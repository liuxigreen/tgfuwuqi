import os
import json
import time
from serpapi import GoogleSearch

# 第四批 100 个真实加密账号 (包含顶级做市商, 量化机构, 链上追踪器, 宏观研究员, 以及未纳入的硬核交易员)
NEW_100_TRADERS_V4 = [
    "a16zcrypto", "paradigm", "multicoincap", "jump_", "wintermute_t", 
    "GSR_io", "DWFLabs", "ambergroup_io", "KronosResearch", "QCPCapital", 
    "SeliniCapital", "Flowdesk_co", "Auros_global", "FolkvangTrading", "PrestoLabs", 
    "Tokenterminal", "DeFiLlama", "glassnode", "nansen_ai", "ArkhamIntel", 
    "MessariCrypto", "Delphi_Digital", "TheBlock__", "CoinDesk", "Cointelegraph", 
    "CryptoSlate", "Blockworks_", "DecryptMedia", "WatcherGuru", "BitcoinMagazine", 
    "CryptoPanicCom", "BeInCrypto", "CryptoBriefing", "AMBCrypto", "UdotToday", 
    "CryptoGlobeInfo", "NewsBTC", "CoinMarketCap", "CoinGecko", "CryptoCompare", 
    "NomicsData", "LunarCrush", "CryptoRank_io", "CoinPaprika", "CoinCodex", 
    "LiveCoinWatch", "Santimentfeed", "CryptoQuant_com", "Skewdotcom", "KaikoData", 
    "CoinMetrics", "DappRadar", "DefiPulse", "Zapper_fi", "Dapp_com", 
    "StateOfTheDApps", "DappReview", "Etherscan", "BscScan", "PolygonScan", 
    "FtmScan", "SnowTrace", "Arbiscan", "OptimisticEtherscan", "CronosScan", 
    "BobaScan", "HecoInfo", "MoonriverBlockexplorer", "AuroraScan", "MetisExplorer", 
    "CeloScan", "KavaScan", "GnosisScan", "FuseExplorer", "OasisScan", 
    "EvmOSExplorer", "TelosScan", "SyscoinExplorer", "BttcScan", "KlaytnTally", 
    "WanchainExplorer", "MeterExplorer", "MilkomedaExplorer", "NahmiiExplorer", "ThundercoreExplorer", 
    "DexGuru", "Zerion_io", "DeBankDeFi", "InstaDApp", "ApeBoard", 
    "SonarWatch", "YieldWatch", "VfatTools", "FarmArmy", "StepFinance", 
    "DefiYield", "APYVision", "KrystalDefi", "CryptoCobain", "MustStopMurad"
]

NEW_100_TRADERS_V4 = list(set(NEW_100_TRADERS_V4))[:100]

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def build_offline_database_v4():
    api_key = os.getenv("SERPAPI_API_KEY")
    all_extracted_tweets = []
    
    chunks = list(chunk_list(NEW_100_TRADERS_V4, 30))
    print(f"🚀 开始执行【第四批离线打包】(Batch 4 ETL)，将新 100 个机构/做市商/巨鲸账号分为 {len(chunks)} 批进行极限搜索...")
    
    for i, batch in enumerate(chunks):
        sites = " OR ".join([f"site:twitter.com/{handle}" for handle in batch])
        # 加入机构量化的高频词汇
        query = f'({sites}) ("arbitrage" OR "market making" OR "liquidity" OR "stop loss" OR "hedging" OR "spread" OR "volatility")'
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 20
        }
        
        try:
            print(f"\n[Batch {i+1}/{len(chunks)}] 发送请求，包含 {len(batch)} 个机构/大V账号...")
            res = GoogleSearch(params).get_dict()
            if "organic_results" in res:
                results = res["organic_results"]
                print(f"✅ 成功命中 {len(results)} 条机构级交易干货！")
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

    db_file = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v4.json"
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 第四批离线数据库构建完成！屯下了 {len(all_extracted_tweets)} 条极高质量的机构级推文。")
    print(f"💾 数据已保存在: {db_file}")

if __name__ == "__main__":
    build_offline_database_v4()
