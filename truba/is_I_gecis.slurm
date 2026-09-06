#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J I_gecis
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=10:00:00
#SBATCH --array=0-11
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/I_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/I_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_i$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# I -- GECIS NOKTASI x0 COZUNURLUGE DAYANIKLI MI
#      (docs/truba/PROTOKOL-I-GECIS.md, kosudan ONCE commit'lendi)
#
# H olctu (A69): krater derinligi MUTLAK olarak yakinsamiyor
# (0,36 -> 0,61 m, %72) ama Y0 ile iliskisi iki olcekte de ayni
# (r = -0,943 vs -0,925).
#
# Fiziksel olarak anlamli parametre derinligin DEGERI degil,
# GECIS NOKTASI x0: kohezyon hangi degerin ustunde krateri
# sinirlamaya basliyor. Bizim krater 0,5 m, DART'inki ~10 m --
# MUTLAK OLCEK ZATEN AKTARILAMAZ. Aktarilabilecek olan x0.
#
# Bu kampanya G1 ile AYNI 24 theta'yi ORTA merdivende kosuyor ki
# iki olcekte de sigmoid uydurulup x0 kiyaslanabilsin.
#
# YARGI: |x0_orta - x0_kaba| < 2 sqrt(s2_kaba + s2_orta) -> DAYANIKLI
#        2-4 sigma -> ZAYIF ;  > 4 sigma -> DAYANIKSIZ
# ============================================================

TASARIM_TOHUMU=20260906
ORTA="48:2.8 24:1.4 12:0.7 6:0.35 3:0.175"

# 24 nokta / 6 dilim = 4 nokta/gorev; iki tohum = 12 gorev
D=$(( SLURM_ARRAY_TASK_ID % 6 ))
if [ "$SLURM_ARRAY_TASK_ID" -lt 6 ]; then
  SAHNE_TOHUM=20260906
else
  SAHNE_TOHUM=99991111
fi
DILIM="${D}/6"

echo "=============================================================="
echo "I/$SLURM_ARRAY_TASK_ID  dilim=$DILIM  sahne=$SAHNE_TOHUM"
echo "  merdiven = $ORTA   (N = 69 886)"
echo "  tasarim tohumu = $TASARIM_TOHUMU  (G1 ile AYNI)"
echo ""
echo "YARGI (PROTOKOL-I-GECIS.md, KOSUDAN ONCE):"
echo "  Her olcekte sigmoid uydurulur (d_alt >= 0, A67)."
echo "  Kiyaslanan: x0 (gecis) ve w (keskinlik)."
echo "  |x0_orta - x0_kaba| < 2 sigma -> DAYANIKLI"
echo "                        2-4 sigma -> ZAYIF"
echo "                        > 4 sigma -> DAYANIKSIZ"
echo "  ON SART: her iki olcekte R^2 > 0,85 ve x0 veri ICINDE."
echo "=============================================================="

python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --n-lhs 24 --t-end 0.024 --dilim "$DILIM" \
    --root-seed "$TASARIM_TOHUMU" --sahne-tohum "$SAHNE_TOHUM" \
    --kademeler $ORTA \
    --out "$KOK/kampanya/I_orta_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "I/$SLURM_ARRAY_TASK_ID rc=$rc"
exit $rc
