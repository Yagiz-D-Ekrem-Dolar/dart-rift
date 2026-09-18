#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J W2_duman
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/W2D_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/W2D_%j.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_w2d"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL W2 S3 -- DUMAN KOSUSU (BILIMSEL SONUC DEGIL)
#   A92 duzeltmesi GPU'da momentum defterini kapatiyor mu?
#   Kabul: donmus >= 1 VE momentum_artik_bagil <= 1e-4.
#   beta YARGIYA GIRMEZ ve raporlanmaz.
# ============================================================
TAS="$KOK/kampanya/W2D_tasarim.json"
echo '{"theta": [[1.15, 1.0e1, 0.0]]}' > "$TAS.$SLURM_JOB_ID.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin"
KIYAS="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 \
--mu-f 0.6 --yercekimi"

echo "W2 duman: kod $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 5.0 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --kademeler kaba $ORTAK $KIYAS \
    --gec-evre-t 0.2 --gec-evre-A 1.0e5 \
    --dondurma-k 3.0 --dondurma-her 200 \
    --impuls-log --beta-km --azami-adim 4000000 --adim-bildir 20000 \
    --out "$KOK/kampanya/W2D_duman.jsonl"
rc=$?
echo "W2 duman rc=$rc"
exit $rc
