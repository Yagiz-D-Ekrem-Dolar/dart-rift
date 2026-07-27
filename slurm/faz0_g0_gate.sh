#!/bin/bash
#SBATCH -J drift_g0
#SBATCH -p palamut-cuda
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH --gres=gpu:1
#SBATCH --time=00:45:00
#SBATCH --output=g0_%j.out
#SBATCH --error=g0_%j.err
# DART-RIFT FAZ 0 — G0 kapi kaniti (TRUBA / ARF-ACC)
#
# TRUBA kurali: /arf'a pip/conda ile paket KURULMAZ. Ek paketler (warp-lang,
# pytest-cov, coverage) job-yerel diske ($TMPDIR, node-local) acilir. Wheel bir
# zip arsividir; pip yerine `python -m zipfile` ile acariz — boylece pip'in
# /arf uzerindeki onbellek/derleme dizinlerine hic dokunulmaz.
#
# Onkosul (giris dugumunde bir kez):
#   python3 -m pip download warp-lang pytest-cov coverage --no-deps \
#       -d /arf/scratch/<grup>/driftclaude/wheels

set -euo pipefail

REPO="${DRIFT_REPO:-/arf/scratch/egitimg16/driftclaude/dart-rift}"
WHEELS="${DRIFT_WHEELS:-/arf/scratch/egitimg16/driftclaude/wheels}"
LOCAL="${TMPDIR:-/tmp}/drift_${SLURM_JOB_ID}"
PYLIB="$LOCAL/pylib"
mkdir -p "$PYLIB" "$LOCAL/warp_cache"
trap 'rm -rf "$LOCAL"' EXIT

module purge
module load apps/truba-ai/gpu-2024.0

echo "== dugum: $(hostname) =="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
echo "== python: $(python3 --version 2>&1) =="

# Wheel'leri once job-yerel diske KOPYALA, sonra oradan ac.
# (Lustre uzerinden dogrudan zip okumak hesap dugumunde BadZipFile uretti —
#  job 1425474; ayni dosyalar giris dugumunde testzip'ten temiz gecmisti.)
cp "$WHEELS"/*.whl "$LOCAL/"
for whl in "$LOCAL"/*.whl; do
    echo "-- aciliyor: $(basename "$whl")  ($(stat -c%s "$whl") bayt, md5 $(md5sum "$whl" | cut -c1-12))"
    python3 -m zipfile -e "$whl" "$PYLIB"
done

export PYTHONPATH="$PYLIB:$REPO/src:$REPO/tests:${PYTHONPATH:-}"
export DARTRIFT_WARP_CACHE="$LOCAL/warp_cache"
export WARP_CACHE_PATH="$LOCAL/warp_cache"

python3 -c "import warp; print('warp', warp.__version__)"
python3 -c "import warp as wp; wp.init(); print('cihazlar:', [str(d) for d in wp.get_devices()])"

cd "$REPO"
RUN_DIR="$REPO/gate_runs/g0_truba_${SLURM_JOB_ID}"
python3 scripts/run_g0_gate.py --require-gpu --run-dir "$RUN_DIR"
rc=$?
echo "== G0 kapi kosusu bitti; cikis kodu: $rc =="
exit $rc
