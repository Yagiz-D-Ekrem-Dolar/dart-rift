#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J No_orta
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --array=0-11
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/No_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/No_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_no$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# N ve N2 tasarimlari ORTA merdivende (s_min 0,175 m).
#   Protokol M kaba/orta/ince yakinsamasini soyluyor; hangi merdivenin
#   uretim oldugu M'nin yargisina bagli. Orta nokta basina ~550 s
#   (M/12-15 olculdu), 96 nokta ~15 GPU-saat: M'yi beklemeden koşuluyor
#   ki karar ciktiginda veri hazir olsun. Yargi kurallari N ve P'nin
#   AYNISI; yalniz --desen farkli.
#   0-5 : N  tasarimi (root_seed 20260906) -> No_matris_sahne*
#   6-11: N2 tasarimi (root_seed 20260914) -> N2o_matris_sahne*
#   her altı: sahne 20260906 dilim 0..2/3, sahne 99991111 dilim 0..2/3
# ============================================================
TOHUMLAR=(20260906 99991111)
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0"
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 6 ]; then TAS=20260906; AD=No; else TAS=20260914; AD=N2o; fi
j=$((i % 6))
SAHNE_TOHUM=${TOHUMLAR[$((j / 3))]}
DILIM="$((j % 3))/3"
echo "No/$i  tasarim=$TAS  sahne=$SAHNE_TOHUM  dilim=$DILIM  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --n-lhs 24 --t-end 0.024 --dilim "$DILIM" \
    --root-seed "$TAS" --sahne-tohum "$SAHNE_TOHUM" \
    --kademeler orta $ORTAK \
    --out "$KOK/kampanya/${AD}_matris_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "No/$i ($AD) rc=$rc"
exit $rc
