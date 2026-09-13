#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J dolgu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/dolgu_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/dolgu_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_dolgu$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# A83 KARARI -- PATLAYAN NOKTALARIN DOLGUSU (kesme + yogunluk tabani)
#   Liste: $LISTE (sbatch --export=LISTE=...), satir basina:
#     CIKTI_ONEKI  TASARIM_TOHUMU  LHS_INDEKSI  SAHNE_TOHUMU  MERDIVEN
#   Gorev i = listenin i. satiri (0'dan). Ciktilar havuz desenine
#   `<ONEK>_matris_<TOHUM>_<INDEKS>_sahne<S>` diye eklenir.
# ============================================================
SATIR=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$LISTE")
read -r ONEK TAS IDX S LAD <<< "$SATIR"
TASD="$KOK/kampanya/dolgu_tasarim_${TAS}_${IDX}.json"
python - "$TAS" "$IDX" "$TASD" <<'PY'
import json, sys
from dartrift.inference.design import lhs_design, DART_UZAYI_S3
t = lhs_design(DART_UZAYI_S3, 24, root_seed=int(sys.argv[1]))[int(sys.argv[2])]
json.dump({"theta": [t.tolist()]}, open(sys.argv[3], "w"))
print("theta", t.tolist())
PY
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0 --dayanim-kesme --yogunluk-tabani"
echo "dolgu/$SLURM_ARRAY_TASK_ID  $ONEK tasarim=$TAS idx=$IDX sahne=$S merdiven=$LAD  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.024 --root-seed 20260906 --sahne-tohum "$S" \
    --tasarim-dosyasi "$TASD" --kademeler "$LAD" $ORTAK \
    --out "$KOK/kampanya/${ONEK}_matris_${TAS}_${IDX}_sahne${S}.jsonl"
rc=$?
echo "dolgu/$SLURM_ARRAY_TASK_ID rc=$rc"
exit $rc
