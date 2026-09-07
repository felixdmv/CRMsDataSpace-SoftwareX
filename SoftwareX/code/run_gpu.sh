#!/bin/bash
# SoftwareX - Lanzador en nodo con GPU NVIDIA A100
PORT=${1:-8081}

export CPATH="/home/felix.demiguel/contenido_computo03_felix/anaconda3/include/python3.12:$HOME/.local/include/python3.12:$CPATH"
export C_INCLUDE_PATH="/home/felix.demiguel/contenido_computo03_felix/anaconda3/include/python3.12:$HOME/.local/include/python3.12:$C_INCLUDE_PATH"

echo "============================================================"
echo "  CRMs Data Space - SoftwareX en GPU NVIDIA A100"
echo "============================================================"
echo "  [INFO] Solicitando 1x GPU NVIDIA A100 a Slurm..."
echo ""
echo "  Instrucciones de monitorizacion y conexion:"
echo "  - En la interfaz web: veras el indicador 'GPU: NVIDIA A100' y barra VRAM en vivo."
echo "  - En otra terminal: srun --jobid=<JOBID> --overlap watch -n 1 nvidia-smi"
echo "============================================================"

# Silence VS Code Remote IPC socket forwarding warning across compute nodes
unset VSCODE_IPC_HOOK_CLI

exec srun --partition=computo --gres=gpu:1 python run_app.py --port "$PORT"
