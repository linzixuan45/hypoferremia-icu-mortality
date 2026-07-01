#!/bin/bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

SERVER_PORT="${SERVER_PORT:-7788}"
PYTHON="${HYPOFERRREMIA_PYTHON:-/root/miniconda3/bin/python}"
PID_FILE="$DIR/.webui.pid"
LOG_FILE="$DIR/webui.log"

stop_service() {
  if [[ -f "$PID_FILE" ]]; then
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping webui (pid $pid)..."
      kill "$pid" 2>/dev/null || true
      for _ in $(seq 1 10); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.5
      done
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
  fi

  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${SERVER_PORT}/tcp" 2>/dev/null || true
  elif command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti ":${SERVER_PORT}" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
      echo "Stopping process on port ${SERVER_PORT}..."
      kill $pids 2>/dev/null || true
    fi
  fi
}

start_service() {
  if ! "$PYTHON" -c "import gradio" 2>/dev/null; then
    echo "Installing web dependencies..."
    "$PYTHON" -m pip install -r requirements-web.txt -q
  fi

  echo "Starting webui on ${SERVER_NAME:-0.0.0.0}:${SERVER_PORT}..."
  nohup "$PYTHON" webui.py >>"$LOG_FILE" 2>&1 &
  echo $! >"$PID_FILE"
  echo "Started (pid $(cat "$PID_FILE")). Log: $LOG_FILE"
}

stop_service
start_service
