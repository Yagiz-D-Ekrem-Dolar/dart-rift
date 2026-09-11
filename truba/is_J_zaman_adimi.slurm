#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J J_zaman
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --array=0-83
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/J_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/J_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_j$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL J -- SABIT h'DE ZAMAN ADIMI  (+ I2)
#   docs/truba/PROTOKOL-J-ZAMAN-ADIMI.md, kosudan ONCE commit'lendi
#
# Uzman (2026-09-11): kuvvet GERI DONDURULMEMIS deneme gerilmesini
# goruyor; fazlalik ~ (sqrt3/2) G gamma_dot dt. Rapor A72 dogruladi
# (125 parcacik, Y = 100 Pa: q/Y = 1 966).
#
#  0-11 : I2 -- ORTA merdiven, ara kipi, cfl 0,25  (en uzun, ONCE)
# 12-47 : J1 -- kaba, uretim cekmesi (G1 kosulu), 6 kol
# 48-83 : J2 -- kaba, cekme kirpik (G2 kosulu, TANI), 6 kol
# ============================================================

TASARIM_TOHUMU=20260906
TOHUMLAR=(20260906 99991111)
KIPLER=(son son son ara ara ara)
CFLLER=(0.25 0.125 0.0625 0.25 0.125 0.0625)
CETIK=(c0250 c0125 c0625 c0250 c0125 c0625)

i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 12 ]; then
  SER=I2; j=$i
  TNO=$((j / 6)); DNO=$((j % 6))
  KIP=ara; CFL=0.25; CET=c0250
  DILIM="$DNO/6"; KADEME=""; EK=""
elif [ "$i" -lt 48 ]; then
  SER=J1; j=$((i - 12)); EK=""
  KNO=$((j / 6)); r=$((j % 6)); TNO=$((r / 3)); DNO=$((r % 3))
  KIP=${KIPLER[$KNO]}; CFL=${CFLLER[$KNO]}; CET=${CETIK[$KNO]}
  DILIM="$DNO/3"; KADEME="--kademeler kaba"
elif [ "$i" -lt 84 ]; then
  SER=J2; j=$((i - 48)); EK="--matris-cekme-yok"
  KNO=$((j / 6)); r=$((j % 6)); TNO=$((r / 3)); DNO=$((r % 3))
  KIP=${KIPLER[$KNO]}; CFL=${CFLLER[$KNO]}; CET=${CETIK[$KNO]}
  DILIM="$DNO/3"; KADEME="--kademeler kaba"
else
  echo "bilinmeyen gorev $i"; exit 1
fi
SAHNE_TOHUM=${TOHUMLAR[$TNO]}
KOL=${SER}_${KIP}_${CET}

echo "=============================================================="
echo "J/$i  $KOL  dilim=$DILIM  sahne=$SAHNE_TOHUM"
echo "  akma kipi = $KIP   cfl = $CFL   ek = '$EK'   kademe = '$KADEME'"
echo "  kod: $(git rev-parse HEAD)"
echo ""
echo "ON KOSULLAR (dt_raporu.py, kilitli):"
echo "  O1 kol basina tamamlanan >= %90"
echo "  O2 sigmoid R2 > 0,85 ve x0 veri icinde"
echo "  O3 ara kolunda HER noktada kuvvet ani q/Y <= 1 + 1e-9"
echo "  O4 J1_son_c0250 <-> G1 bit-tekrar"
echo "=============================================================="

python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --n-lhs 24 --t-end 0.024 --dilim "$DILIM" \
    --root-seed "$TASARIM_TOHUMU" --sahne-tohum "$SAHNE_TOHUM" \
    $KADEME $EK --cfl "$CFL" --akma-kipi "$KIP" \
    --out "$KOK/kampanya/${KOL}_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "J/$i ($KOL) rc=$rc"
exit $rc
