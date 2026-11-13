#!/bin/bash
# ==============================================================================
# Slurm SBATCH Job Script for evaluation_rredondo on HPC GPU Cluster
# SoftwareX: "A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization"
# ==============================================================================
#SBATCH --job-name=eval_rredondo_gpu
#SBATCH --partition=computo
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=evaluation_rredondo/logs/slurm_gpu_%j.log
#SBATCH --error=evaluation_rredondo/logs/slurm_gpu_%j.err

# Target model provider can be passed as environment variable or 1st argument (default: qwen)
MODEL_PROVIDER="${1:-${MODEL:-qwen}}"

# Base paths
WORKSPACE_DIR="/home/raquel.redondo/contenido_computo03/SoftwareX"
CENTRAL_CACHE_USER="/home/felix.demiguel"
CONTAINER_SIF="/opt/ohpc/pub/containers/nvidia-pytorch-24.03-uv.sif"

cd "${WORKSPACE_DIR}" || exit 1
mkdir -p evaluation_rredondo/logs evaluation_rredondo/results

echo "=========================================================================="
echo "  STARTING SOFTWAREX BENCHMARK ON HPC CLUSTER: evaluation_rredondo"
echo "  Date:       $(date)"
echo "  Host:       $(hostname)"
echo "  Slurm Job:  ${SLURM_JOB_ID:-manual}"
echo "  Partition:  ${SLURM_JOB_PARTITION:-computo}"
echo "  Model:      ${MODEL_PROVIDER}"
echo "=========================================================================="

echo "[Cluster Info] Active GPU Hardware:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi -L
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
else
    echo "nvidia-smi not available in host shell"
fi
echo "=========================================================================="

# Export Hugging Face cache location to utilize pre-cached local weights
export HF_HOME="${CENTRAL_CACHE_USER}/.cache/huggingface"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export PYTHONUNBUFFERED=1
export PYTHONPATH="${WORKSPACE_DIR}/code:${WORKSPACE_DIR}:${PYTHONPATH}"

# Execute benchmark inside Apptainer / Singularity container with CUDA GPU passthrough
if [ -f "${CONTAINER_SIF}" ]; then
    echo "[Container] Launching Apptainer with NVIDIA CUDA acceleration..."
    apptainer exec --nv \
      --bind "${CENTRAL_CACHE_USER}:${CENTRAL_CACHE_USER}" \
      --bind "${WORKSPACE_DIR}:${WORKSPACE_DIR}" \
      --bind /home/raquel.redondo:/home/raquel.redondo \
      "${CONTAINER_SIF}" \
      python3 -u evaluation_rredondo/benchmark_rredondo.py --provider "${MODEL_PROVIDER}"
else
    echo "[Warning] Apptainer image ${CONTAINER_SIF} not found. Running directly with host python3..."
    python3 -u evaluation_rredondo/benchmark_rredondo.py --provider "${MODEL_PROVIDER}"
fi

EXIT_CODE=$?
echo "=========================================================================="
echo "  FINISHED EVALUATION BENCHMARK: $(date)"
echo "  Exit Code: ${EXIT_CODE}"
echo "=========================================================================="
exit ${EXIT_CODE}
