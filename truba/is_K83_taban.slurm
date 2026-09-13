#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J K83_taban
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --array=0-18
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/K83_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/K83_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_k83$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# A83 DOGRULAMA -- YOGUNLUK TABANI (docs/truba/PROTOKOL-A83-TABAN.md)
#   0-11 : K83  -- M kaba 6 theta x 2 tohum, kesme + taban   (V2: K80 ile)
#   12-17: Nkd  -- patlayan uc theta x iki tohum, kaba        (V1 + havuz dolgusu)
#          12,13: N  #10   14,15: N2 #6   16,17: N2 #18  (cift=20260906)
#   18   : Tkt  -- T matris 99991111, 0,2 s                    (V1)
#   tasarim dosyalari: kampanya/A83_tasarim_{N10,N2_6,N2_18}.json (gonderimde)
# ============================================================
TOHUMLAR=(20260906 99991111)
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0 --dayanim-kesme --yogunluk-tabani"
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 12 ]; then
  K=$((i / 2)); S=${TOHUMLAR[$((i % 2))]}
  TAS="$KOK/kampanya/M_tasarim_t${K}.json"; TEND=0.024
  OUT="$KOK/kampanya/K83_kaba_t${K}_sahne${S}.jsonl"
elif [ "$i" -lt 18 ]; then
  ADLAR=(N10 N2_6 N2_18); j=$((i - 12)); AD=${ADLAR[$((j / 2))]}; S=${TOHUMLAR[$((j % 2))]}
  TAS="$KOK/kampanya/A83_tasarim_${AD}.json"; TEND=0.024
  # Havuz deseni icin ayri kampanya adi; theta dosyadan.
  OUT="$KOK/kampanya/Nkd_matris_${AD}_sahne${S}.jsonl"
else
  S=99991111; TAS="$KOK/kampanya/T_tasarim.json"; TEND=0.2
  OUT="$KOK/kampanya/Tkt_matris_sahne${S}.jsonl"
fi
if [ ! -f "$TAS" ]; then echo "tasarim dosyasi yok: $TAS"; exit 2; fi
echo "K83/$i  tasarim=$TAS  sahne=$S  t_end=$TEND  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end "$TEND" --root-seed 20260906 --sahne-tohum "$S" \
    --tasarim-dosyasi "$TAS" --kademeler kaba $ORTAK \
    --out "$OUT"
rc=$?
echo "K83/$i rc=$rc"
exit $rc
