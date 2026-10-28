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

# Active supervisor: Keep all 3 processes alive without restarting the whole container
while true; do
  if ! kill -0 "$FWD_PID" 2>/dev/null; then
    echo "[start.sh] forwarder.py (PID $FWD_PID) exited. Restarting forwarder..."
    python forwarder.py &
    FWD_PID=$!
    echo "[start.sh] forwarder.py restarted with PID $FWD_PID"
  fi

  if ! kill -0 "$BOT_PID" 2>/dev/null; then
    echo "[start.sh] control_bot.py (PID $BOT_PID) exited. Restarting control_bot..."
    python control_bot.py &
    BOT_PID=$!
    echo "[start.sh] control_bot.py restarted with PID $BOT_PID"
  fi

  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    echo "[start.sh] web.py (PID $WEB_PID) exited. Restarting web..."
    python web.py &
    WEB_PID=$!
    echo "[start.sh] web.py restarted with PID $WEB_PID"
  fi

  sleep 5
done

