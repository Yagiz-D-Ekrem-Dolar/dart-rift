#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J T_zaman
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --array=0-3
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/T_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/T_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_t$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL T -- ZAMANDA PLATO TANISI (docs/truba/PROTOKOL-T-ZAMAN.md)
#   0,1: matris sahasi (tohum 20260906, 99991111)
#   2,3: blok sahasi   (tohum 20260906, 99991111)
# ============================================================
TOHUMLAR=(20260906 99991111)
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh"
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 2 ]; then SAHA=matris; SB="--carpma-sahasi matris --saha-yaricapi 3.0"
else SAHA=blok; SB="--carpma-sahasi blok --saha-blok-yaricapi 4.0"; fi
SAHNE_TOHUM=${TOHUMLAR[$((i % 2))]}
TAS="$KOK/kampanya/T_tasarim.json"
if [ ! -f "$TAS" ]; then echo "tasarim dosyasi yok: $TAS"; exit 2; fi
echo "T/$i  saha=$SAHA  sahne=$SAHNE_TOHUM  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.2 --root-seed 20260906 --sahne-tohum "$SAHNE_TOHUM" \
    --tasarim-dosyasi "$TAS" --kademeler kaba $ORTAK $SB \
    --out "$KOK/kampanya/T_${SAHA}_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "T/$i ($SAHA) rc=$rc"
exit $rc
