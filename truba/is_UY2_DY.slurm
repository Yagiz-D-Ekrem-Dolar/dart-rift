#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J UY2_DY
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-1
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/UY2DY_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/UY2DY_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# ============================================================
# gorev 0: PROTOKOL-UY2 (docs/truba/PROTOKOL-UY2-KESISIM.md)
#          cozunurluk x gecis ani KESISIMI -- orta merdiven, t_gecis = 1,0 s
# gorev 1: PROTOKOL-DY  (docs/truba/PROTOKOL-DY-DART-GEC-EVRE.md)
#          DART sahnesinin gec evre modeliyle ILK kosusu
# Sabit agac (A96): AGAC zorunlu, temiz ve SABIT_COMMIT ile ayni olmali.
# ZORUNLU_EXPORT: AGAC
# ============================================================
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi (sabit worktree)"; exit 2; fi
if [ ! -d "$AGAC/src/dartrift" ]; then echo "HATA: AGAC '$AGAC' dart-rift agaci degil"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC $AGAC_COMMIT, SABIT_COMMIT $(cat "$KOK/SABIT_COMMIT")"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_uy2dy$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$AGAC"

i=$SLURM_ARRAY_TASK_ID
ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin --yercekimi \
--gec-evre-t 1.0 --gec-evre-A 1.0e5 --dondurma-k 3.0 --dondurma-her 200 \
--impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000"

if [ "$i" -eq 0 ]; then
  AD=UY2_orta_g1p0; TEND=300
  TAS="$KOK/kampanya/UY2_tasarim.json"
  echo '{"theta": [[1.15, 10.0, 0.0]]}' > "$TAS.$SLURM_JOB_ID.tmp" && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"
  OZEL="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 --mu-f 0.6 \
--spacing 7.0 --kademeler 48:2.8 24:1.4 12:0.7 6:0.35 3:0.175"
elif [ "$i" -eq 1 ]; then
  AD=DY_dart_g1p0; TEND=600
  TAS="$KOK/kampanya/DY_tasarim.json"
  echo '{"theta": [[1.15, 10.0, 0.25]]}' > "$TAS.$SLURM_JOB_ID.tmp" && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"
  OZEL="--model-sinifi M1 --hedef-yari-eksenler 88.5 87.0 58.0 \
--yigin-yogunlugu 2376.0 --mermi-uc-kure --mermi-kutlesi 579.4 \
--mermi-hizi 6144.9 --mermi-yogunlugu 1000.0 --carpma-acisi 17.0 --mu-f 0.6 \
--spacing 7.0 --kademeler kaba"
else
  echo "HATA: gorev $i tanimsiz"; exit 3
fi

echo "UY2DY/$i  $AD  t_end=$TEND  kod: $AGAC_COMMIT"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end "$TEND" --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" $ORTAK $OZEL \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "UY2DY/$i ($AD) rc=$rc"
exit $rc
