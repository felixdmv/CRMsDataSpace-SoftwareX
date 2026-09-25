#!/usr/bin/env bash
# Elsevier SoftwareX — General-Purpose GIS Architecture Template Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8085}"

echo "=========================================================================="
echo " 🌍 Elsevier SoftwareX: General-Purpose GIS Architecture Template Launcher"
echo " 🚀 Launching Standalone Web Server on Port $PORT"
echo "=========================================================================="

python3 "$SCRIPT_DIR/template/run_template.py" --port "$PORT"
