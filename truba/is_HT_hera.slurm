#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J HT_hera
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=03:00:00
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/HT_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/HT_%j.err
set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export OMP_NUM_THREADS=16
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"
K="$KOK/kampanya"
# PROTOKOL HT -- Hera on kayitlari (docs/truba/PROTOKOL-HT-HERA-TAHMIN.md)
# A84: desenler '+' ile; havuz sayilir, eksikse o kayit ATLANIR (sessiz eksik yok).
say () { t=0; IFS='+' read -r -a ds <<< "$1"; for d in "${ds[@]}"; do n=$(ls $K/$d/nokta_*.npz 2>/dev/null | wc -l); t=$((t+n)); done; echo $t; }
kayit () {  # $1 desen  $2 etiket  $3 en az  [$4 cozunurluk]
  n=$(say "$1")
  if [ "$n" -lt "$3" ]; then echo "ATLANDI $2: $n npz < $3"; return 0; fi
  ek=""; [ -n "${4:-}" ] && ek="--cozunurluk $4"
  python -u scripts/hera_tahmin.py --kok "$K" --desen "$1" $ek --etiket "$2" --cikti-dizini "$K"
}
kayit "Nto_matris_sahne*.durumlar+N2to_matris_sahne*.durumlar" Qo 86 "$K/S_cozunurluk_Mt_orta.json"
kayit "Ni_matris_sahne*.durumlar+N2i_matris_sahne*.durumlar+N3i_matris_sahne*.durumlar" i72 130
echo "HT bitti"
