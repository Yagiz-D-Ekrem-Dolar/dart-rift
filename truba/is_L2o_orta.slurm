#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J L2o_orta
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --array=0-5
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/L2o_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/L2o_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_l2o$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL L2 §8 -- MATRIS KOLU ORTA MERDIVENDE TEKRAR (yorum tablosu §5)
#   docs/truba/PROTOKOL-L2-SAHA.md, kosudan ONCE commit'lendi
#  0-5 : L2o_matris (orta merdiven, carpma noktasinin 3 m kuresinde blok yok)
#  her kolda: gorev 0/1 = 7 noktalik turev tasarimi; 2-5 = yalniz merkez
# ============================================================
TOHUMLAR=(20260906 99991111 11111111 22222222 33333333 44444444)
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh"
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 6 ]; then
  KOL=L2o_matris; j=$i; SAHA="--carpma-sahasi matris --saha-yaricapi 3.0"
else
  KOL=L2_blok; j=$((i - 6)); SAHA="--carpma-sahasi blok --saha-blok-yaricapi 4.0"
fi
SAHNE_TOHUM=${TOHUMLAR[$j]}
TAS="$KOK/kampanya/L2_tasarim_${KOL}_${j}.json"
if [ "$j" -lt 2 ]; then
  python scripts/duyarlilik_raporu.py --kok "$KOK/kampanya" --kol x --tasarim-yaz "$TAS"
else
  python scripts/duyarlilik_raporu.py --kok "$KOK/kampanya" --kol x --tasarim-yaz "$TAS" --sadece-merkez
fi
echo "L2o/$i  $KOL  sahne=$SAHNE_TOHUM  saha='$SAHA'  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.024 --root-seed 20260906 --sahne-tohum "$SAHNE_TOHUM" \
    --tasarim-dosyasi "$TAS" --kademeler orta $ORTAK $SAHA \
    --out "$KOK/kampanya/${KOL}_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "L2o/$i ($KOL) rc=$rc"
exit $rc
