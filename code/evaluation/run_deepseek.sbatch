#!/bin/bash
# ==============================================================================
# Slurm SBATCH Job Script specifically for DeepSeek-R1 Distill Qwen 7B
# SoftwareX: "A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization"
# ==============================================================================
#SBATCH --job-name=eval_deepseek_gpu
#SBATCH --partition=computo
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=02:30:00
#SBATCH --output=code/evaluation/logs/slurm_deepseek_%j.log
#SBATCH --error=code/evaluation/logs/slurm_deepseek_%j.err

MODEL_PROVIDER="deepseek"

WORKSPACE_DIR="${SLURM_SUBMIT_DIR:-$PWD}"
if [ -d "${WORKSPACE_DIR}/code/evaluation" ]; then
    EVAL_DIR="${WORKSPACE_DIR}/code/evaluation"
elif [ -f "${WORKSPACE_DIR}/benchmark_unified.py" ]; then
    EVAL_DIR="${WORKSPACE_DIR}"
    WORKSPACE_DIR="$(cd "${WORKSPACE_DIR}/../.." && pwd)"
else
    EVAL_DIR="${WORKSPACE_DIR}"
fi

CENTRAL_CACHE_USER="/home/felix.demiguel"
CONTAINER_SIF="/opt/ohpc/pub/containers/nvidia-pytorch-24.03-uv.sif"

cd "${WORKSPACE_DIR}" || exit 1
mkdir -p "${EVAL_DIR}/logs" "${EVAL_DIR}/results"

echo "=========================================================================="
echo "  STARTING DEEPSEEK BENCHMARK ON HPC CLUSTER"
echo "  Date:       $(date)"
echo "  Host:       $(hostname)"
echo "  Slurm Job:  ${SLURM_JOB_ID:-manual}"
echo "  Model:      ${MODEL_PROVIDER}"
echo "=========================================================================="

export HF_HOME="${CENTRAL_CACHE_USER}/.cache/huggingface"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export PYTHONUNBUFFERED=1
export PYTHONPATH="${WORKSPACE_DIR}/code:${WORKSPACE_DIR}:${PYTHONPATH}"

BENCHMARK_SCRIPT="${EVAL_DIR}/benchmark_unified.py"
if [ ! -f "${BENCHMARK_SCRIPT}" ]; then
    BENCHMARK_SCRIPT="${EVAL_DIR}/benchmark_rredondo.py"
fi

if [ -f "${CONTAINER_SIF}" ]; then
    echo "[Container] Launching Apptainer with NVIDIA CUDA acceleration..."
    apptainer exec --nv \
      --bind "${CENTRAL_CACHE_USER}:${CENTRAL_CACHE_USER}" \
      --bind "${WORKSPACE_DIR}:${WORKSPACE_DIR}" \
      "${CONTAINER_SIF}" \
      python3 -u "${BENCHMARK_SCRIPT}" --provider "${MODEL_PROVIDER}"
else
    echo "[Warning] Apptainer image ${CONTAINER_SIF} not found. Running directly with host python3..."
    python3 -u "${BENCHMARK_SCRIPT}" --provider "${MODEL_PROVIDER}"
fi

EXIT_CODE=$?
echo "=========================================================================="
echo "  FINISHED DEEPSEEK BENCHMARK: $(date) (Exit Code: ${EXIT_CODE})"
echo "=========================================================================="
exit ${EXIT_CODE}
