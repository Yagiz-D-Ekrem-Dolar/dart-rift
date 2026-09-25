#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J A98K
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/A98K_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/A98K_%j.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya/a98k"
module load apps/truba-ai/gpu-2024.0

# ============================================================
# PROTOKOL A98K (docs/truba/PROTOKOL-A98K-KAZI-AKISI.md)
#   Kontrollu gec evre kazi akisi (Maxwell Z-modeli), 3 aralik x 4 kol,
#   TEK GPU'da SIRAYLA (kuyruga yigin yok). Var olan cikti atlanir
#   (yeniden gonderimde kaldigi yerden). Sira: once kaba, sonra ince --
#   kismi sonuc erken gelsin.
#
# SABITLENMIS AGAC. AGAC ve AGAC_COMMIT ZORUNLU; agac temiz ve beklenen
# commit'te olmali. SABIT_COMMIT'e (A98 kosularinin agaci) DOKUNULMAZ:
# A98'in bekleyen gorevi baslarken onu denetliyor.
# ZORUNLU_EXPORT: AGAC AGAC_COMMIT
# ============================================================
if [ -z "${AGAC:-}" ] || [ -z "${AGAC_COMMIT:-}" ]; then
  echo "HATA: AGAC ve AGAC_COMMIT verilmeli"; exit 2; fi
if [ ! -d "$AGAC/src/dartrift" ]; then echo "HATA: AGAC '$AGAC' bir dart-rift agaci degil"; exit 2; fi
BULUNAN=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$BULUNAN" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC $BULUNAN, beklenen $AGAC_COMMIT"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_a98k"
# ortak_bas.sh: tesisat (GPU), python 3.10, paket sinavi (AGAC'in dartrift'i).
source "$KOK/ortak_bas.sh"
cd "$AGAC"

T_END=40
CIK="$KOK/kampanya/a98k"
echo "A98K  kod: $BULUNAN  agac: $AGAC  t_end: $T_END"
for S in 1.0 0.5 0.25; do
  E=$(echo "$S" | sed -e 's/^1\.0$/1/' -e 's/\./p/')
  for KOL in av1 av01 av0 av01L; do
    AD="K_s${E}_${KOL}"
    if [ -f "$CIK/$AD.json" ]; then echo "  $AD zaten var -- atlandi"; continue; fi
    case $KOL in
      av1)   EK="" ;;
      av01)  EK="--av 0.1 0.2" ;;
      av0)   EK="--av 0 0" ;;
      av01L) EK="--av 0.1 0.2 --sureklilik-trL" ;;
    esac
    # shellcheck disable=SC2086
    python scripts/a98k_kazi_akisi.py --s "$S" $EK --t-end "$T_END" \
        --device cuda:0 --komsu bvh --her 10 --n-ornek 40 --etiket "$AD" \
        --out "$CIK/$AD.json"
    echo "  $AD rc=$?"
  done
done
if [ ! -f "$KOK/kampanya/S_A98K.json" ]; then
  python scripts/a98k_raporu.py --kok "$CIK" --json "$KOK/kampanya/S_A98K.json"
else
  python scripts/a98k_raporu.py --kok "$CIK"
fi
echo "A98K bitti rc=$?"
