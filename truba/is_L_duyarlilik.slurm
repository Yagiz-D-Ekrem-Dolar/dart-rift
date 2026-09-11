#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J L_duyar
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=03:00:00
#SBATCH --array=0-11
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/L_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/L_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_l$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL L -- UC EKSENLI DUYARLILIK PILOTU (uzman Soru 13)
#   docs/truba/PROTOKOL-L-DUYARLILIK.md, kosudan ONCE commit'lendi
#
#  0-5 : L_ara_kirpik (ara + cekme siniri + blok v2 + geometri,
#        blok yaricapi 1,7-6,5 m)
#  6-11: L_son_uretim (G1 ile ayni uretim)
#  her kolda: gorev 0/1 = 7 noktalik turev tasarimi, tohum s0/s1;
#             gorev 2-5 = yalniz merkez, tohum s2..s5 (gurultu)
# ============================================================

TOHUMLAR=(20260906 99991111 11111111 22222222 33333333 44444444)
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 6 ]; then
  KOL=L_ara_kirpik; j=$i
  EK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5"
else
  KOL=L_son_uretim; j=$((i - 6))
  EK=""
fi
SAHNE_TOHUM=${TOHUMLAR[$j]}
TAS="$KOK/kampanya/L_tasarim_${KOL}_${j}.json"
if [ "$j" -lt 2 ]; then
  python scripts/duyarlilik_raporu.py --kok "$KOK/kampanya" --kol x --tasarim-yaz "$TAS"
else
  python scripts/duyarlilik_raporu.py --kok "$KOK/kampanya" --kol x --tasarim-yaz "$TAS" --sadece-merkez
fi

echo "=============================================================="
echo "L/$i  $KOL  sahne=$SAHNE_TOHUM  tasarim=$(basename $TAS)"
echo "  ek = '$EK'"
echo "  kod: $(git rev-parse HEAD)"
echo "=============================================================="

python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.024 --root-seed 20260906 --sahne-tohum "$SAHNE_TOHUM" \
    --tasarim-dosyasi "$TAS" --kademeler kaba $EK \
    --out "$KOK/kampanya/${KOL}_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "L/$i ($KOL) rc=$rc"
exit $rc
