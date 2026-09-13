#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J N2_ayirt
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --array=0-5
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/N2_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/N2_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_n2$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL P DIS ORNEKLEM (N2) -- docs/truba/PROTOKOL-P-KALIBRASYON.md §4b
#   0-2: sahne 20260906, dilim 0/3..2/3
#   3-5: sahne 99991111, dilim 0/3..2/3
#   TASARIM tohumu 20260914: N ile AYNI fizik ve sahne tohumlari, BASKA theta
# ============================================================
TOHUMLAR=(20260906 99991111)
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0"
i=$SLURM_ARRAY_TASK_ID
SAHNE_TOHUM=${TOHUMLAR[$((i / 3))]}
DILIM="$((i % 3))/3"
echo "N2/$i  sahne=$SAHNE_TOHUM  dilim=$DILIM  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --n-lhs 24 --t-end 0.024 --dilim "$DILIM" \
    --root-seed 20260914 --sahne-tohum "$SAHNE_TOHUM" \
    --kademeler kaba $ORTAK \
    --out "$KOK/kampanya/N2_matris_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "N2/$i rc=$rc"
exit $rc
