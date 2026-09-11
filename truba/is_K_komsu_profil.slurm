#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J K_komsu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=05:00:00
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/K_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/K_%j.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_k"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# K -- A52: hash <-> destek kutulu BVH, H100'de ADIM SURESI
#
# Yerel RTX 3050'de (FP64 = FP32/64) kaba merdivende hizlanma 1,59x.
# Tuketici GPU'da FP64 fizik cekirdekleri baskin olabilir; H100'de
# (FP64 = FP32/2) aday taramasinin payi farkli. Uzman: "Aday
# sayisindan 100 kat cozucu hizlanmasi vaat etmem" -- OLCUYORUZ.
# Durum farki da yazilir (yalniz toplama sirasi beklenir).
# ============================================================
echo "kod: $(git rev-parse HEAD)"
nvidia-smi --query-gpu=name --format=csv,noheader
for K in kaba orta; do
  python scripts/komsu_profil.py --kademeler $K --adim 40 \
      --json "$KOK/kampanya/K_komsu_profil_${K}.json"
done

# ------------------------------------------------------------
# A73 -- mevcut kampanya durumlarina FIZIKSEL YUZEY OPERATORU.
# Giris dugumunde calistirilan surec, G1'in 48 durumunu olcup sigmoid
# uydurmasina gecmisken DISARIDAN OLDURULDU (iz yok, JSON yok). Burada
# ayrilmis kaynakla ve nokta basina ilerleme yazarak.
# BETIMLEYICI: kilitli yargilar degismez.
# ------------------------------------------------------------
export OMP_NUM_THREADS=4
python -u scripts/yuzey_krater_raporu.py \
    --kol G1 "$KOK/kampanya/G1_uretim_sahne*.durumlar" \
    --kol G2 "$KOK/kampanya/G2_kirpik_sahne*.durumlar" \
    --kol I  "$KOK/kampanya/I_orta_sahne*.durumlar" \
    --json "$KOK/kampanya/YUZEY_RAPOR_G1_G2_I.json"
