#!/bin/bash
export PYTHONUNBUFFERED=1
export PYTHONOPTIMIZE=1
export MALLOC_ARENA_MAX=2
export MALLOC_TRIM_THRESHOLD_=65536

cleanup() {
  echo "[start.sh] Terminating all processes..."
  kill -TERM "$FWD_PID" "$BOT_PID" "$WEB_PID" 2>/dev/null
  sleep 2
  kill -9 "$FWD_PID" "$BOT_PID" "$WEB_PID" 2>/dev/null
  exit 0
}

trap cleanup SIGTERM SIGINT

# 1. Forwarder engine
python forwarder.py &
FWD_PID=$!
echo "[start.sh] Forwarder engine started with PID $FWD_PID"

# 2. Control Bot
python control_bot.py &
BOT_PID=$!
echo "[start.sh] Control Bot started with PID $BOT_PID"

# 3. Web server
python web.py &
WEB_PID=$!
echo "[start.sh] Web server started with PID $WEB_PID"

# Active supervisor: If ANY process crashes or runs out of memory, restart container
while true; do
  if ! kill -0 "$FWD_PID" 2>/dev/null; then
    echo "[start.sh] ALERT: forwarder.py (PID $FWD_PID) stopped! Restarting container..."
    cleanup
    exit 1
  fi
  if ! kill -0 "$BOT_PID" 2>/dev/null; then
    echo "[start.sh] ALERT: control_bot.py (PID $BOT_PID) stopped! Restarting container..."
    cleanup
    exit 1
  fi
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    echo "[start.sh] ALERT: web.py (PID $WEB_PID) stopped! Restarting container..."
    cleanup
    exit 1
  fi
  sleep 5
done
