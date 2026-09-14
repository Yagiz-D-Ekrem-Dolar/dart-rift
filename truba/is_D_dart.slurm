#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J D_dart
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/D_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/D_%j.err
set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export OMP_NUM_THREADS=16
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"
K="$KOK/kampanya"
# ============================================================
# PROTOKOL D -- GERCEK DART GOZLEMI (docs/truba/PROTOKOL-D-DART-GOZLEM.md)
#   Q1 (Mt) + Q2/Q3 (Ntk, Nto) + ince-72 bittikten sonra.
#   A84: desenler '+' ile; her havuz once SAYILIR, eksikse o adim atlanir
#   ve rapora "ATLANDI" yazilir (sessiz eksik havuz YOK).
# ============================================================
say () { t=0; IFS='+' read -r -a ds <<< "$1"; for d in "${ds[@]}"; do n=$(ls $K/$d/nokta_*.npz 2>/dev/null | wc -l); t=$((t+n)); done; echo $t; }
for L in kaba orta; do
  echo "=== cozunurluk hatasi Mt $L ==="
  python -u scripts/cozunurluk_hatasi.py --kok "$K" --onek Mt --uretim $L --json "$K/S_cozunurluk_Mt_$L.json"
done
calis () {  # $1 desen  $2 cikti  $3 en az npz  [$4 cozunurluk json]
  n=$(say "$1")
  if [ "$n" -lt "$3" ]; then echo "ATLANDI $2: $n npz < $3"; return 0; fi
  echo "=== D $2 ($n npz) ==="
  ek=""; [ -n "${4:-}" ] && ek="--cozunurluk $4"
  python -u scripts/dart_gozlem_posterior.py --kok "$K" --desen "$1" $ek --json "$K/$2"
}
calis "Nto_matris_sahne*.durumlar+N2to_matris_sahne*.durumlar" S_DART_Qo.json 86 "$K/S_cozunurluk_Mt_orta.json"
calis "Ntk_matris_sahne*.durumlar+N2tk_matris_sahne*.durumlar" S_DART_Qk.json 86 "$K/S_cozunurluk_Mt_kaba.json"
calis "Ni_matris_sahne*.durumlar+N2i_matris_sahne*.durumlar+N3i_matris_sahne*.durumlar" S_DART_i72.json 130
echo "=== Bitis 3 taslagi ==="
python -u scripts/bitis3_raporu.py --kok "$K" --cikti "$K/BITIS3-TASLAK.md"
echo "D bitti"
