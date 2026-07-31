#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python3 webui_low_fe.py
