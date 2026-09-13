#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J M_yakin
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --array=0-35
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/M_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/M_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_m$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL M -- UC COZUNURLUKTE YAKINSAMA PILOTU
#   docs/truba/PROTOKOL-M-YAKINSAMA.md, kosudan ONCE commit'lendi
#   gorev i: merdiven = i/12 (kaba/orta/ince), theta = (i%12)/2, tohum = (i%12)%2
#   tasarim dosyalari gonderimde uretilir (m_yakinsama_raporu.py --tasarim-yaz)
# ============================================================
TOHUMLAR=(20260906 99991111)
MERD=(kaba orta ince)
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0"
i=$SLURM_ARRAY_TASK_ID
LAD=${MERD[$((i / 12))]}
r=$((i % 12)); K=$((r / 2)); SAHNE_TOHUM=${TOHUMLAR[$((r % 2))]}
TAS="$KOK/kampanya/M_tasarim_t${K}.json"
if [ ! -f "$TAS" ]; then echo "tasarim dosyasi yok: $TAS"; exit 2; fi
echo "M/$i  merdiven=$LAD  theta=t$K  sahne=$SAHNE_TOHUM  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.024 --root-seed 20260906 --sahne-tohum "$SAHNE_TOHUM" \
    --tasarim-dosyasi "$TAS" --kademeler "$LAD" $ORTAK \
    --out "$KOK/kampanya/M_${LAD}_t${K}_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "M/$i ($LAD t$K) rc=$rc"
exit $rc
