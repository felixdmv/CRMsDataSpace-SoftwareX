#!/bin/bash
# ==============================================================================
# Orchestrator & Job Submission Tool for evaluation_rredondo on Slurm HPC Cluster
# SoftwareX: "A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization"
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SBATCH_GPU="${SCRIPT_DIR}/run_cluster_gpu.sbatch"
SBATCH_CPU="${SCRIPT_DIR}/run_cluster_cpu.sbatch"

print_usage() {
    echo "Usage: $0 [model_name | all | cpu | status | --local [model]]"
    echo ""
    echo "Supported Model Options:"
    echo "  qwen       - Qwen 2.5 7B Instruct (Recommended Sovereign GPU Model)"
    echo "  mistral    - Mistral 7B Instruct v0.2"
    echo "  llama      - Llama 3.2 3B Instruct (Lightweight GPU Model)"
    echo "  llama8b    - Llama 3.1 8B Instruct"
    echo "  phi3       - Phi-3 Mini 4K Instruct"
    echo "  deepseek   - DeepSeek R1 Distill Qwen 7B"
    echo "  mock       - Deterministic Offline Baseline (Instantaneous CPU Heuristics)"
    echo "  cpu        - Submit CPU Baseline job via Slurm"
    echo "  all        - Submit all supported sovereign models sequentially to Slurm"
    echo "  status     - Show current status of Slurm jobs (squeue)"
    echo "  --local    - Execute benchmark directly on current node without Slurm"
    echo ""
    echo "Examples:"
    echo "  $0 qwen              # Submit Qwen 2.5 7B to Slurm GPU partition"
    echo "  $0 all               # Submit all models to Slurm"
    echo "  $0 status            # Check running jobs"
    echo "  $0 --local mock      # Run deterministic baseline immediately on login node"
}

TARGET="${1:-qwen}"

if [ "${TARGET}" == "--help" ] || [ "${TARGET}" == "-h" ]; then
    print_usage
    exit 0
fi

if [ "${TARGET}" == "status" ]; then
    echo "=== Current Slurm Jobs for ${USER} ==="
    squeue -u "${USER}"
    exit 0
fi

if [ "${TARGET}" == "--local" ]; then
    LOCAL_MODEL="${2:-mock}"
    echo "=== Running evaluation_rredondo locally with provider: ${LOCAL_MODEL} ==="
    python3 "${SCRIPT_DIR}/benchmark_rredondo.py" --provider "${LOCAL_MODEL}"
    exit $?
fi

# Check if sbatch is available
if ! command -v sbatch &> /dev/null; then
    echo "[Warning] Slurm command 'sbatch' not found in path."
    echo "Falling back to local execution with provider: ${TARGET}"
    python3 "${SCRIPT_DIR}/benchmark_rredondo.py" --provider "${TARGET}"
    exit $?
fi

if [ "${TARGET}" == "cpu" ] || [ "${TARGET}" == "mock" ]; then
    echo "Submitting CPU Baseline Job to Slurm..."
    sbatch "${SBATCH_CPU}"
    exit $?
fi

if [ "${TARGET}" == "all" ]; then
    echo "=========================================================================="
    echo " Submitting Comprehensive Model Battery to Slurm GPU Partition"
    echo " Models: qwen, mistral, llama, llama8b, phi3, deepseek"
    echo "=========================================================================="
    MODELS=("qwen" "mistral" "llama" "llama8b" "phi3" "deepseek")
    for m in "${MODELS[@]}"; do
        echo -n "Submitting ${m} -> "
        sbatch --job-name="eval_rr_${m}" "${SBATCH_GPU}" "${m}"
        sleep 1
    done
    echo ""
    echo "All jobs submitted. Monitor progress with: $0 status"
    exit 0
fi

# Submit single GPU model
echo "Submitting Slurm GPU Job for model: ${TARGET}..."
sbatch --job-name="eval_rr_${TARGET}" "${SBATCH_GPU}" "${TARGET}"
echo "Job submitted. Monitor queue with: $0 status"
