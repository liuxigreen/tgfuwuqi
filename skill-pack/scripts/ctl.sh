#!/bin/bash
# AgentHansa 一键管理脚本
# 用法: bash ctl.sh [start|stop|status|restart|log]
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$DIR/memory/hansa.pid"
LOG_FILE="$DIR/logs/hansa-daemon.log"
SCRIPT="$DIR/agenthansa-hansa.py"

mkdir -p "$DIR/memory" "$DIR/logs"

case "${1:-status}" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "already_running $(cat "$PID_FILE")"
      exit 0
    fi
    nohup python3 -u "$SCRIPT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 0.5
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "started $(cat "$PID_FILE")"
    else
      echo "failed"
      cat "$LOG_FILE" | tail -5
    fi
    ;;
  stop)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      kill "$(cat "$PID_FILE")"
      echo "stopped $(cat "$PID_FILE")"
      rm -f "$PID_FILE"
    else
      echo "not_running"
      rm -f "$PID_FILE"
    fi
    ;;
  restart)
    bash "$0" stop
    sleep 1
    bash "$0" start
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "running $(cat "$PID_FILE")"
    else
      echo "not_running"
    fi
    ;;
  log)
    tail -${2:-30} "$LOG_FILE"
    ;;
  *)
    echo "usage: ctl.sh [start|stop|status|restart|log [N]]"
    ;;
esac
