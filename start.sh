#!/bin/bash
export PYTHONUNBUFFERED=1
export MALLOC_ARENA_MAX=2

# 1. Forwarder engine (auto-restarting background loop)
(
  while true; do
    echo "[start.sh] Starting forwarder.py..."
    python forwarder.py
    echo "[start.sh] forwarder.py exited. Restarting in 5s..."
    sleep 5
  done
) &

# 2. Control Bot (auto-restarting background loop)
(
  while true; do
    echo "[start.sh] Starting control_bot.py..."
    python control_bot.py
    echo "[start.sh] control_bot.py exited. Restarting in 5s..."
    sleep 5
  done
) &

# 3. Web server (foreground process replacing the subshell)
exec python web.py
