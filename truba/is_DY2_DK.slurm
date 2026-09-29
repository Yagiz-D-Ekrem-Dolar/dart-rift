#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J DY2_DK
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-1
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/DY2DK_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/DY2DK_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# ============================================================
# PROTOKOL-DY S6 (docs/truba/PROTOKOL-DY-DART-GEC-EVRE.md)
#   gorev 0: DY2 -- elipsoit, A112 duzeltmeli kabuk, kalibre yogunluk 2306,1
#   gorev 1: DK  -- hacim-esdeger KURE (R = 76,436), kalibre yogunluk 2305,8
#   Ikisi de 4,3000e9 kg (A108 denetimi gecti: -%0,05 ve -%0,12).
#   S4'un kurali DEGISMEDI. DK ayrica sigma_sekil'i olcer.
# ZORUNLU_EXPORT: AGAC
# ============================================================
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi"; exit 2; fi
if [ ! -d "$AGAC/src/dartrift" ]; then echo "HATA: AGAC gecersiz"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC $AGAC_COMMIT, SABIT_COMMIT $(cat "$KOK/SABIT_COMMIT")"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_dy2dk$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$AGAC"

i=$SLURM_ARRAY_TASK_ID
TAS="$KOK/kampanya/DY2_tasarim_$i.json"
echo '{"theta": [[1.15, 10.0, 0.25]]}' > "$TAS.$SLURM_JOB_ID.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin --yercekimi \
--gec-evre-t 1.0 --gec-evre-A 1.0e5 --dondurma-k 3.0 --dondurma-her 200 \
--impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
--model-sinifi M1 --mermi-uc-kure --mermi-kutlesi 579.4 --mermi-hizi 6144.9 \
--mermi-yogunlugu 1000.0 --carpma-acisi 17.0 --mu-f 0.6 \
--spacing 7.0 --kademeler kaba"

if [ "$i" -eq 0 ]; then
  AD=DY2_dart_g1p0
  OZEL="--hedef-yari-eksenler 88.5 87.0 58.0 --yigin-yogunlugu 2306.1"
elif [ "$i" -eq 1 ]; then
  AD=DK_kure_g1p0
  OZEL="--hedef-yaricapi 76.436 --yigin-yogunlugu 2305.8"
else
  echo "HATA: gorev $i tanimsiz"; exit 3
fi

echo "DY2DK/$i  $AD  kod: $AGAC_COMMIT"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 600 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" $ORTAK $OZEL \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "DY2DK/$i ($AD) rc=$rc"
exit $rc
