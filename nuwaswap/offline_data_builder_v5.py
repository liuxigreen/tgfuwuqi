import os
import json
import time
from serpapi import GoogleSearch

# 第五批 100 个真实加密账号 (专注高阶衍生品交易员, 期权分析师, 算法套利者, 以及一些实战派老兵)
NEW_100_TRADERS_V5 = [
    "ThinkingCrypto1", "KoroushAK", "rektcapital", "SmartContracter", "CryptoGainz1", 
    "Crypto_Chase", "Crypto_McKenna", "Crypto_Macro", "Crypto_BULL_", "Crypto_Core_", 
    "lightcrypto", "loomdart", "inversebrah", "ZeusZissou", "Trader_Dante", 
    "CarpeNoctom", "filbfilb", "VentureCoinist", "scottmelker", "PeterLBrandt", 
    "woonomic", "100trillionUSD", "CeterisPar1bus", "ThinkingMACRO", "RaoulGMI", 
    "hasufl", "KyleLDavies", "AlamedaTrabucco", "EvgenyGaevoy", "kaiynne", 
    "Arthur_0x", "ki_young_ju", "WillyWoo", "ToneVays", "B_B_C_C", 
    "CryptoWendyO", "APompliano", "AltcoinDailyio", "IvanOnTech", "Bitboy_Crypto", 
    "JRNYcrypto", "elliotrades", "TheMoonCarl", "DatDashCom", "CryptoBusy", 
    "CryptoLark", "Boxmining", "Nicholas_Merten", "CryptoJebb", "AltcoinBuzzio", 
    "blknoiz06", "CL207", "AviFelman", "Rewkang", "0xENAS", 
    "kamikaz_ETH", "WClementeIII", "DylanLeClair_", "krugermacro", "joemccann", 
    "cburniske", "RyanSAdams", "TrustlessState", "ercwl", "udiWertheimer", 
    "zachxbt", "carolinecapital", "NorthRockLP", "gametheorizing", "mewn21", 
    "Tetranode", "0xSisyphus", "dcfgod", "IcedKnife", "Fiskantes", 
    "CryptoYoda1338", "nansen_intern", "ASvanevik", "BarrySilbert", "saylor", 
    "CathieDWood", "milesdeutscher", "LadyofCrypto1", "Ashcryptoreal", "CryptoRover", 
    "cryptojack", "MartiniGuyYT", "MMCrypto", "danheld", "TechDev_52", 
    "intocryptoverse", "BobLoukas", "jasonpizzino", "Sheldon_Sniper", "crypto_banter", 
    "TraderKoz", "Tradermayne", "pierre_crypt0", "UpOnlyTV", "mrjasonchoi"
]

NEW_100_TRADERS_V5 = list(set(NEW_100_TRADERS_V5))[:100]

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def build_offline_database_v5():
    api_key = os.getenv("SERPAPI_API_KEY")
    all_extracted_tweets = []
    
    chunks = list(chunk_list(NEW_100_TRADERS_V5, 30))
    print(f"🚀 开始执行【第五批离线打包】(Batch 5 ETL)，将新 100 个实战派/衍生品大V分为 {len(chunks)} 批进行极限搜索...")
    
    for i, batch in enumerate(chunks):
        sites = " OR ".join([f"site:twitter.com/{handle}" for handle in batch])
        # 增加期权、对冲、极值等衍生品词汇
        query = f'({sites}) ("options" OR "funding rate" OR "liquidations" OR "stop loss" OR "squeeze" OR "delta" OR "gamma")'
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 20
        }
        
        try:
            print(f"\n[Batch {i+1}/{len(chunks)}] 发送请求，包含 {len(batch)} 个实战大V账号...")
            res = GoogleSearch(params).get_dict()
            if "organic_results" in res:
                results = res["organic_results"]
                print(f"✅ 成功命中 {len(results)} 条实战级衍生品干货！")
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

    db_file = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v5.json"
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 第五批离线数据库构建完成！屯下了 {len(all_extracted_tweets)} 条极高质量的衍生品/实战级推文。")
    print(f"💾 数据已保存在: {db_file}")

if __name__ == "__main__":
    build_offline_database_v5()
