#!/usr/bin/env bash
# CRMsDataSpace - Lanzador GPU general desde la raíz (Slurm + NVIDIA A100)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/code/run_gpu.sh" 2>/dev/null
exec "$SCRIPT_DIR/code/run_gpu.sh" "$@"
