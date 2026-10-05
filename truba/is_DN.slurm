#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J DN_nisan
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/DN_%A.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/DN_%A.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# PROTOKOL-DY S9 (kilitli): DY2 ile BIREBIR AYNI sahne; degisen TEK sey
# NISAN YONU. Carpma noktasi kutuptan 25,0 m kirise tasiniyor:
# yuzey noktasi (24,8901 ; 0 ; 55,6589), nisan birim (0,408231 ; 0 ; 0,912879).
# Gercek DART sekil merkezinden 25,0 +- 1,0 m uzaga carpti (Daly 2023).
# URETIM NISANI BU OLCUMLE DEGISMEZ (S9.4); yalniz kutup nisani seciminin
# BEDELINI butceye olculmus olarak yazar. KAPI DEGIL.
# ZORUNLU_EXPORT: AGAC
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC/SABIT_COMMIT uyusmuyor"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_dn"
source "$KOK/ortak_bas.sh"
cd "$AGAC"

AD=DN_nisan25_g1p0
TAS="$KOK/kampanya/DN_tasarim.json"
echo '{"theta": [[1.15, 10.0, 0.25]]}' > "$TAS.$SLURM_JOB_ID.tmp"  \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

# DY2 ile ayni: uc kure mermi, kalibre yogunluk, elipsoit, 17 derece, t_g = 1,0 s
ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin --yercekimi \
--gec-evre-t 1.0 --gec-evre-A 1.0e5 --dondurma-k 3.0 --dondurma-her 200 \
--impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
--model-sinifi M1 --mermi-kutlesi 579.4 --mermi-hizi 6144.9 \
--mermi-yogunlugu 1000.0 --carpma-acisi 17.0 --mu-f 0.6 --mermi-uc-kure \
--hedef-yari-eksenler 88.5 87.0 58.0 --yigin-yogunlugu 2306.1 \
--spacing 7.0 --kademeler kaba \
--nisan 24.8901 0.0 55.6589"

echo "DN  $AD  nisan 25 m kacik  kod: $AGAC_COMMIT"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 600 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" $ORTAK \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "DN ($AD) rc=$rc"
exit $rc
