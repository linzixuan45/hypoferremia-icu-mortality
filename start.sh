#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${HYPOFERRREMIA_PYTHON:-/root/miniconda3/bin/python}"

if ! "$PYTHON" -c "import gradio" 2>/dev/null; then
  echo "Installing web dependencies..."
  "$PYTHON" -m pip install -r requirements-web.txt -q
fi

exec "$PYTHON" webui.py
