#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J DUMAN
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/DUMAN_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/DUMAN_%j.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya/duman"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_duman"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# DUMAN SINAVI -- protokol DEGIL, bilimsel veri DEGIL (2026-09-16).
#   Yeni hesapta (egitimg16u3) U'dan ONCE uctan uca boru hatti: ortam,
#   warp CUDA derlemesi, sahne + kademeli inceltme, cozucu, npz yazimi.
#   U ile ayni uretim bayraklari ve U0 merkez theta; t_end 3 ms; sok kapisi
#   KAPALI (amac fizik degil, yazma yolu). Ciktilar kampanya/duman/ altinda,
#   U raporunun deseniyle (U_*) karismaz.
# ============================================================
TAS="$KOK/kampanya/duman/tasarim_U0.json"
echo '{"theta": [[1.15, 1.0e5, 0.275]]}' > "$TAS"
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0 --dayanim-kesme --yogunluk-tabani"
echo "DUMAN kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.003 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --kademeler kaba $ORTAK --sok-kapisi-kapali \
    --out "$KOK/kampanya/duman/DUMAN_U0_kaba.jsonl"
rc=$?
echo "DUMAN surucu rc=$rc"
[ "$rc" -ne 0 ] && exit $rc

python - "$KOK/kampanya/duman" <<'PY'
import glob
import json
import sys

import numpy as np

d = sys.argv[1]
satir = [json.loads(s) for s in open(f"{d}/DUMAN_U0_kaba.jsonl") if s.strip()]
npz = sorted(glob.glob(f"{d}/DUMAN_U0_kaba.durumlar/nokta_*.npz"))
print("DUMAN jsonl satir:", len(satir), " npz:", len(npz))
ok = len(satir) >= 1 and len(npz) >= 1
if npz:
    z = np.load(npz[0])
    ft = json.loads(str(z["fizik_tani"]))
    b = float(ft.get("beta_hedef", float("nan")))
    print("DUMAN t =", float(z["t"]), " beta_hedef =", b, " N =", len(z["m"]))
    ok = ok and bool(np.isfinite(b))
print("DUMAN SONUC:", "GECTI" if ok else "DUSTU")
sys.exit(0 if ok else 8)
PY
