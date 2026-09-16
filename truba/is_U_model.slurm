#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J U_model
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=10:00:00
#SBATCH --array=0-19
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/U_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/U_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_u$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL U -- MODEL YETERLILIGI (docs/truba/PROTOKOL-U-MODEL.md)
#   0-15 : 8 varyant x 2 tohum, kaba, 0,1 s
#   16-19: U0 ve U8 x 2 tohum, orta, 0,1 s
# ============================================================
TOHUMLAR=(20260906 99991111)
AD=(U0 U1 U2 U3 U4 U5 U6 U8)
TH=("1.15 1.0e5 0.275" "1.15 1.0e1 0.275" "1.15 1.0e0 0.275" "1.15 1.0e5 0.275" \
    "1.15 1.0e5 0.275" "1.15 1.0e5 0.275" "1.15 1.0e5 0.275" "1.15 1.0e0 0.275")
EK=("" "--onsel-disi-izin" "--onsel-disi-izin" "--mu-f 0.2" "--mu-f 0.05" \
    "--porozite-pe 1e5 --porozite-ps 1e7" "--yigin-yogunlugu 1500" \
    "--onsel-disi-izin --mu-f 0.2 --porozite-pe 1e5 --porozite-ps 1e7 --yigin-yogunlugu 1500")
ORTAK="--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh --carpma-sahasi matris --saha-yaricapi 3.0 --dayanim-kesme --yogunluk-tabani"
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -lt 16 ]; then v=$((i / 2)); LAD=kaba; S=${TOHUMLAR[$((i % 2))]}
else j=$((i - 16)); v=$(( (j / 2) == 0 ? 0 : 7 )); LAD=orta; S=${TOHUMLAR[$((j % 2))]}; fi
A=${AD[$v]}
TAS="$KOK/kampanya/U_tasarim_${A}.json"
read -r TA TY TF <<< "${TH[$v]}"
# Atomik yazim (2026-09-16): ayni varyantin iki tohumu (ör. gorev 0 ve 1) AYNI
# dosyaya yaziyor. `> "$TAS"` biri dosyayi sifirlarken otekinin python'u okursa
# bos JSON okuyup duserdi. Gecici dosya + mv -f: okuyan her zaman tam dosya gorur.
echo "{\"theta\": [[$TA, $TY, $TF]]}" > "$TAS.$SLURM_JOB_ID.tmp" && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"
echo "U/$i  varyant=$A  merdiven=$LAD  sahne=$S  ek=${EK[$v]}  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 0.1 --root-seed 20260906 --sahne-tohum "$S" \
    --tasarim-dosyasi "$TAS" --kademeler "$LAD" $ORTAK ${EK[$v]} \
    --out "$KOK/kampanya/U_${A}_${LAD}_sahne${S}.jsonl"
rc=$?
echo "U/$i ($A $LAD) rc=$rc"
exit $rc
