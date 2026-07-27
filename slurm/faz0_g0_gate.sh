#!/bin/bash
#SBATCH -J drift_g0
#SBATCH -p kolyoz-cuda
#SBATCH -C H100
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH --gres=gpu:1
#SBATCH --time=00:45:00
#SBATCH --output=g0_%j.out
#SBATCH --error=g0_%j.err
#
# Kuyruk notu: palamut-cuda'daki palamut5 dugumu /arf'a VERI yazamiyor
# (metadata yazilir, dd 5MB -> 0 bayt; job 1425490 exit 10). Ayni test
# kolyoz19/H100'de 587 MB/s ile temiz gecti (job 1425491). Kanit kosulari
# bu yuzden kolyoz-cuda/H100'de yapilir.
# DART-RIFT FAZ 0 — G0 kapi kaniti (TRUBA / ARF-ACC)
#
# TRUBA kurali: /arf'a pip/conda ile paket KURULMAZ. Ek paketler (warp-lang,
# pytest-cov, coverage) pip calistirilmadan, wheel arsivleri acilarak hazir bir
# dizinden PYTHONPATH ile kullanilir (toplam 639 dosya; inode kotasi 500.000).
# Hazirlik ADIMLARI GIRIS DUGUMUNDE bir kez yapilir, hesap dugumunde degil:
#
#   cd /arf/scratch/<grup>/driftclaude
#   module purge && module load apps/truba-ai/gpu-2024.0
#   python3 -m pip download warp-lang pytest-cov coverage --no-deps -d wheels
#   mkdir -p pylib
#   for w in wheels/*.whl; do python3 -m zipfile -e "$w" pylib; done
#
# (Hesap dugumunde wheel acma/kopyalama denendi ve kararsiz cikti — bkz.
#  docs/defter, job 1425474 ve 1425480.)

set -euo pipefail
set -x

REPO="${DRIFT_REPO:-/arf/scratch/egitimg16/driftclaude/dart-rift}"
PYLIB="${DRIFT_PYLIB:-/arf/scratch/egitimg16/driftclaude/pylib}"
LOCAL="${TMPDIR:-/tmp}/drift_${SLURM_JOB_ID}"
mkdir -p "$LOCAL/warp_cache"
trap 'rm -rf "$LOCAL"' EXIT

module purge
module load apps/truba-ai/gpu-2024.0

set +x
echo "== dugum: $(hostname) =="
# GPU saglik kontrolu: TRUBA'da arizali dugume dusmek mumkun (or. kolyoz13,
# "No devices were found"). Bunu erken ve NET bir mesajla ayirt et ki
# donanim arizasi bizim kodumuzun hatasi gibi gorunmesin.
if ! nvidia-smi --query-gpu=name,driver_version --format=csv,noheader; then
    echo "HATA: bu dugumde GPU sorgulanamiyor — DONANIM/SURUCU ARIZASI." >&2
    echo "Kodla ilgisi yok; isi baska dugume gonderin:" >&2
    echo "  sbatch --exclude=$(hostname) slurm/faz0_g0_gate.sh" >&2
    exit 75   # EX_TEMPFAIL: gecici altyapi hatasi, kapi sonucu DEGIL
fi
echo "== python: $(python3 --version 2>&1) =="
set -x

export PYTHONPATH="$PYLIB:$REPO/src:$REPO/tests:${PYTHONPATH:-}"
# Warp kernel onbellegi job-yerel diske; /arf'a yazma yok.
export DARTRIFT_WARP_CACHE="$LOCAL/warp_cache"
export WARP_CACHE_PATH="$LOCAL/warp_cache"

python3 -c "import warp; print('warp', warp.__version__)"
python3 -c "import warp as wp; wp.init(); print('cihazlar:', [str(d) for d in wp.get_devices()])"

cd "$REPO"

# 1) Kirmizi-takim kontrol listesi (§12) — teslimden once isletilir.
set +x
echo "########## KIRMIZI TAKIM (DR-RIFT-P0 §12) ##########"
set -x
python3 scripts/run_red_team.py --run-dir "$REPO/gate_runs/redteam_truba_${SLURM_JOB_ID}"

# 2) G0 kapisi (§9) — sekiz kriter, GPU roundtrip atlanamaz.
set +x
echo "########## G0 KAPISI (DR-RIFT-P0 §9) ##########"
set -x
python3 scripts/run_g0_gate.py --require-gpu --run-dir "$REPO/gate_runs/g0_truba_${SLURM_JOB_ID}"
rc=$?
set +x
echo "== Kirmizi takim + G0 kapi kosusu bitti; cikis kodu: $rc =="
exit $rc
