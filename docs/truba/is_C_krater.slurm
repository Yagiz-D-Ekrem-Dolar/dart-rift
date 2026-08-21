#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J a17_krater
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/c_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/c_%j.err

set -u
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache"
cd "$KOK/dart-rift"

echo "=============================================================="
echo "C -- KRATER COZUNURLUGU: lam2 = 4 (aralik 3,5 -> 1,75 m)"
echo "     Y0 = 1 Pa (matris VE blok), yercekimi ACIK, t_end = 5 s"
echo "     olcut: OLCUT-krater-cozunurlugu.md (kosudan ONCE yazildi)"
echo "     taban (kol B, is 1515196): bekleyen = 0, beta_bal = 1,411231"
echo "=============================================================="
python scripts/faz48_iki_asama.py --device cuda:0 \
    --lam2 4 --Y0 1.0 --boulder-Y0 1.0 --yercekimli \
    --t-end 5.0 --iz-every 2000 \
    --out "$KOK/ciktilar/C_krater_lam2_4.json"
echo "C rc=$?"
echo "BITTI: $(date)"
