#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J GEC_DOKUM
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=3-00:00:00
#SBATCH --array=0-3%4
#   kolyoz11/13 (KAYIT-085): "nvidia-smi GPU gormuyor" ile dustu.
#SBATCH --exclude=kolyoz19,kolyoz9,kolyoz11,kolyoz13
#SBATCH -o /arf/scratch/egitimg16u3/driftclaude/ciktilar/GEC_DOKUM_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u3/driftclaude/ciktilar/GEC_DOKUM_%A_%a.err

set -uo pipefail
KOK=${KOK:-/arf/scratch/egitimg16u3/driftclaude}
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# ======================================================================
# PROTOKOL-HT EK-2 (kilitli, bu kosu gonderilmeden ONCE yazildi)
#   docs/truba/PROTOKOL-HT-EK2-2026-11-01.md
# ======================================================================
# TEK SORU: t = 600 s'te krater kacmamis ejekta tarafindan ORTULU
# (KAYIT-090: eksende 6,50-47,99 m, ortanca 30,89 m). Ejekta dustukten
# sonra okunabilir hale geliyor mu?
#
# Dort nokta EK-2 §3'te, KOSUDAN ONCE secildi -- ortu yuksekligi
# araligini kapsiyor ve posteriorun kipini (Y0 ~ 18,7 Pa) iceriyor:
#   dilim 16/96  Y0=1,15 Pa   ortu 10,27 m  (en ince)
#   dilim 20/96  Y0=6,46 Pa   ortu 30,89 m  (ortanca)
#   dilim 84/96  Y0=18,57 Pa  ortu 44,95 m  (POSTERIORUN KIPI)
#   dilim 87/96  Y0=1,35 Pa   ortu 47,99 m  (en kalin)
#
# DEGISEN TEK SEY --t-end: asagidaki ORTAK satiri is_HAVUZ.slurm ile
# BIREBIR AYNIDIR, yalniz --dilim k/96 ve --azami-adim tavani farkli.
# Tavan bir fizik ayari DEGIL: 5 000 s adim butcesini asmasin diye
# 4e7 -> 8e7. Baska bir sey degisirse olculen sey "gec dokum" olmaz.
#
# MALIYET KUTUKTEN OLCULDU (is 1592569, nokta 0): erken evre
# dt = 4,4e-6 s, gec evre dt = 3,8e-3 s; 600 s ~ 390 000 adim,
# 5 000 s ~ 1 550 000 adim, yani ~4 kat -> nokta basina ~20 GPU-saat.
#
# BILINEN SINIR (EK-2 §6): gec evre DUSUK SES HIZLI BIR VEKIL
# malzemedir (ADR-0050/L1). Bu kosu bir OLCUM ARACI SINAVIDIR (ortu
# aciliyor mu), son kraterin niceliksel ongorusu DEGIL.
# ZORUNLU_EXPORT: AGAC
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_gecdokum$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$AGAC"

# EK-2 §3'un dort noktasi; sira array gorev numarasiyla eslenir.
NOKTALAR=(16 20 84 87)
i=${NOKTALAR[$SLURM_ARRAY_TASK_ID]}
N_DILIM=96
AD=GEC_DOKUM_g1p0

# is_HAVUZ.slurm ile BIREBIR AYNI (yalniz dilim ve azami-adim).
ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin --yercekimi \
--gec-evre-t 1.0 --gec-evre-A 1.0e5 --dondurma-k 3.0 --dondurma-her 200 \
--impuls-log --beta-km --azami-adim 80000000 --adim-bildir 50000 \
--model-sinifi M1 --mermi-kutlesi 579.4 --mermi-hizi 6144.9 \
--mermi-yogunlugu 1000.0 --carpma-acisi 17.0 --mu-f 0.6 --mermi-uc-kure \
--hedef-yari-eksenler 88.5 87.0 58.0 --yigin-yogunlugu 2306.1 \
--spacing 7.0 --kademeler kaba \
--uzay-s4 --n-lhs 96 --dilim $i/$N_DILIM \
--blok-rmin 14.0 --blok-rmax 56.0 \
--istege-bagli-gozlemli krater_derinlik"

echo "GEC_DOKUM dilim $i/$N_DILIM  t_end=5000  kod: $AGAC_COMMIT"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 5000 --root-seed 20260906 --sahne-tohum 20260906 \
    $ORTAK \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "GEC_DOKUM dilim $i rc=$rc"
exit $rc
