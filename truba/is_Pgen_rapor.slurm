#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J Pgen_rap
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=16:00:00
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/Pgen_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/Pgen_%j.err
set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export OMP_NUM_THREADS=16
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"
# Genel P raporu (PROTOKOL-P §4d-4f). --export: D, O, SN
#
# A84: `sbatch --export=ALL,D="a,b,c"` virgulu DEGISKEN AYIRICISI sayar;
# D yalniz ilk desene iner ve rapor sessizce tek kampanyayla kosar
# (2026-09-14: dort rapor "46 kosu, 23 theta" okudu). Desenler burada
# `+` ile ayrilir ve virgule cevrilir; havuz sayisi DENETLENIR.
D="${D//+/,}"
N_DESEN=$(echo "$D" | tr ',' '\n' | grep -c .)
echo "desen sayisi: $N_DESEN  ->  $D"
if [ -n "${BEKLENEN_DESEN:-}" ] && [ "$N_DESEN" != "$BEKLENEN_DESEN" ]; then
  echo "HATA: $BEKLENEN_DESEN desen bekleniyordu, $N_DESEN geldi"; exit 4
fi
K="$KOK/kampanya"
# A84 DENETIMI (2): desen basina npz sayisi. BEKLENEN_KOSU_EN_AZ verilmisse
# toplam bundan azsa is DURUR (exit 5); raporda okunan kosu sayisi da
# denetlenir (exit 6). Bir rapor sessizce eksik havuzla kosmaz.
IFS=',' read -r -a DESENLER <<< "$D"
N_NPZ=0
for d in "${DESENLER[@]}"; do
  n=$(ls "$K"/$d/nokta_*.npz 2>/dev/null | wc -l)
  echo "  desen $d: $n npz"
  N_NPZ=$((N_NPZ + n))
done
echo "toplam npz: $N_NPZ  (en az beklenen: ${BEKLENEN_KOSU_EN_AZ:-verilmedi})"
if [ -n "${BEKLENEN_KOSU_EN_AZ:-}" ] && [ "$N_NPZ" -lt "$BEKLENEN_KOSU_EN_AZ" ]; then
  echo "HATA (A84 denetimi): $N_NPZ npz < $BEKLENEN_KOSU_EN_AZ"; exit 5
fi
kosu_denetle () {  # $1: json; katli.n_kosu >= BEKLENEN_KOSU_EN_AZ - 8
python - "$1" "${BEKLENEN_KOSU_EN_AZ:-0}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
n = d.get("katli", {}).get("n_kosu", d.get("n_kosu", 0)); esik = int(sys.argv[2]) - 8
print(f"DENETIM {sys.argv[1]}: okunan kosu {n}, esik {esik} ->", "GECTI" if n >= esik else "DUSTU")
sys.exit(0 if n >= esik else 6)
PY
}
yol () {
python -u - "$1" <<'PY'
import json, os, sys
sys.path.insert(0, "scripts")
import p_kalibrasyon_raporu as pr
K = os.environ["KOK"] + "/kampanya"; o = sys.argv[1]
try:
    a = json.load(open(f"{K}/S_{o}_kuadratik.json")); b = json.load(open(f"{K}/S_{o}_gp.json"))
    y = pr.yol_sec(a["katli"], b["katli"])
except Exception as e:
    y = {"hata": str(e)}
print(f"YOL SECIMI {o}:", y); json.dump(y, open(f"{K}/S_{o}_yol.json", "w"), indent=1)
PY
}
export KOK
echo "=== N havuz $O ==="
python -u scripts/n_ayirt_raporu.py --kok "$K" --desen "$D" --json "$K/S_$SN.json"
for V in kuadratik gp; do
  echo "=== P-v4 $O $V ==="
  python -u scripts/p_kalibrasyon_raporu.py --kok "$K" --desen "$D" --s-n "$K/S_$SN.json" --vekil $V --artik kfold4 --katli --json "$K/S_${O}_$V.json"
  kosu_denetle "$K/S_${O}_$V.json" || exit 6
done
yol $O
for V in kuadratik gp; do
  echo "=== P-v4b $O $V ==="
  python -u scripts/p_kalibrasyon_raporu.py --kok "$K" --desen "$D" --s-n "$K/S_$SN.json" --vekil $V --artik kfold4 --katli --genis-gozlem --json "$K/S_${O}b_$V.json"
done
yol ${O}b
echo "=== sekil verisi $O ==="
python -u scripts/p_sekil_verisi.py --kok "$K" --desen "$D" --s-n "$K/S_$SN.json" --genis-gozlem --json "$K/P_sekil_${O}b.json"
python -u scripts/p_sekil_verisi.py --kok "$K" --desen "$D" --s-n "$K/S_$SN.json" --json "$K/P_sekil_${O}.json"
echo "Pgen $O bitti"
