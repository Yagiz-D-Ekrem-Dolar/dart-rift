#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J HAVUZ
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-23%2
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/HAVUZ_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/HAVUZ_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# PROTOKOL-HAVUZ (kilitli, havuz gonderilmeden ONCE yazildi):
#   - sahne DY2 ile BIREBIR AYNI (S2), degisen tek sey theta
#   - uzay DART_UZAYI_S4 (ADR-0053 KABUL + PROTOKOL-DO olcumu, S3.1 kapisi)
#   - 96 nokta LHS, 24 dilim x 4 nokta. `%2` ile en fazla 2 gorev birden
#     kosar (2 GPU siniri); Slurm biri bitince digerini baslatir.
#     Dilim basina ~4 x 5 = 20 saat, is siniri 24 saat -> pay var.
#     Toplam ~480 GPU-saat; 2 GPU ile duvar suresi ~10 gun.
#   - krater_derinlik ISTEGE BAGLI (ADR-0055/A114): olculemezse `nan`,
#     kayit DUSMEZ; beta ve ejekta kesri yasar
#   - bloklar r in [14, 56] m, q = 3 SAYI olarak (ADR-0057 KABUL)
#   - matris cekmesi KAPALI (ADR-0056 KABUL)
# `ensemble_kos` tamamlanan noktalari ATLAR: is yeniden gonderilebilir.
# ZORUNLU_EXPORT: AGAC
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC/SABIT_COMMIT uyusmuyor"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_havuz$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$AGAC"

i=$SLURM_ARRAY_TASK_ID
N_DILIM=24
AD=HAVUZ_g1p0

# DY2 ile ayni sahne; theta LHS'den gelir (--tasarim-dosyasi YOK)
ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin --yercekimi \
--gec-evre-t 1.0 --gec-evre-A 1.0e5 --dondurma-k 3.0 --dondurma-her 200 \
--impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
--model-sinifi M1 --mermi-kutlesi 579.4 --mermi-hizi 6144.9 \
--mermi-yogunlugu 1000.0 --carpma-acisi 17.0 --mu-f 0.6 --mermi-uc-kure \
--hedef-yari-eksenler 88.5 87.0 58.0 --yigin-yogunlugu 2306.1 \
--spacing 7.0 --kademeler kaba \
--uzay-s4 --n-lhs 96 --dilim $i/$N_DILIM \
--blok-rmin 14.0 --blok-rmax 56.0 \
--istege-bagli-gozlemli krater_derinlik"

echo "HAVUZ dilim $i/$N_DILIM  kod: $AGAC_COMMIT"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 600 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" $ORTAK \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "HAVUZ dilim $i rc=$rc"
exit $rc
