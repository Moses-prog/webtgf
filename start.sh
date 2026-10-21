#!/bin/bash
export PYTHONUNBUFFERED=1
export MALLOC_ARENA_MAX=2

cleanup() {
  echo "[start.sh] SIGTERM/SIGINT received. Terminating all processes cleanly..."
  kill -TERM "$FWD_PID" "$BOT_PID" "$WEB_PID" 2>/dev/null
  wait "$FWD_PID" "$BOT_PID" "$WEB_PID" 2>/dev/null
  exit 0
}

trap cleanup SIGTERM SIGINT

# 1. Forwarder engine
python forwarder.py &
FWD_PID=$!

# 2. Control Bot
python control_bot.py &
BOT_PID=$!

# 3. Web server
python web.py &
WEB_PID=$!

wait $WEB_PID
cleanup
