#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${AGENTHANSA_REPO_DIR:-/workspace/agenthansa}"
BRANCH="${AGENTHANSA_UPLOAD_BRANCH:-codex/review-api-documentation-for-leaderboard-scores-2vsk0j}"
TAIL_LINES="${AGENTHANSA_LOG_TAIL_LINES:-5000}"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "ERROR: repo not found at $REPO_DIR"
  exit 1
fi

cd "$REPO_DIR"
mkdir -p logs runtime

# 用空全局配置，避免宿主机 git inSteadOf 把 SSH 重写成 HTTPS。
GIT_CONFIG_GLOBAL=/dev/null git fetch origin "$BRANCH:$BRANCH" >/dev/null 2>&1 || true
GIT_CONFIG_GLOBAL=/dev/null git checkout "$BRANCH" >/dev/null 2>&1 || GIT_CONFIG_GLOBAL=/dev/null git checkout -b "$BRANCH"

python3 agenthansa-log-ingest.py --output-dir logs --tail-lines "$TAIL_LINES"
python3 agenthansa-log-analyze.py --logs-dir logs > logs/REPORT.md
python3 agenthansa-auto-tune.py --logs-dir logs --output-env runtime/agenthansa-tuned.env > logs/AUTO_TUNE.txt

# 强制追踪被 .gitignore 忽略的日志/报告文件
GIT_CONFIG_GLOBAL=/dev/null git add -f \
  logs/auto.log \
  logs/redpacket.log \
  logs/task-summary.jsonl \
  logs/redpacket-summary.jsonl \
  logs/REPORT.md \
  logs/AUTO_TUNE.txt \
  runtime/agenthansa-tuned.env 2>/dev/null || true

if GIT_CONFIG_GLOBAL=/dev/null git diff --cached --quiet; then
  echo "NO_CHANGES"
  exit 0
fi

TS="$(date +%Y%m%d-%H%M%S)"
GIT_CONFIG_GLOBAL=/dev/null git commit -m "chore: upload AgentHansa logs + report (${TS})" >/dev/null
GIT_CONFIG_GLOBAL=/dev/null git push origin "$BRANCH" >/dev/null

HASH="$(GIT_CONFIG_GLOBAL=/dev/null git rev-parse --short HEAD)"
echo "UPLOADED branch=${BRANCH} commit=${HASH}"
