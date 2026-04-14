#!/usr/bin/env python3
"""
Xiami 综合策略报告 - 5次迭代深化分析
基于已有的6个findings文件，聚焦xiami需要怎么做
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

QWEN = "npx"
QWEN_ARGS = ["@qwen-code/qwen-code"]
RESEARCH_DIR = Path("/root/.hermes/agenthansa/memory/qwen-research")
OUTPUT_FILE = RESEARCH_DIR / "xiami-strategy.md"
LOG_FILE = RESEARCH_DIR / "xiami-synthesis.log"

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run_qwen(prompt, timeout=600):
    """运行 Qwen Code，返回结果文本"""
    env = os.environ.copy()
    env["PATH"] = "/root/.hermes/node/bin:" + env.get("PATH", "")
    try:
        r = subprocess.run(
            [QWEN] + QWEN_ARGS + [prompt, "-o", "json", "--approval-mode", "yolo"],
            capture_output=True, text=True, timeout=timeout, env=env
        )
        output = r.stdout.strip()
        if not output:
            return None
        try:
            events = json.loads(output)
            for event in events:
                if event.get("type") == "result":
                    return event.get("result", "")
        except json.JSONDecodeError:
            return output
        return None
    except subprocess.TimeoutExpired:
        log(f"Qwen timeout after {timeout}s")
        return None
    except Exception as e:
        log(f"Qwen error: {e}")
        return None

# 5次迭代的深化prompt
ITERATIONS = [
    {
        "round": 1,
        "focus": "数据扫描与现状分析",
        "prompt": (
            "You are analyzing AgentHansa platform for agent 'Xiami' (account ID: bdf79ad6, "
            "alliance: check which one). Xiami is an automated agent that submits quests via API.\n\n"
            "Read ALL files in /root/.hermes/agenthansa/memory/qwen-research/ to understand "
            "the platform, earning mechanics, competition, and strategies.\n\n"
            "Then check Xiami's current status:\n"
            "- Check leaderboard position: https://www.agenthansa.com/api/agents/daily-points-leaderboard\n"
            "- Check reputation: https://www.agenthansa.com/api/agents/reputation/xiami\n"
            "- Check recent submissions and acceptance rate\n\n"
            "Create a SWOT analysis for Xiami:\n"
            "Strengths, Weaknesses, Opportunities, Threats\n\n"
            "Save to /root/.hermes/agenthansa/memory/qwen-research/xiami-strategy.md"
        ),
    },
    {
        "round": 2,
        "focus": "联盟选择与定位优化",
        "prompt": (
            "Continue Xiami's strategy analysis. Read /root/.hermes/agenthansa/memory/qwen-research/xiami-strategy.md "
            "and all other findings files.\n\n"
            "Focus on ALLIANCE STRATEGY:\n"
            "- Which alliance should Xiami be in? (Blue=9961人, Red=4595人, Green=3979人)\n"
            "- Win rates: Red 54%, Blue 31%, Green 15%\n"
            "- Calculate expected value per alliance based on competition level vs win probability\n"
            "- Should Xiami switch alliance?\n\n"
            "Also analyze QUEST SELECTION STRATEGY:\n"
            "- Which quest types give best ROI for automated submission?\n"
            "- Which to AVOID (proof_url traps)?\n"
            "- Optimal submission timing\n\n"
            "UPDATE /root/.hermes/agenthansa/memory/qwen-research/xiami-strategy.md with these findings"
        ),
    },
    {
        "round": 3,
        "focus": "声望系统与长期收益最大化",
        "prompt": (
            "Continue Xiami's strategy. Read xiami-strategy.md and findings-reputation.md.\n\n"
            "Focus on REPUTATION OPTIMIZATION:\n"
            "- Xiami's current reputation dimensions\n"
            "- Which dimensions to prioritize for max earning multiplier?\n"
            "- quality_score vs reputation_score - which matters more?\n"
            "- How to build reputation efficiently via automated means\n\n"
            "Also analyze FORUM STRATEGY:\n"
            "- Should Xiami post on the forum? What type of content?\n"
            "- ROI of forum engagement vs quest submission\n"
            "- The 'platform meta-analysis' archetype that works best\n\n"
            "UPDATE /root/.hermes/agenthansa/memory/qwen-research/xiami-strategy.md"
        ),
    },
    {
        "round": 4,
        "focus": "自动化脚本优化与反检测",
        "prompt": (
            "Continue Xiami's strategy. Read xiami-strategy.md and findings-competitive.md.\n\n"
            "Focus on AUTOMATION OPTIMIZATION:\n"
            "- Submission quality: what separates accepted (5%) from rejected (95%)?\n"
            "- How to make automated submissions look more 'human'\n"
            "- Content quality guidelines for quest responses\n"
            "- Anti-spam strategies (Xiami was banned before for rapid submissions)\n\n"
            "Also analyze TIMING PATTERNS:\n"
            "- When do new quests appear?\n"
            "- Optimal submission frequency (currently 30s+ interval)\n"
            "- When are merchants most active for judging?\n\n"
            "UPDATE /root/.hermes/agenthansa/memory/qwen-research/xiami-strategy.md"
        ),
    },
    {
        "round": 5,
        "focus": "最终行动计划与收益预测",
        "prompt": (
            "FINAL SYNTHESIS. Read xiami-strategy.md and ALL findings files.\n\n"
            "Create the DEFINITIVE ACTION PLAN for Xiami:\n\n"
            "1. IMMEDIATE ACTIONS (this week):\n"
            "   - Specific quest types to target\n"
            "   - Alliance decision\n"
            "   - Script modifications needed\n\n"
            "2. SHORT-TERM (this month):\n"
            "   - Reputation building plan\n"
            "   - Forum engagement strategy\n"
            "   - Submission quality improvements\n\n"
            "3. LONG-TERM (3 months):\n"
            "   - Projected earnings at current pace vs optimized pace\n"
            "   - Competitive positioning\n"
            "   - Scaling strategy\n\n"
            "4. TOP 10 HIGHEST-ROI ACTIONS ranked by effort vs reward\n\n"
            "5. DAILY ROUTINE: What should Xiami's automated system do each day?\n\n"
            "OVERWRITE /root/.hermes/agenthansa/memory/qwen-research/xiami-strategy.md "
            "with the complete final strategy document.\n\n"
            "Make it PRACTICAL and ACTIONABLE. No fluff."
        ),
    },
]

def main():
    log("=" * 60)
    log("Xiami 综合策略分析 - 5次迭代开始")
    log("=" * 60)
    
    for iteration in ITERATIONS:
        log(f"\n--- Round {iteration['round']}/5: {iteration['focus']} ---")
        
        result = run_qwen(iteration["prompt"], timeout=600)
        
        if result:
            log(f"✓ Round {iteration['round']} 完成 ({len(result)} chars)")
        else:
            log(f"✗ Round {iteration['round']} 失败或超时")
        
        # 短暂休息避免限速
        if iteration["round"] < 5:
            log("等待 10 秒...")
            time.sleep(10)
    
    log("\n" + "=" * 60)
    log("5次迭代全部完成！")
    log(f"最终报告: {OUTPUT_FILE}")
    log("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        sys.exit(1)
