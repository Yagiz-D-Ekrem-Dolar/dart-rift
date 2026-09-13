#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J Nk_ayirt
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --array=0-23
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/Nk_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/Nk_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_nk$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# N ve N2 TASARIMLARI, URETIM FIZIGIYLE (A80 karari: --dayanim-kesme)
#   docs/truba/PROTOKOL-A80-KESME.md §3: V1 KARARLI, V2 FIZIGI DEGISTIRIYOR
#   -> uretim kampanyalari kesmeyle YENIDEN; kesmesizler betimleyici.
#   gorev i: merdiven = i/12 (kaba, orta)
#            r = i%12: tasarim = r/6 (N 20260906, N2 20260914)
#            sahne = (r%6)/3, dilim = (r%6)%3
#   cikti: Nk_ / N2k_ (kaba), Nok_ / N2ok_ (orta)
# ============================================================
TOHUMLAR=(20260906 99991111)
TASARIM=(20260906 20260914)
MERD=(kaba orta)
ONEK_kaba=(Nk N2k)
ONEK_orta=(Nok N2ok)
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0 --dayanim-kesme"
i=$SLURM_ARRAY_TASK_ID
LAD=${MERD[$((i / 12))]}
r=$((i % 12))
d=$((r / 6))
TAS=${TASARIM[$d]}
OV="ONEK_${LAD}[$d]"; AD=${!OV}
j=$((r % 6))
SAHNE_TOHUM=${TOHUMLAR[$((j / 3))]}
DILIM="$((j % 3))/3"
echo "Nk/$i  merdiven=$LAD  tasarim=$TAS  ad=$AD  sahne=$SAHNE_TOHUM  dilim=$DILIM  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --n-lhs 24 --t-end 0.024 --dilim "$DILIM" \
    --root-seed "$TAS" --sahne-tohum "$SAHNE_TOHUM" \
    --kademeler "$LAD" $ORTAK \
    --out "$KOK/kampanya/${AD}_matris_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "Nk/$i ($AD) rc=$rc"
exit $rc
