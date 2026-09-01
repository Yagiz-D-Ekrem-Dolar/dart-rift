#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J a17_moloz
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/a17_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/a17_%j.err

set -euo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache"
cd "$KOK/dart-rift"

echo "=============================================================="
echo "S -- ORTAM SINAVI: uretim, t_end = 0,2 s"
echo "beklenen beta = 1.411216 (yerel ve TRUBA ile BIREBIR)"
echo "=============================================================="
python scripts/faz48_iki_asama.py --device cuda:0 --t-end 0.2 \
    --out "$KOK/ciktilar/S_uretim.json"
S_RC=$?
if [ $S_RC -ne 0 ]; then
    echo "S KOLU DUSTU (rc=$S_RC) -- devam edilmiyor"
    exit $S_RC
fi

python - <<'PY'
import json, sys
d = json.load(open("/arf/scratch/egitimg16u1/driftclaude/ciktilar/S_uretim.json"))
b, a1 = d["beta"], d["A1"]
ok = abs(b - 1.4112162721355217) <= 1e-5 and abs(a1 - 2.0390593305845943) <= 1e-6
print(f"ORTAM SINAVI: beta={b!r} A1={a1!r} -> {'TUTTU' if ok else 'TUTMADI'}")
sys.exit(0 if ok else 3)
PY
if [ $? -ne 0 ]; then
    echo "ORTAM SINAVI TUTMADI -- B kolu KOSULMUYOR (olcut 0)"
    exit 3
fi

echo
echo "=============================================================="
echo "B -- GERCEK MOLOZ YIGINI: Y0 = 1 Pa (matris VE blok),"
echo "     yercekimi ACIK, t_end = 5 s"
echo "=============================================================="
python scripts/faz48_iki_asama.py --device cuda:0 \
    --Y0 1.0 --boulder-Y0 1.0 --yercekimli --t-end 5.0 --iz-every 2000 \
    --out "$KOK/ciktilar/B_moloz.json"
echo "B rc=$?"
echo "BITTI: $(date)"
