#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J H_kryak
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=08:00:00
#SBATCH --array=0-5
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/H_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/H_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_h$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# H -- KRATER DERINLIGININ COZUNURLUK YAKINSAMASI
#      (docs/truba/PROTOKOL-H-KRATER.md, kosudan ONCE commit'lendi)
#
# G1 olctu: krater derinligi theta'yi AYIRT EDIYOR
#   F = 1006, matris_Y0 ile rho = -0,9417 (p < 0,0001).
# Ama TEK cozunurlukte (kaba, N = 17 201).
#
# beta'nin yakinsamasi A52 yuzunden IMKANSIZ (R3 icin 224 saat).
# Krater icin DEGIL: kaba ve orta merdivenlerin ikisi de
# karsilanabilir. Bu kampanya o iki noktayi kuruyor.
#
# TASARIM: AYNI LHS tasariminin ayni uc noktasi, iki cozunurlukte,
# iki sahne gerceklemesiyle. `--dilim 0/8` -> nokta 0, 8, 16.
#
# Uc nokta az; bu yuzden IDDIA da kucuk tutuluyor: "krater
# derinliginin theta-tepkisi cozunurlukle KORUNUYOR mu" -- Richardson
# derecesi DEGIL.
# ============================================================

TASARIM_TOHUMU=20260906
KABA="48:5.6 24:2.8 12:1.4 6:0.7 3:0.35"
ORTA="48:2.8 24:1.4 12:0.7 6:0.35 3:0.175"

case $SLURM_ARRAY_TASK_ID in
  0) KOL=H_kaba;   MERD="$KABA"; SAHNE_TOHUM=20260906; DILIM="0/8" ;;
  1) KOL=H_kaba;   MERD="$KABA"; SAHNE_TOHUM=99991111; DILIM="0/8" ;;
  2) KOL=H_orta;   MERD="$ORTA"; SAHNE_TOHUM=20260906; DILIM="0/8" ;;
  3) KOL=H_orta;   MERD="$ORTA"; SAHNE_TOHUM=99991111; DILIM="0/8" ;;
  4) KOL=H_orta_b; MERD="$ORTA"; SAHNE_TOHUM=20260906; DILIM="1/8" ;;
  5) KOL=H_orta_b; MERD="$ORTA"; SAHNE_TOHUM=99991111; DILIM="1/8" ;;
  *) echo "bilinmeyen gorev"; exit 1 ;;
esac

echo "=============================================================="
echo "H/$SLURM_ARRAY_TASK_ID  $KOL  dilim=$DILIM  sahne=$SAHNE_TOHUM"
echo "  merdiven = $MERD"
echo ""
echo "YARGI (PROTOKOL-H-KRATER.md, KOSUDAN ONCE):"
echo "  1) Her theta icin |d_orta - d_kaba| / d_orta olculur."
echo "  2) Ayni theta'nin iki gerceklemesi arasindaki fark GURULTU."
echo "  3) KARAR: cozunurluk farki, gurultu tabaninin uc katindan"
echo "     kucukse krater derinligi bu iki olcek arasinda KORUNUYOR."
echo "     Buyukse KORUNMUYOR ve G1'in sonucu tek olcege bagli kalir."
echo "  Bu bir Richardson derecesi DEGIL; iki noktali bir DIRENC"
echo "  sinavidir ve oyle bildirilir."
echo "=============================================================="

python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --n-lhs 24 --t-end 0.024 --dilim "$DILIM" \
    --root-seed "$TASARIM_TOHUMU" --sahne-tohum "$SAHNE_TOHUM" \
    --kademeler $MERD \
    --out "$KOK/kampanya/${KOL}_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "H/$SLURM_ARRAY_TASK_ID ($KOL) rc=$rc"
exit $rc
