#!/bin/bash
# SoftwareX - Lanzador en nodo con GPU NVIDIA A100
# Replicable para cualquier usuario del cluster (ej. compañera o revisores en HPC)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    python3 "$SCRIPT_DIR/run_gpu_app.py" --help
    exit 0
fi

PORT=${1:-8081}

# Dynamic include paths for Triton JIT compilation
for INC in "$CONDA_PREFIX/include/python3.12" "$HOME/.local/include/python3.12" "$HOME/anaconda3/include/python3.12" "$HOME/miniconda3/include/python3.12"; do
    if [ -d "$INC" ]; then
        export CPATH="$INC:$CPATH"
        export C_INCLUDE_PATH="$INC:$C_INCLUDE_PATH"
        break
    fi
done

echo "============================================================"
echo "  CRMs Data Space - SoftwareX en GPU NVIDIA A100"
echo "============================================================"
echo "  [INFO] Solicitando 1x GPU NVIDIA A100 a Slurm y preparando proxy..."
echo ""
echo "  Instrucciones de monitorización y conexión:"
echo "  - En la interfaz web: verás el indicador 'GPU: NVIDIA A100' y barra VRAM en vivo."
echo "  - En otra terminal: srun --overlap watch -n 1 nvidia-smi"
echo "============================================================"

# Silence VS Code Remote IPC socket forwarding warning across compute nodes
unset VSCODE_IPC_HOOK_CLI

exec python3 "$SCRIPT_DIR/run_gpu_app.py" --port "$PORT"
