#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J V_model
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-9
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/V_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/V_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_v$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL V -- KOSULLU (docs/truba/PROTOKOL-V-MODEL2.md)
#   YALNIZ U genel yargisi "HICBIR VARYANT ULASMIYOR" ise gonderilir.
#   5 varyant x 2 tohum, kaba, 0,2 s. V4 ek bayraklari gonderimde:
#     sbatch --export=ALL,V4_EK="--mu-f 0.2 ..." is_V_model.slurm
#   (A84: V4_EK icinde VIRGUL KULLANMA)
# ============================================================
if [ -z "${V4_EK+x}" ]; then echo "HATA: V4_EK verilmedi (U'nun en yakin varyanti)"; exit 2; fi
# 2026-09-15 oz denetim (gonderimden ONCE): V4_U eskiden ${V4_U:-U0} ile sessizce U0
# sayiliyordu ve U_tasarim dosyasi yoksa V4 sessizce merkez theta ile kosuyordu.
if [ -z "${V4_U:-}" ]; then echo "HATA: V4_U verilmedi (or. U2)"; exit 2; fi
TOHUMLAR=(20260906 99991111)
AD=(V0 V1 V2 V3 V4)
EK=("" "--yercekimi" "--hasar" "--yercekimi --hasar" "$V4_EK --yercekimi --hasar")
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0 --dayanim-kesme --yogunluk-tabani"
i=$SLURM_ARRAY_TASK_ID
v=$((i / 2)); S=${TOHUMLAR[$((i % 2))]}; A=${AD[$v]}
TH="1.15 1.0e5 0.275"
if [ "$A" = V4 ]; then
  # U'nun en yakin varyantinin theta'si (V4_U, or. U2) U_tasarim'dan alinir;
  # onsel disi Y0 ise V4_EK '--onsel-disi-izin' icermelidir.
  TAS_U="$KOK/kampanya/U_tasarim_${V4_U}.json"
  if [ ! -f "$TAS_U" ]; then echo "HATA: $TAS_U yok -- V4 theta'si U'dan alinamadi"; exit 3; fi
  TH=$(python -c "import json;t=json.load(open('$TAS_U'))['theta'][0];print(*t)") \
    || { echo "HATA: $TAS_U okunamadi"; exit 3; }
fi
TAS="$KOK/kampanya/V_tasarim_${A}.json"
read -r TA TY TF <<< "$TH"
echo "{\"theta\": [[$TA, $TY, $TF]]}" > "$TAS"
echo "V/$i  varyant=$A  sahne=$S  ek=${EK[$v]}  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.2 --root-seed 20260906 --sahne-tohum "$S" \
    --tasarim-dosyasi "$TAS" --kademeler kaba $ORTAK ${EK[$v]} \
    --out "$KOK/kampanya/V_${A}_kaba_sahne${S}.jsonl"
rc=$?
echo "V/$i ($A) rc=$rc"
exit $rc
