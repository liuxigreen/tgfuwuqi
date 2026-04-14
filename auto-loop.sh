#!/bin/bash
# AgentHansa 自动循环 — V7 全收入流水线
# 融合：签到/streak + 红包 + quest提交 + collective bounties + 论坛发帖 + 论坛互动 + 排名追击
# 反spam：失败熔断 + 间隔随机化 + 凌晨加密度
# 红包由独立sniper进程处理，不受影响
PID_FILE="/root/.hermes/agenthansa/memory/auto-loop.pid"
LOG="/root/.hermes/agenthansa/logs/auto-loop.log"
HOURLY_CHECK="/root/.hermes/agenthansa/agenthansa-hourly-check.py"
HISTORY="/root/.hermes/agenthansa/memory/submission-history.jsonl"
ENV_FILE="/root/.hermes/agenthansa/.env.agenthansa"
ROUND=0
CONSECUTIVE_SPAM=0
MAX_CONSECUTIVE_SPAM=3

# 脚本路径
CHECKIN="/root/.hermes/agenthansa/agenthansa-checkin.py"
FORUM_DAILY="/root/.hermes/agenthansa/forum-daily.py"
FORUM_INTERACT="/root/.hermes/agenthansa/forum-interact.py"
AUTO_PY="/root/.hermes/agenthansa/agenthansa-auto.py"
BOUNTIES_PY="/root/.hermes/agenthansa/agenthansa-bounties.py"
RETRY_PY="/root/.hermes/agenthansa/retry-failed-quests.py"
RANK_CHASE="/root/.hermes/agenthansa/rank-chase.py"
OPTIMIZER="/root/.hermes/agenthansa/auto-optimizer.py"

# 加载环境变量
if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
fi

mkdir -p /root/.hermes/agenthansa/memory /root/.hermes/agenthansa/logs

echo $$ > "$PID_FILE"
echo "[$(date '+%H:%M:%S')] 自动循环启动 V6 (全收入流水线, 熔断=连续${MAX_CONSECUTIVE_SPAM}次spam冷却2h)" >> "$LOG"

# ========== 函数 ==========

check_spam_burst() {
    # 检查最近N条submission是否连续spamed
    if [ ! -f "$HISTORY" ]; then
        echo "0"
        return
    fi
    local count=0
    while IFS= read -r line; do
        if echo "$line" | grep -qi "spam\|paused\|velocity\|429"; then
            count=$((count + 1))
        else
            count=0
        fi
    done < <(tail -"$MAX_CONSECUTIVE_SPAM" "$HISTORY")
    echo "$count"
}

do_checkin() {
    # 每日签到（脚本内部判断是否已签）
    echo "[$(date '+%H:%M:%S')] [签到] 执行..." >> "$LOG"
    python3 "$CHECKIN" >> "$LOG" 2>&1
}

do_forum_post() {
    # 每日论坛发帖（脚本内部判断是否已发）
    echo "[$(date '+%H:%M:%S')] [论坛] 发帖..." >> "$LOG"
    python3 "$FORUM_DAILY" >> "$LOG" 2>&1
}

do_side_quests() {
    # Side quests微任务 ($0.03/个)
    echo "[$(date '+%H:%M:%S')] [SideQuest] 检查..." >> "$LOG"
    python3 /root/.hermes/agenthansa/agenthansa-side-quests.py >> "$LOG" 2>&1
}

do_forum_interact() {
    # 论坛互动（upvote 3-5个帖子）
    echo "[$(date '+%H:%M:%S')] [论坛] 互动..." >> "$LOG"
    python3 "$FORUM_INTERACT" >> "$LOG" 2>&1
}

