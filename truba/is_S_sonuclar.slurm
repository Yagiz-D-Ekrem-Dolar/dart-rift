#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J S_sonuc
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/S_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/S_%j.err

# ============================================================
# S -- J / K / L BITINCE BUTUN RAPORLAR, TEK ISTE
#
# Gonderim (bagimlilikla, kendiliginden baslar):
#   sbatch --dependency=afterany:1555356:1555431:1555432 truba/is_S_sonuclar.slurm
#
# Neden is: giris dugumunde calistirilan yuzey raporu surec disaridan
# olduruldu (iz yok, JSON yok). Burada ayrilmis kaynakla.
# Kilitli yargilar (dt_raporu, duyarlilik_raporu) + BETIMLEYICI ekler
# (yuzey, kacis) AYRI dosyalara yazilir.
# ============================================================
set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export OMP_NUM_THREADS=8
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"
K="$KOK/kampanya"
echo "kod: $(git rev-parse HEAD)"

echo "=== KILITLI: Protokol J (J1, J2, I2, O4) ==="
python -u scripts/dt_raporu.py --kok "$K" --seri J1 --json "$K/S_J1.json"
python -u scripts/dt_raporu.py --kok "$K" --seri J2 --json "$K/S_J2.json"
python -u scripts/dt_raporu.py --kok "$K" --i2 --tekrar --json "$K/S_I2_O4.json"

echo "=== KILITLI: Protokol L (duyarlilik pilotu) ==="
python -u scripts/duyarlilik_raporu.py --kok "$K" \
    --kol L_ara_kirpik L_son_uretim --json "$K/S_L.json"

echo "=== BETIMLEYICI: yuzey operatoru (A73), J/I2 kollari ==="
python -u scripts/yuzey_krater_raporu.py \
    --kol J1_son_c0250  "$K/J1_son_c0250_sahne*.durumlar" \
    --kol J1_son_c0625  "$K/J1_son_c0625_sahne*.durumlar" \
    --kol J1_ara_c0250  "$K/J1_ara_c0250_sahne*.durumlar" \
    --kol J1_ara_c0625  "$K/J1_ara_c0625_sahne*.durumlar" \
    --kol I2_ara_c0250  "$K/I2_ara_c0250_sahne*.durumlar" \
    --json "$K/S_yuzey_J.json"

echo "=== BETIMLEYICI: enerji tabanli kacis (uzman S10) ==="
python -u scripts/kacis_raporu.py \
    --kol G2_kirpik     "$K/G2_kirpik_sahne*.durumlar" \
    --kol J2_ara_c0250  "$K/J2_ara_c0250_sahne*.durumlar" \
    --kol L_ara_kirpik  "$K/L_ara_kirpik_sahne*.durumlar" \
    --json "$K/S_kacis.json"

echo "=== ENERJI DEFTERI (A77): kol basina e_tot sapmasi ==="
python -u - <<'EOF'
import glob, json, numpy as np
K = "/arf/scratch/egitimg16u1/driftclaude/kampanya/"
for kol in sorted({p.split("/")[-2].split("_sahne")[0]
                   for p in glob.glob(K + "*_sahne*.durumlar/nokta_*.npz")}):
    s = []
    for f in glob.glob(K + kol + "_sahne*.durumlar/nokta_*.npz"):
        z = np.load(f)
        if "enerji" in z.files:
            s.append(json.loads(str(z["enerji"]))["e_tot_bagil_sapma"])
    if s:
        print(f"{kol:>22}  n={len(s):3d}  e_tot sapma medyan {np.median(s):+.3e}"
              f"  min {np.min(s):+.3e}  max {np.max(s):+.3e}")
EOF
echo "S bitti"
