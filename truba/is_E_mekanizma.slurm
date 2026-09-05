#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J E_mek
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=08:00:00
#SBATCH --array=0-5
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/E_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/E_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_e$SLURM_ARRAY_TASK_ID"

# TESISAT SINAVI + SERILESTIRILMIS PULL + SURUM KAYDI (A38/A39)
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# Merdiven R2 olceginde: N = 69 886, olculen 2,81 adim/s.
# A52: daha ince merdiven komsu sorgusu yuzunden 45 kat yavasliyor.
MERDIVEN="48:2.8 24:1.4 12:0.7 6:0.35 3:0.175"
ORTAK="--device cuda:0 --tek-asama --kademeler $MERDIVEN"

case $SLURM_ARRAY_TASK_ID in
  # --- E1: sok GERCEKTEN olusuyor mu (PROTOKOL-E1-ERKEN.md v2) ---
  # Sok mermiyi 6,0e-5 s'te geciyor = ~11 adim. Iz araligi 2000 idi;
  # yani depodaki HICBIR olcum canli soku gormedi (A45).
  0) ETIKET=E1a_uretim;  EK="--t-end 1e-3 --iz-every 2" ;;
  1) ETIKET=E1b_donuk;   EK="--t-end 1e-3 --iz-every 2 --alpha-donuk" ;;
  # --- E2: matris cekmede mi bagli (PROTOKOL-E2-CEKME.md) ---
  # A51: Y0 sekiz mertebe degisirken EOS cekme basinci
  # -1,518635e+07 Pa'da YEDI HANEYE KADAR AYNI kaliyor.
  2) ETIKET=E2a_uretim;  EK="--t-end 0.024 --iz-every 20" ;;
  3) ETIKET=E2b_kirpik;  EK="--t-end 0.024 --iz-every 20 --matris-cekme-yok" ;;
  # --- E3: yapay viskozite (A53) ---
  # Olculdu: alpha_av 1,0 -> 0,1 ile kacan kutle 132 kat artiyor VE
  # kutle agirlikli eksenel hiz 3188 kat DUSUYOR: 1264 m/s (jet) ->
  # 0,397 m/s (KAZI AKISI hiz olcegi). Yani akis ORTAYA CIKIYOR.
  # Ben bu kolu "hepsi kaba seviyeden" diye elemistim; eleme gerekcesi
  # gecerliydi ama SONUC yanlisti. E3 onu E2 ile AYNI kosulda tekrarliyor.
  4) ETIKET=E3_av_dusuk; EK="--t-end 0.024 --iz-every 20 --alpha-av 0.1 --beta-av 0.2" ;;
  # E3o: AV ORTA nokta. A53'un acik sorusu 'akis cozunurlukte yasiyor
  # mu' idi ve dogru sinav BIR KADEME INCE kol olurdu -- ama A52
  # yuzunden 107 SAAT surerdi (sinir 24). Onun yerine AV'yi ARADA
  # tutup mekanizmanin SUREKLI mi yoksa esikli mi oldugunu olcuyoruz:
  # surekliyse AV gercek bir kontrol parametresi, esikliyse sayisal.
  5) ETIKET=E3o_av_orta; EK="--t-end 0.024 --iz-every 20 --alpha-av 0.4 --beta-av 0.8" ;;
  *) echo "bilinmeyen gorev"; exit 1 ;;
esac

echo "=============================================================="
echo "E/$ETIKET   ek bayrak = '$EK'"
echo ""
echo "YARGI KURALLARI KOSUDAN ONCE COMMIT EDILDI:"
echo "  docs/truba/PROTOKOL-E1-ERKEN.md  (v2)"
echo "  docs/truba/PROTOKOL-E2-CEKME.md"
echo ""
echo "E1 KARARI: rho_max > 2702,7 mi (kati sikismasi VAR mi)."
echo "  Esik payi sart: gozeneksiz kolda sayisal artik 2700,1 idi."
echo "E2 KARARI: r>R sayisiyla DEGIL. v_r dagilimi, kacis hizini"
echo "  asan kutle (r>R sarti OLMADAN) ve krater gidisi ile."
echo "  ON SART: iki kolun rho_max gidisi ORTUSMELI; ortusmezse"
echo "  deney SONUCSUZDUR."
echo "=============================================================="

python scripts/faz48_iki_asama.py $ORTAK $EK \
    --out "$KOK/kampanya/E_${ETIKET}.json"
rc=$?
echo "$ETIKET rc=$rc"
exit $rc
