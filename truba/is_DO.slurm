#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J DO_onsel
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-1
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/DO_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/DO_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# PROTOKOL-DO S2 (kilitli): DY2 ile BIREBIR AYNI sahne; degisen TEK sey Y0.
#   DO1 = 500 Pa (literaturun ust ucu, onsel alt kenarinin ALTINDA)
#   DO2 = 5000 Pa (onselin ICINDE)
# ZORUNLU_EXPORT: AGAC
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC/SABIT_COMMIT uyusmuyor"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_do$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$AGAC"

i=$SLURM_ARRAY_TASK_ID
if [ "$i" -eq 0 ]; then
  AD=DO1_Y500_g1p0;  Y0=500.0
elif [ "$i" -eq 1 ]; then
  AD=DO2_Y5000_g1p0; Y0=5000.0
else
  echo "HATA: gorev $i tanimsiz"; exit 3
fi

TAS="$KOK/kampanya/DO_tasarim_$i.json"
printf '{"theta": [[1.15, %s, 0.25]]}\n' "$Y0" > "$TAS.$SLURM_JOB_ID.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

# DY2 ile ayni: uc kure mermi, kalibre yogunluk, elipsoit, 17 derece, t_g = 1,0 s
ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin --yercekimi \
--gec-evre-t 1.0 --gec-evre-A 1.0e5 --dondurma-k 3.0 --dondurma-her 200 \
--impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
--model-sinifi M1 --mermi-kutlesi 579.4 --mermi-hizi 6144.9 \
--mermi-yogunlugu 1000.0 --carpma-acisi 17.0 --mu-f 0.6 --mermi-uc-kure \
--hedef-yari-eksenler 88.5 87.0 58.0 --yigin-yogunlugu 2306.1 \
--spacing 7.0 --kademeler kaba"

echo "DO/$i  $AD  Y0=$Y0 Pa  kod: $AGAC_COMMIT"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 600 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" $ORTAK \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "DO/$i ($AD) rc=$rc"
exit $rc
