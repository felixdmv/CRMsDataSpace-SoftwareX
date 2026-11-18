#!/bin/bash
# ==============================================================================
# Slurm SBATCH Job Script for evaluation_rredondo on CPU Compute Node
# SoftwareX: "A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization"
# ==============================================================================
#SBATCH --job-name=eval_rredondo_cpu
#SBATCH --partition=computo
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=evaluation_rredondo/logs/slurm_cpu_%j.log
#SBATCH --error=evaluation_rredondo/logs/slurm_cpu_%j.err

WORKSPACE_DIR="/home/raquel.redondo/contenido_computo03/SoftwareX"
cd "${WORKSPACE_DIR}" || exit 1
mkdir -p evaluation_rredondo/logs evaluation_rredondo/results

echo "=========================================================================="
echo "  STARTING DETERMINISTIC BASELINE BENCHMARK ON CPU COMPUTE NODE"
echo "  Date:       $(date)"
echo "  Host:       $(hostname)"
echo "  Slurm Job:  ${SLURM_JOB_ID:-manual}"
echo "=========================================================================="

export PYTHONUNBUFFERED=1
export PYTHONPATH="${WORKSPACE_DIR}/code:${WORKSPACE_DIR}:${PYTHONPATH}"

python3 -u evaluation_rredondo/benchmark_rredondo.py --provider mock

EXIT_CODE=$?
echo "=========================================================================="
echo "  FINISHED CPU BENCHMARK: $(date)"
echo "  Exit Code: ${EXIT_CODE}"
echo "=========================================================================="
exit ${EXIT_CODE}
