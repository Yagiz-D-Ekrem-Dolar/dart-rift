#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J F_avc
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=08:00:00
#SBATCH --array=0-5
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/F_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/F_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_f$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# F -- AV x COZUNURLUK IZGARASI
#
# A53: alpha_av 1,0 -> 0,1 ile <v> 1264 m/s (jet) -> 0,397 m/s
# (kazi akisi) oluyor ve kacan kutle 132 kat artiyor.
#
# ACIK SORU: bu kaba parcacik artefakti mi?
# Dogru sinav BIR KADEME INCE merdivendi ama A52 yuzunden 107 saat
# surerdi. Onun yerine IKI MEVCUT olcekte tekrarliyoruz:
#   KABA = R1 olcegi (N = 17 201, olculen 5 dk/kosu)
#   ORTA = R2 olcegi (N = 69 886, olculen ~1,2 sa/kosu)
#
# Mekanizma IKISINDE DE duruyorsa cozunurluk-dirençli bir iddia olur.
# ============================================================

KABA="48:5.6 24:2.8 12:1.4 6:0.7 3:0.35"
ORTA="48:2.8 24:1.4 12:0.7 6:0.35 3:0.175"

case $SLURM_ARRAY_TASK_ID in
  0) ETIKET=F_kaba_av10; MERD="$KABA"; AV="--alpha-av 1.0 --beta-av 2.0" ;;
  1) ETIKET=F_kaba_av04; MERD="$KABA"; AV="--alpha-av 0.4 --beta-av 0.8" ;;
  2) ETIKET=F_kaba_av01; MERD="$KABA"; AV="--alpha-av 0.1 --beta-av 0.2" ;;
  3) ETIKET=F_orta_av10; MERD="$ORTA"; AV="--alpha-av 1.0 --beta-av 2.0" ;;
  4) ETIKET=F_orta_av04; MERD="$ORTA"; AV="--alpha-av 0.4 --beta-av 0.8" ;;
  5) ETIKET=F_orta_av01; MERD="$ORTA"; AV="--alpha-av 0.1 --beta-av 0.2" ;;
  *) echo "bilinmeyen gorev"; exit 1 ;;
esac

echo "=============================================================="
echo "F/$ETIKET   merdiven='$MERD'   AV='$AV'"
echo ""
echo "YARGI (docs/truba/PROTOKOL-F-AV.md, KOSUDAN ONCE commit'lendi):"
echo "  Olculen: <v> = P_kacan_hedef / kutle_kacan_hedef"
echo "  1) <v> her iki olcekte de alpha_av ile MONOTON azaliyorsa"
echo "     -> AV gercek bir kontrol parametresi (SUREKLI mekanizma)"
echo "  2) Yalniz bir olcekte gorunuyorsa -> COZUNURLUK ARTEFAKTI"
echo "  3) Etki iki olcekte AYNI YONDE ama farkli buyuklukte"
echo "     -> mekanizma gercek, buyuklugu cozulmemis"
echo "=============================================================="

python scripts/faz48_iki_asama.py --device cuda:0 --tek-asama \
    --kademeler $MERD --t-end 0.024 --iz-every 200 $AV \
    --out "$KOK/kampanya/${ETIKET}.json"
rc=$?
echo "$ETIKET rc=$rc"
exit $rc
