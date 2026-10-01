#!/bin/bash
#SBATCH --job-name=crm_dst_bench
#SBATCH --partition=computo
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=code/evaluation/dst_benchmark_slurm_%j.log

cd /home/felix.demiguel/contenido_computo03_felix/CRMsDataSpace

echo "=========================================================="
echo " Starting SoftwareX Conversational DST Benchmark on GPU"
echo " Date: $(date)"
echo " Host: $(hostname)"
echo " CUDA Device:"
nvidia-smi -L
echo "=========================================================="

apptainer exec --nv \
  --bind /home/felix.demiguel:/home/felix.demiguel \
  /opt/ohpc/pub/containers/nvidia-pytorch-24.03-uv.sif \
  python3 -u code/evaluation/benchmark_conversational_dst.py --models llama8b

echo "=========================================================="
echo " Finished Conversational DST Benchmark: $(date)"
echo "=========================================================="
