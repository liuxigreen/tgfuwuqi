import os
import json
import time
from serpapi import GoogleSearch

# 第八批 100 个真实加密账号 (重点覆盖 Memecoin 狙击手、链上 Degen、NFT 巨鲸、Airdrop 猎手和极高风险偏好的交易员)
NEW_100_TRADERS_V8 = [
    "punk6529", "CozomoMedici", "beaniemaxi", "frankdegods", "machibigbrother",
    "dingalingts", "0xb1", "CryptoISO", "DCLBlogger", "AlexBecker",
    "MuroCrypto", "CryptoKoryo", "0xTindorr", "DeFiMinty", "TheDeFinvestor",
    "CryptoNostra", "0xSalazar", "DeFi_Cheetah", "OlimpioCrypto", "DegenApe",
    "NFTGod", "Farokh", "Zeneca", "Kmoney", "Pranksy",
    "KeyboardMonkey3", "OSF_Rekt", "Mando", "GordonGoner", "DeFiIgnas",
    "DefiEdge", "TheDeFiDog", "DeFiDad", "DeFiGod", "AltcoinPsycho",
    "AltcoinSherpa", "HsakaTrades", "Ansem", "Murad", "AndrewKang",
    "Cobie", "Hasu", "TarunChitra", "RobertLeshner", "KainWarwick",
    "AntonNell", "AndreCronje", "DanieleSesta", "Banteg", "Samczsun",
    "MuditGupta", "GeorgiosKonstantopoulos", "MattHuang", "FredEhrsam", "BrianArmstrong",
    "VitalikButerin", "ArthurHayes", "BenDelo", "MichaelSaylor", "CathieWood",
    "ElonMusk", "TimDraper", "Chamath", "MarkCuban", "KevinOLeary",
    "RayDalio", "PaulTudorJones", "ChrisBurniske", "BarrySilbert", "MikeNovogratz",
    "DanMorehead", "RaoulPal", "SuZhu", "KyleDavies", "DoKwon",
    "SamBankmanFried", "CarolineEllison", "SamTrabucco", "NishadSingh", "GaryWang",
    "RyanSalame", "SatoshiNakamoto", "HalFinney", "NickSzabo", "AdamBack",
    "WeiDai", "DavidChaum", "CraigWright", "DorianNakamoto", "LenSassaman",
    "GavinAndresen", "PieterWuille", "LukeDashjr", "GregMaxwell", "WladimirVanderLaan",
    "JeffGarzik", "MikeHearn", "PeterTodd", "AmirTaaki", "AndreasAntonopoulos"
]

NEW_100_TRADERS_V8 = list(set(NEW_100_TRADERS_V8))[:100]

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def build_offline_database_v8():
    api_key = os.getenv("SERPAPI_API_KEY")
    all_extracted_tweets = []
    
    chunks = list(chunk_list(NEW_100_TRADERS_V8, 30))
    print(f"🚀 开始执行【第八批离线打包】(Batch 8 ETL)，将新 100 个链上Degen/NFT巨鲸/Memecoin狙击手分为 {len(chunks)} 批进行极限搜索...")
    
    for i, batch in enumerate(chunks):
        sites = " OR ".join([f"site:twitter.com/{handle}" for handle in batch])
        # 强化 Degen 和高风险高赔率词汇
        query = f'({sites}) ("sniper" OR "memecoin" OR "airdrop" OR "100x" OR "gem" OR "rug" OR "moonshot")'
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 20
        }
        
        try:
            print(f"\n[Batch {i+1}/{len(chunks)}] 发送请求，包含 {len(batch)} 个Degen大V账号...")
            res = GoogleSearch(params).get_dict()
            if "organic_results" in res:
                results = res["organic_results"]
                print(f"✅ 成功命中 {len(results)} 条极高风险的链上干货！")
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

    db_file = "/workspace/.claude/skills/crypto-trader-framework/references/sources/offline_tweets_database_v8.json"
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 第八批离线数据库构建完成！屯下了 {len(all_extracted_tweets)} 条极高风险的推文。")
    print(f"💾 数据已保存在: {db_file}")

if __name__ == "__main__":
    build_offline_database_v8()
