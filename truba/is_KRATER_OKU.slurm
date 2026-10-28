#!/bin/bash
#SBATCH --job-name=krater_oku
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#
# ADR-0061 + ADR-0062 sonrasi uretim havuzunun 96 noktasinda krater
# gozlemlisini YENIDEN OKUR. Kaynak: KAYIT-088 (kok sebep), KAYIT-089
# (duzeltmenin tek basina yetmedigi olcumu).
#
# NICIN GPU DEGIL: is yalnizca kayitli `npz` durum dosyalarini okuyup
# CPU'da doluluk es-yuzeyi tariyor. Warp/GPU kullanilmaz, dolayisiyla
# `ortak_bas.sh` (nvidia-smi tesisat sinavi, cikis 91) KOSULMAZ ve
# kullanicinin GPU butcesi HARCANMAZ.
#
# NICIN GIRIS DUGUMUNDE DEGIL: giris dugumunde `ulimit -t = 300 s`;
# is ~4m42s CPU harcayip "CPU time limit exceeded" ile oldu (olculdu
# 2026-10-28). Sessiz yarim cikti yerine kuyruga.

set -euo pipefail

KOK=${KOK:-/arf/scratch/egitimg16u3/driftclaude}
AGAC=${AGAC:-$KOK/agac_havuz}
KAMPANYA=${KAMPANYA:-$KOK/kampanya}
CIKTI=${CIKTI:-$KOK/havuz_krater_adr0062.json}
ONCEKI=${ONCEKI:-}

export PATH=/arf/sw/apps/truba-ai/gpu/miniforge3-2024/envs/gpu-2024.0/bin:$PATH
export PYTHONPATH="$KOK/pylib:$AGAC/src"
# A-serisi ders: OpenBLAS is parcacigi sayisi serbest birakilinca
# cekirdek dokumu aliniyordu.
export OMP_NUM_THREADS=4

cd "$AGAC"
echo "commit: $(git rev-parse HEAD)"
echo "kirli : $(git status --porcelain | wc -l) dosya"
python -c "import sys, numpy; print('python', sys.version.split()[0], 'numpy', numpy.__version__)"

ek=()
if [ -n "$ONCEKI" ]; then ek=(--onceki "$ONCEKI"); fi

python scripts/havuz_krater_yeniden_oku.py \
    --kampanya "$KAMPANYA" \
    --cikti "$CIKTI" \
    --beklenen 96 \
    "${ek[@]}"
