import os
import json
import time
from serpapi import GoogleSearch

# 第六批 100 个真实加密账号 (专注极早期 OG, 匿名巨鲸, 链上追踪的大户, 算法猎手)
NEW_100_TRADERS_V6 = [
    "cz_binance", "VitalikButerin", "brian_armstrong", "SatoshiLite", "jespow",
    "gavofyork", "aantonop", "ErikVoorhees", "NickSzabo4", "jimmysong",
    "dan_pantera", "novogratz", "barrysilbert", "cameron", "tyler",
    "michael_saylor", "jack", "elonmusk", "CathieDWood", "RaoulGMI",
    "100trillionUSD", "woonomic", "PeterLBrandt", "ToneVays", "TuurDemeester",
    "filbfilb", "B_B_C_C", "cryptomanran", "AltcoinDailyio", "IvanOnTech",
    "Bitboy_Crypto", "JRNYcrypto", "elliotrades", "TheMoonCarl", "CryptoLark",
    "Boxmining", "Nicholas_Merten", "CryptoJebb", "AltcoinBuzzio", "DatDashCom",
    "0xMaki", "bantg", "AndreCronjeTech", "danielesesta", "RuneKek",
    "StaniKulechov", "haydenzadams", "rleshner", "tarunchitra", "samczsun",
    "Mudit__Gupta", "0xfoobar", "gakonst", "matthuang", "FEhrsam",
    "twobitidiot", "MessariCrypto", "Delphi_Digital", "nansen_ai", "ArkhamIntel",
    "zhusu", "KyleLDavies", "AlamedaTrabucco", "EvgenyGaevoy", "kaiynne",
    "CryptoHayes", "justinsuntron", "SBF_FTX", "carolinecapital", "garywang",
    "nishadsingh", "loomdart", "DegenSpartan", "Awilaby", "inversebrah",
    "ledgerstatus", "VentureCoinist", "scottmelker", "CryptoWendyO", "APompliano",
    "Pentosh1", "CredibleCrypto", "Bluntz_Capital", "lightcrypto", "GCRClassic",
    "Crypto_Macro", "Crypto_BULL_", "Crypto_Core_", "Crypto_Chase", "Crypto_McKenna",
    "SmartContracter", "CryptoGainz1", "rektcapital", "KoroushAK", "ThinkingCrypto1",
    "AngeloBTC", "CryptoCobain", "CryptoDonAlt", "CanteringClark", "IncomeSharks"
]

NEW_100_TRADERS_V6 = list(set(NEW_100_TRADERS_V6))[:100]

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def build_offline_database_v6():
    api_key = os.getenv("SERPAPI_API_KEY")
    all_extracted_tweets = []
    
    chunks = list(chunk_list(NEW_100_TRADERS_V6, 30))
    print(f"🚀 开始执行【第六批离线打包】(Batch 6 ETL)，将新 100 个早期巨鲸/隐秘大户分为 {len(chunks)} 批进行极限搜索...")
    
    for i, batch in enumerate(chunks):
        sites = " OR ".join([f"site:twitter.com/{handle}" for handle in batch])
        # 增加宏观周期、巨鲸建仓、逃顶等词汇
        query = f'({sites}) ("accumulation" OR "distribution" OR "cycle" OR "top" OR "bottom" OR "halving" OR "capitulation")'
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 20
        }
        
        try:
            print(f"\n[Batch {i+1}/{len(chunks)}] 发送请求，包含 {len(batch)} 个巨鲸/OG账号...")
            res = GoogleSearch(params).get_dict()
            if "organic_results" in res:
                results = res["organic_results"]
                print(f"✅ 成功命中 {len(results)} 条巨鲸级宏观/周期干货！")
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

    db_file = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v6.json"
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 第六批离线数据库构建完成！屯下了 {len(all_extracted_tweets)} 条极高质量的巨鲸/宏观级推文。")
    print(f"💾 数据已保存在: {db_file}")

if __name__ == "__main__":
    build_offline_database_v6()
