#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J UA_uzak
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-1
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/UA_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/UA_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_ua$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL UA -- UZAK ALAN COZUNURLUGU (docs/truba/PROTOKOL-UA-UZAK-ALAN.md)
#   W2_Y10_g0p2 ile AYNI her sey; yalniz taban aralik: 5,0 m ve 3,5 m.
#   7 m kolu W2_Y10_g0p2'dir (yeniden kosulmaz).
# ============================================================
TABAN=(5.0 3.5)
TAD=(5p0 3p5)
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -ge 2 ]; then echo "HATA: gorev $i tanimsiz"; exit 3; fi

TAS="$KOK/kampanya/UA_tasarim.json"
echo '{"theta": [[1.15, 10.0, 0.0]]}' > "$TAS.$SLURM_JOB_ID.$i.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.$i.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin"
KIYAS="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 \
--mu-f 0.6 --yercekimi"

AD="UA_s${TAD[$i]}"
echo "UA/$i  $AD  taban=${TABAN[$i]} m  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 600 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --spacing "${TABAN[$i]}" \
    --kademeler 24:2.8 12:1.4 6:0.7 3:0.35 $ORTAK $KIYAS \
    --gec-evre-t 0.2 --gec-evre-A 1.0e5 \
    --dondurma-k 3.0 --dondurma-her 200 \
    --impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "UA/$i ($AD) rc=$rc"
exit $rc
