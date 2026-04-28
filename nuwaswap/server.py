from fastapi import FastAPI
import uvicorn
from live_yaobi_diagnoser import fetch_mock_coin_data, calculate_yaobi_score

# ---------------------------------------------------------
# 女娲系统：后端 API 服务 (为前端 Agent 提供遥控器)
# 作用：部署在 2G VPS 上，全天候接受 Agent 的调用指令
# ---------------------------------------------------------

app = FastAPI(title="Nuwa Agent TradeKit API")

@app.get("/")
def health_check():
    """健康检查接口：Agent 确认后台是否存活"""
    return {
        "status": "online", 
        "system": "Nuwa Trading Engine", 
        "cpu_usage": "relaxing", 
        "memory_usage": "sufficient"
    }

@app.get("/diagnose/{symbol}")
def diagnose_coin(symbol: str):
    """核心接口：Agent 请求分析代币妖气值"""
    symbol = symbol.upper()
    
    # 1. 后端去爬取数据 (不占用 Agent 的思考时间)
    data = fetch_mock_coin_data(symbol)
    
    # 2. 调用 100 分制模型打分
    score, breakdown = calculate_yaobi_score(data)
    
    # 3. 给出初步建议 (提报给 Agent 审批)
    preliminary_action = "WAIT (观望)"
    if score > 80:
        if data.get("market_cap_usd", 0) > 30000000:
            preliminary_action = "SHORT (建议做空，庄家派发期)"
        else:
            preliminary_action = "LONG_SNIPE (建议小仓位潜伏做多)"
            
    return {
        "symbol": symbol,
        "score": score,
        "breakdown": breakdown,
        "preliminary_action": preliminary_action,
        "message": "请 Agent 总监根据以上得分和建议，向用户转述并下达最终开单授权。"
    }

if __name__ == "__main__":
    # 运行在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)