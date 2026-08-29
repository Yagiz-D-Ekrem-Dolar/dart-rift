#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J merdiven
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/merdiven_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/merdiven_%j.err

# A25 CARESI: kademeli (oz-benzer) inceltme, TEK ASAMA.
#
# Merdiven ile iki asamali yol BIRLESMIYOR: aktarim r<r1'i kabalastirdigi
# icin merdivenin ic seviyelerini ogutur (faz48 bunu SystemExit ile
# reddediyor). Bu yuzden --tek-asama.
#
# OLCUT 0 (plumbing): uretim kolu once kosulur ve beta/A1 birebir tutmali;
# tutmazsa merdiven kolu KOSULMAZ. Bu deponun kurali.

set -u
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache"
cd "$KOK/dart-rift"

echo "=============================================================="
echo "S -- ORTAM SINAVI (olcut 0): uretim, t_end = 0,2 s"
echo "beklenen beta = 1.411216, A1 = 2.039059"
echo "=============================================================="
python scripts/faz48_iki_asama.py --device cuda:0 --t-end 0.2 \
    --out "$KOK/ciktilar/M_S_uretim.json" || exit $?

python - <<'PY'
import json, sys
d = json.load(open("/arf/scratch/egitimg16u1/driftclaude/ciktilar/M_S_uretim.json"))
b, a1 = d["beta"], d["A1"]
ok = abs(b - 1.4112162721355217) <= 1e-5 and abs(a1 - 2.0390593305845943) <= 1e-6
print(f"ORTAM SINAVI: beta={b!r} A1={a1!r} -> {'TUTTU' if ok else 'TUTMADI'}")
sys.exit(0 if ok else 3)
PY
[ $? -eq 0 ] || { echo "ORTAM SINAVI TUTMADI -- merdiven KOSULMUYOR"; exit 3; }

echo
echo "=============================================================="
echo "T -- TABAN CIZGISI: tek basamak, ayni s_min, AYNI t_end"
echo "     beklenen: kaba seviyede soklanan parcacik = 0 (A25)"
echo "=============================================================="
python scripts/faz48_iki_asama.py --device cuda:0 --tek-asama \
    --lam2 10 --r-ince2 3 --t-end 0.2 \
    --out "$KOK/ciktilar/M_T_tekbasamak.json"
echo "T rc=$?"

echo
echo "=============================================================="
echo "M -- MERDIVEN (oz-benzer, r/s = 8,6): s_min = 0,35 m, r_dis = 24 m"
echo "     kabuklar  r<3:0,35  3-6:0,70  6-12:1,40  12-24:2,80"
echo "     beklenen N ~ 51 000, H100'de ~1,4 saat"
echo "     GECER <=> kaba seviyelerde de soklanan parcacik VAR"
echo "=============================================================="
python scripts/faz48_iki_asama.py --device cuda:0 --tek-asama \
    --kademeler 24:1.25 12:2.5 6:5 3:10 --t-end 0.2 --iz-every 500 \
    --out "$KOK/ciktilar/M_merdiven.json"
echo "M rc=$?"

echo
echo "SOK YARGILARI (kosular kendi yargisini tasiyor, ADR-0049):"
python - <<'PY'
import json, pathlib
kok = pathlib.Path("/arf/scratch/egitimg16u1/driftclaude/ciktilar")
for ad in ("M_T_tekbasamak", "M_merdiven"):
    y = kok / f"{ad}.json"
    if not y.exists():
        print(f"  {ad}: DOSYA YOK"); continue
    d = json.loads(y.read_text())
    s = d.get("sok", {})
    print(f"  {ad}: sikisma_max=%{s.get('sikisma_max_yuzde', float('nan')):.3f} "
          f"[{s.get('yargi')}]  beta={d.get('beta')}")
PY
echo "BITTI: $(date)"
