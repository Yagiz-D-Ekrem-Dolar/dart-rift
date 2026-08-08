#!/bin/bash
#SBATCH -p kolyoz-cuda
#SBATCH -A egitimg16
#SBATCH -J f4z
#SBATCH -N 1
#SBATCH -n 16
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH -o f4z_%j.out
source /arf/scratch/egitimg16/driftclaude/ortam.sh 2>/dev/null || true
bash /arf/scratch/egitimg16/driftclaude/dart-rift/scripts/faz4_zincir.sh
