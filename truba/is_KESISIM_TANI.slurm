#!/bin/bash
#SBATCH --job-name=kesisim_tani
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#
# Eksende KAC kez `phi = esik` kesisiliyor? Tahmin ve kapilar KOSUDAN
# ONCE kilitlendi: `scripts/tani_krater_kesisim_sayisi.py` docstring'i,
# commit 07d7bbb. Kaynak sorun: KAYIT-091 §7 (13 tek tanili nokta).
#
# NICIN GPU DEGIL: yalnizca kayitli `npz` durum dosyalari okunur ve
# CPU'da eksen boyunca doluluk ornekleniyor. Warp/GPU kullanilmaz,
# dolayisiyla `ortak_bas.sh` (nvidia-smi sinavi, cikis 91) KOSULMAZ ve
# kullanicinin GPU butcesi HARCANMAZ. Gec dokumlu kosu (1639229) 4 GPU
# tutuyor; bu is ona dokunmaz.
#
# NICIN GIRIS DUGUMUNDE DEGIL: giris dugumunde `ulimit -t = 300 s`;
# ayni sinifta bir is ~4m42s CPU harcayip "CPU time limit exceeded"
# ile olmustu (olculdu 2026-10-28). Sessiz yarim cikti yerine kuyruga.

set -euo pipefail

KOK=${KOK:-/arf/scratch/egitimg16u3/driftclaude}
AGAC=${AGAC:-$KOK/agac_havuz}
KAMPANYA=${KAMPANYA:-$KOK/kampanya}
CIKTI=${CIKTI:-$KOK/tani_kesisim_sayisi.json}

export PATH=/arf/sw/apps/truba-ai/gpu/miniforge3-2024/envs/gpu-2024.0/bin:$PATH
export PYTHONPATH="$KOK/pylib:$AGAC/src"
# A-serisi ders: OpenBLAS is parcacigi sayisi serbest birakilinca
# cekirdek dokumu aliniyordu.
export OMP_NUM_THREADS=4

cd "$AGAC"
echo "commit: $(git rev-parse HEAD)"
echo "kirli : $(git status --porcelain | wc -l) dosya"
python -c "import sys, numpy; print('python', sys.version.split()[0], 'numpy', numpy.__version__)"

# Kume etiketleri depodaki CSV'den gelir; betik 96 BEKLER (kural 8).
python scripts/tani_krater_kesisim_sayisi.py \
    --kampanya "$KAMPANYA" \
    --tarama-csv "$AGAC/docs/sonuclar/havuz_krater_tarama_96.csv" \
    --cikti "$CIKTI" \
    --beklenen 96
