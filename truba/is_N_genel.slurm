#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J N_genel
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/Ngen_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/Ngen_%A_%a.err
set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_ng${SLURM_JOB_ID}_$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"
# Genel N kampanyasi (P §4f), uretim fizigi kesme + taban.
# --export: LAD, TASARIMLAR="t1 t2", ONEKLER="o1 o2", NDILIM, [T_END=0.024]
# UYARI (A84): --export degerlerinde VIRGUL KULLANMA; SLURM ayirici sayar.
T_END=${T_END:-0.024}
# SAHA (Q5): matris (varsayilan) ya da blok
SAHA=${SAHA:-matris}
if [ "$SAHA" = blok ]; then SB="--carpma-sahasi blok --saha-blok-yaricapi 4.0"
elif [ "$SAHA" = matris ]; then SB="--carpma-sahasi matris --saha-yaricapi 3.0"
else echo "HATA: bilinmeyen SAHA=$SAHA"; exit 2; fi
# gorev i = d*2*NDILIM + s*NDILIM + k
read -r -a TASA <<< "$TASARIMLAR"; read -r -a ONA <<< "$ONEKLER"
TOHUMLAR=(20260906 99991111)
i=$SLURM_ARRAY_TASK_ID
d=$((i / (2 * NDILIM))); r=$((i % (2 * NDILIM))); s=$((r / NDILIM)); k=$((r % NDILIM))
TAS=${TASA[$d]}; AD=${ONA[$d]}; S=${TOHUMLAR[$s]}
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --dayanim-kesme --yogunluk-tabani"
echo "Ngen/$i $LAD saha=$SAHA t_end=$T_END tasarim=$TAS ad=$AD sahne=$S dilim=$k/$NDILIM kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 --n-lhs 24 --t-end "$T_END" \
  --dilim "$k/$NDILIM" --root-seed "$TAS" --sahne-tohum "$S" --kademeler "$LAD" $ORTAK $SB \
  --out "$KOK/kampanya/${AD}_matris_sahne${S}.jsonl"
rc=$?; echo "Ngen/$i rc=$rc"; exit $rc
