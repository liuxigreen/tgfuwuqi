import os
import json
import time
from serpapi import GoogleSearch

# 第七批 100 个真实加密账号 (专注高频剥头皮 Scalpers、日内交易员 Day Traders、以及跨周期量化模型)
NEW_100_TRADERS_V7 = [
    "Trader_XO", "ColdBloodShill", "TheCryptoDog", "inmortalcrypto", "CryptoTony__",
    "ByzGeneral", "AltcoinGordon", "crypto_birb", "CryptoCapo_", "MacnBTC",
    "SatoshiFlippin", "cryptCred", "LomahCrypto", "Crypto_Ed_NL", "CryptoMichNL",
    "CryptoGodJohn", "devchart", "Nebraskangooner", "TheCryptoCactus", "CryptoNewton",
    "IncomeSharks", "CanteringClark", "CryptoDonAlt", "CryptoCobain", "AngeloBTC",
    "ThinkingCrypto1", "KoroushAK", "rektcapital", "SmartContracter", "CryptoGainz1",
    "Crypto_Chase", "Crypto_McKenna", "Crypto_Macro", "Crypto_BULL_", "Crypto_Core_",
    "GCRClassic", "Pentosh1", "CredibleCrypto", "Bluntz_Capital", "lightcrypto",
    "CryptoHayes", "SBF_FTX", "zhusu", "Awilaby", "DegenSpartan",
    "loomdart", "inversebrah", "DaanCrypto", "ZeusZissou", "Trader_Dante",
    "CryptoCred", "ledgerstatus", "CarpeNoctom", "filbfilb", "VentureCoinist",
    "scottmelker", "PeterLBrandt", "woonomic", "100trillionUSD", "CeterisPar1bus",
    "cobie", "ThinkingMACRO", "RaoulGMI", "hasufl", "KyleLDavies",
    "AlamedaTrabucco", "EvgenyGaevoy", "kaiynne", "justinsuntron", "cz_binance",
    "brian_armstrong", "SatoshiLite", "VitalikButerin", "Arthur_0x", "ki_young_ju",
    "WillyWoo", "ToneVays", "B_B_C_C", "cryptomanran", "CryptoWendyO",
    "APompliano", "AltcoinDailyio", "IvanOnTech", "Bitboy_Crypto", "JRNYcrypto",
    "elliotrades", "TheMoonCarl", "DatDashCom", "CryptoBusy", "CryptoLark",
    "Boxmining", "Nicholas_Merten", "CryptoJebb", "AltcoinBuzzio", "blknoiz06",
    "CL207", "AviFelman", "Rewkang", "0xENAS", "kamikaz_ETH"
]

NEW_100_TRADERS_V7 = list(set(NEW_100_TRADERS_V7))[:100]

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def build_offline_database_v7():
    api_key = os.getenv("SERPAPI_API_KEY")
    all_extracted_tweets = []
    
    chunks = list(chunk_list(NEW_100_TRADERS_V7, 30))
    print(f"🚀 开始执行【第七批离线打包】(Batch 7 ETL)，将新 100 个高频/日内/跨周期大V分为 {len(chunks)} 批进行极限搜索...")
    
    for i, batch in enumerate(chunks):
        sites = " OR ".join([f"site:twitter.com/{handle}" for handle in batch])
        # 强化高频短线词汇，试图激活 5m 和 15m 的极限性能
        query = f'({sites}) ("scalp" OR "day trade" OR "high frequency" OR "tick" OR "micro" OR "intraday" OR "quick")'
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 20
        }
        
        try:
            print(f"\n[Batch {i+1}/{len(chunks)}] 发送请求，包含 {len(batch)} 个高频大V账号...")
            res = GoogleSearch(params).get_dict()
            if "organic_results" in res:
                results = res["organic_results"]
                print(f"✅ 成功命中 {len(results)} 条高频短线交易干货！")
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

    db_file = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v7.json"
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 第七批离线数据库构建完成！屯下了 {len(all_extracted_tweets)} 条极高质量的高频/短线推文。")
    print(f"💾 数据已保存在: {db_file}")

if __name__ == "__main__":
    build_offline_database_v7()
