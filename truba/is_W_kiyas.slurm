#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J W_kiyas
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-5
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/W_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/W_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_w$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# PROTOKOL W -- KIYAS SINAMASI (docs/truba/PROTOKOL-W-KIYAS.md)
#   L1 = Raducan & Jutzi 2022, PSJ 3, 128, Tablo 2 (kure, f = 0,6):
#     Y0 = 50 / 10 / 1 Pa  ->  beta = 3,63 / 4,18 / 4,66
#   Tasarim: 3 Y0 x 2 gecis ani (0,2 s ve 1,0 s), tek tohum, kaba.
#   `T_END` ZORUNLU: PROTOKOL-W S3.2 kurali W0 zamanlama kosusuna gore
#   secer; sessiz varsayilan YOK.
# ============================================================
if [ -z "${T_END:-}" ]; then echo "HATA: T_END verilmedi (PROTOKOL-W S3.2)"; exit 2; fi
# ZORUNLU_EXPORT: T_END
Y0=(50.0 50.0 10.0 10.0 1.0 1.0)
YAD=(50 50 10 10 1 1)
GEC=(0.2 1.0 0.2 1.0 0.2 1.0)
GAD=(0p2 1p0 0p2 1p0 0p2 1p0)
i=$SLURM_ARRAY_TASK_ID
if [ "$i" -ge 6 ]; then echo "HATA: gorev $i tanimsiz"; exit 3; fi

TAS="$KOK/kampanya/W_tasarim_Y${YAD[$i]}.json"
echo "{\"theta\": [[1.15, ${Y0[$i]}, 0.0]]}" > "$TAS.$SLURM_JOB_ID.$i.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.$i.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin"
KIYAS="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 \
--mu-f 0.6 --yercekimi"

AD="W_Y${YAD[$i]}_g${GAD[$i]}"
echo "W/$i  $AD  Y0=${Y0[$i]} Pa  t_gecis=${GEC[$i]} s  t_end=$T_END s  kod: $(git rev-parse HEAD)"
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end "$T_END" --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --kademeler kaba $ORTAK $KIYAS \
    --gec-evre-t "${GEC[$i]}" --gec-evre-A 1.0e5 \
    --dondurma-k 3.0 --dondurma-her 200 \
    --impuls-log --beta-km --azami-adim 20000000 \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "W/$i ($AD) rc=$rc"
exit $rc
