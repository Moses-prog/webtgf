#!/bin/bash
export PYTHONUNBUFFERED=1
export PYTHONOPTIMIZE=1
export MALLOC_ARENA_MAX=2
export MALLOC_TRIM_THRESHOLD_=65536

echo "[start.sh] Launching unified WP Relay service..."
exec python web.py
