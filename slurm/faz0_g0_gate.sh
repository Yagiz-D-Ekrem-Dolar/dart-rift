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
# Kural: /arf'a pip/conda kurulumu YAPILMAZ; warp wheel'i job-yerel diske acilir.

set -euo pipefail

REPO="${DRIFT_REPO:-/arf/scratch/egitimg16/driftclaude/dart-rift}"
WHEELS="${DRIFT_WHEELS:-/arf/scratch/egitimg16/driftclaude/wheels}"
LOCAL="${TMPDIR:-/tmp}/drift_${SLURM_JOB_ID}"
mkdir -p "$LOCAL/pylib" "$LOCAL/warp_cache"

module purge
module load apps/truba-ai/gpu-2024.0

echo "== dugum: $(hostname), GPU: =="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

# Ek paketler (warp-lang, pytest-cov, coverage) — /arf'a DEGIL, job-yerel dizine
python3 -m pip install --no-index --find-links "$WHEELS" \
    --target "$LOCAL/pylib" warp-lang pytest-cov coverage --quiet

export PYTHONPATH="$LOCAL/pylib:$REPO/src:$REPO/tests:${PYTHONPATH:-}"
export DARTRIFT_WARP_CACHE="$LOCAL/warp_cache"

cd "$REPO"
python3 -c "import warp; print('warp', warp.__version__)"
python3 scripts/run_g0_gate.py --require-gpu --run-dir "$REPO/gate_runs/g0_truba_${SLURM_JOB_ID}"
echo "== G0 kapi kosusu bitti; cikis kodu: $? =="