do_quest_submit() {
    # 主quest提交逻辑
    echo "[$(date '+%H:%M:%S')] [Quest] 主逻辑..." >> "$LOG"
    python3 "$AUTO_PY" >> "$LOG" 2>&1
    
    # 检查是否触发spam
    local spam_count
    spam_count=$(check_spam_burst)
    if [ "$spam_count" -ge "$MAX_CONSECUTIVE_SPAM" ]; then
        CONSECUTIVE_SPAM=$((CONSECUTIVE_SPAM + 1))
        echo "[$(date '+%H:%M:%S')] ⚠️ 连续spam $spam_count 次! 冷却2h" >> "$LOG"
        sleep 7200
        CONSECUTIVE_SPAM=0
    else
        CONSECUTIVE_SPAM=0
    fi
}

do_bounties() {
    # Collective bounties — 自动join+提交
    echo "[$(date '+%H:%M:%S')] [Bounty] 检查collective bounties..." >> "$LOG"
    python3 "$BOUNTIES_PY" >> "$LOG" 2>&1
}

do_retry() {
    # 失败quest重试
    echo "[$(date '+%H:%M:%S')] [重试] 失败quest..." >> "$LOG"
    python3 "$RETRY_PY" >> "$LOG" 2>&1
}

do_hourly_check() {
    # 每小时检查
    echo "[$(date '+%H:%M:%S')] [巡检] 小时检查..." >> "$LOG"
    python3 "$HOURLY_CHECK" >> "$LOG" 2>&1
    echo "[$(date '+%H:%M:%S')] [巡检] 完成" >> "$LOG"
}

do_rank_chase() {
    # 排名追击（北京时间13-14点）
    HOUR=$((10#$(date '+%H')))
    if [[ "$HOUR" -eq 13 || "$HOUR" -eq 14 ]]; then
        echo "[$(date '+%H:%M:%S')] [追击] 排名追击..." >> "$LOG"
        python3 "$RANK_CHASE" >> "$LOG" 2>&1
    fi
}

do_optimizer() {
    # 每12轮自动优化
    if (( ROUND % 12 == 0 )); then
        echo "[$(date '+%H:%M:%S')] [优化] 自动优化分析..." >> "$LOG"
        python3 "$OPTIMIZER" >> "$LOG" 2>&1
    fi
}

calc_sleep() {
    # 计算间隔：凌晨加密度 + 随机化
    HOUR=$((10#$(date '+%H')))
    if [[ "$HOUR" -ge 4 && "$HOUR" -le 7 ]]; then
        # 北京时间4-7AM：任务大爆发，加密度
        DELAY=$((1500 + RANDOM % 1200))
        echo "[$(date '+%H:%M:%S')] 🔥 凌晨加密度, ${DELAY}s后重试 (25-45min)" >> "$LOG"
    else
        # 常规：40-90min
        DELAY=$((2400 + RANDOM % 3000))
        echo "[$(date '+%H:%M:%S')] 常规模式, ${DELAY}s后重试 (40-90min)" >> "$LOG"
    fi
    echo "$DELAY"
}

# ========== 主循环 ==========

while true; do
    ROUND=$((ROUND + 1))
    echo "" >> "$LOG"
    echo "[$(date '+%H:%M:%S')] ==================== 轮次#${ROUND} ====================" >> "$LOG"
    
    # 1. 签到（每天1次，内部判断）
    do_checkin
    
    # 2. Quest提交（含熔断）
    do_quest_submit
    
    # 3. Collective bounties — 自动join+提交
    do_bounties

    # 4. 失败重试
    do_retry
    
    # 5. 论坛发帖（每天1帖，内部判断）
    do_forum_post
    
    # 5. 论坛互动（upvote 3-5个，每天上限5次）
    do_forum_interact

    # 5.5. Side Quests微任务（$0.03/个）
    do_side_quests
    
    # 6. 每小时检查
    do_hourly_check
    
    # 7. 排名追击（特定时段）
    do_rank_chase
    
    # 8. 自动优化（每12轮）
    do_optimizer
    
    # 9. 计算并sleep
    DELAY=$(calc_sleep)
    sleep "$DELAY"
done
