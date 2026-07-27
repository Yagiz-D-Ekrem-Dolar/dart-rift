#!/bin/bash
#SBATCH -J drift_g12
#SBATCH -p kolyoz-cuda
#SBATCH -C H100
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH --gres=gpu:1
#SBATCH --time=03:00:00
#SBATCH --output=g12_%j.out
#SBATCH --error=g12_%j.out
# DART-RIFT FAZ 1 + FAZ 2 kapi kanitlari (TRUBA / ARF-ACC)
#
# Kuyruk notu: arizali dugumler hariç tutulur. Bilinen arizalar:
#   palamut5 -> /arf'a VERI yazamiyor (dd 5MB -> 0 bayt)
#   palamut6 -> /arf'tan buyuk dosya OKUYAMIYOR (warp/_src/types.py ImportError)
#   kolyoz13 -> GPU surucu arizasi ("No devices were found")
# Saglam oldugu dogrulanan dugumler: kolyoz19, palamut4.
# Gonderim: sbatch --exclude=kolyoz13,palamut5,palamut6 slurm/faz12_gates.sh
#
# stderr STDOUT'a birlestirilir: arizali dugumlerde ayri stderr dosyasi
# sessizce kaybolabiliyor ve hata mesajsiz "basarili" gibi gorunuyordu.

set -euo pipefail

REPO="${DRIFT_REPO:-/arf/scratch/egitimg16/driftclaude/dart-rift}"
PYLIB="${DRIFT_PYLIB:-/arf/scratch/egitimg16/driftclaude/pylib}"
LOCAL="${TMPDIR:-/tmp}/drift_${SLURM_JOB_ID}"
mkdir -p "$LOCAL/warp_cache"
trap 'rm -rf "$LOCAL"' EXIT

module purge
module load apps/truba-ai/gpu-2024.0

echo "== dugum: $(hostname) =="
if ! nvidia-smi --query-gpu=name,driver_version --format=csv,noheader; then
    echo "HATA: GPU sorgulanamiyor — DONANIM ARIZASI, kapi sonucu DEGIL." >&2
    echo "  sbatch --exclude=$(hostname),kolyoz13,palamut5,palamut6 ..." >&2
    exit 75   # EX_TEMPFAIL
fi
echo "== python: $(python3 --version 2>&1) =="

export PYTHONPATH="$PYLIB:$REPO/src:$REPO/tests:${PYTHONPATH:-}"
export DARTRIFT_WARP_CACHE="$LOCAL/warp_cache"
export WARP_CACHE_PATH="$LOCAL/warp_cache"

# Ortam saglik kontrolu: warp gercekten import edilebiliyor mu?
# (palamut6'da pylib OKUNAMADIGI icin bu adim sessizce coküyordu)
if ! python3 -u -c "import warp; print('warp', warp.__version__)"; then
    echo "HATA: warp import edilemedi — pylib bu dugumden okunamiyor." >&2
    echo "  Bu bir DEPOLAMA arizasidir, kapi sonucu DEGIL." >&2
    exit 75
fi
python3 -u -c "import warp as wp; wp.init(); print('cihazlar:', [str(d) for d in wp.get_devices()])"

cd "$REPO"

echo "########## G1 KAPISI (DR-RIFT-P1 §7) ##########"
python3 -u scripts/run_g1_gate.py --device cuda:0 \
    --run-dir "$REPO/gate_runs/g1_truba_${SLURM_JOB_ID}"
g1=$?

echo "########## G2 KAPISI (DR-RIFT-P2 §7) ##########"
python3 -u scripts/run_g2_gate.py --device cuda:0 \
    --run-dir "$REPO/gate_runs/g2_truba_${SLURM_JOB_ID}"
g2=$?

echo "== G1 cikis=$g1  G2 cikis=$g2 =="
exit $(( g1 != 0 ? g1 : g2 ))
