#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J G_ayirt
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --array=0-11
#SBATCH --exclude=kolyoz19
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/G_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/G_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_g$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$KOK/dart-rift"

# ============================================================
# G -- GOZLENEBILIR IC YAPIYI AYIRT EDIYOR MU
#      (docs/truba/PROTOKOL-G-AYIRT.md, kosudan ONCE commit'lendi)
#
# BU SINAV BUGUNE KADAR HIC GECERLI YAPILMADI (rapor A46): surucu
# `sahne_taban=None` gonderiyordu, sahne M0 oluyordu ve M0 dalinda
# BLOK YERLESTIRILMIYOR. theta'nin uc bileseninden IKISI sahneye
# hic ulasmiyordu.
#
# IKI KOL (E2 sonucu, rapor SONUC-E-F-MEKANIZMA.md):
#   G1 = URETIM. Gozlenebilir OLDUGU GIBI theta bilgisi tasiyor mu?
#   G2 = CEKME KIRPIK. E2 olctu: kacan parcacik 45 -> 3 318,
#        delta_beta 0,0352 -> 0,2715. Yani kazi akisi ORADA VAR.
#        Soru: akis var oldugunda gozlenebilir theta'yi ayirt ediyor mu?
#
#   G1 "hayir" + G2 "evet" -> bilgi icerigi CEKME KUSURU yuzunden
#   yok oluyor ve kusur giderilince GERI GELIYOR. En guclu sonuc.
#
# GURULTU TABANI: ayni 24 nokta IKI sahne gerceklemesiyle.
# TASARIM tohumu iki kolda da AYNI (A57) -- yoksa farkli theta'lar
# orneklenir ve eslestirme sifir cikar.
# ============================================================

TASARIM_TOHUMU=20260906

case $SLURM_ARRAY_TASK_ID in
  # --- G1: uretim ---
  0)  KOL=G1_uretim; DILIM="0/3"; SAHNE_TOHUM=20260906; EK="" ;;
  1)  KOL=G1_uretim; DILIM="1/3"; SAHNE_TOHUM=20260906; EK="" ;;
  2)  KOL=G1_uretim; DILIM="2/3"; SAHNE_TOHUM=20260906; EK="" ;;
  3)  KOL=G1_uretim; DILIM="0/3"; SAHNE_TOHUM=99991111; EK="" ;;
  4)  KOL=G1_uretim; DILIM="1/3"; SAHNE_TOHUM=99991111; EK="" ;;
  5)  KOL=G1_uretim; DILIM="2/3"; SAHNE_TOHUM=99991111; EK="" ;;
  # --- G2: cekme kirpik (TANI kolu, uretim modeli DEGIL) ---
  6)  KOL=G2_kirpik; DILIM="0/3"; SAHNE_TOHUM=20260906; EK="--matris-cekme-yok" ;;
  7)  KOL=G2_kirpik; DILIM="1/3"; SAHNE_TOHUM=20260906; EK="--matris-cekme-yok" ;;
  8)  KOL=G2_kirpik; DILIM="2/3"; SAHNE_TOHUM=20260906; EK="--matris-cekme-yok" ;;
  9)  KOL=G2_kirpik; DILIM="0/3"; SAHNE_TOHUM=99991111; EK="--matris-cekme-yok" ;;
  10) KOL=G2_kirpik; DILIM="1/3"; SAHNE_TOHUM=99991111; EK="--matris-cekme-yok" ;;
  11) KOL=G2_kirpik; DILIM="2/3"; SAHNE_TOHUM=99991111; EK="--matris-cekme-yok" ;;
  *) echo "bilinmeyen gorev"; exit 1 ;;
esac

echo "=============================================================="
echo "G/$SLURM_ARRAY_TASK_ID  $KOL  dilim=$DILIM"
echo "  tasarim tohumu = $TASARIM_TOHUMU  (IKI KOLDA DA AYNI)"
echo "  sahne tohumu   = $SAHNE_TOHUM     (gurultu tabani)"
echo "  ek bayrak      = '$EK'"
echo ""
echo "ON KOSULLAR (biri duserse sonuc OKUNMAZ):"
echo "  1) n_kacan_hedef >= 1 olan nokta orani >= %80"
echo "     (nicelik krater_derinlik ise UYGULANMAZ)"
echo "  2) her noktada defter kapali (|artik_bagil| < 1e-10)"
echo "  3) her noktada sok yargisi KISMI veya SOK_VAR"
echo "  4) alpha0 UC benzersiz deger tasimali (mermi+matris+blok)"
echo "     -- iki tanesi varsa A46 geri gelmis demektir"
echo ""
echo "YARGI: F > 4 VE en az bir theta bileseniyle |rho| > 0,5 (p<0,05)"
echo "  -> AYIRT EDIYOR.  Rapor: scripts/ayirt_raporu.py"
echo "=============================================================="

python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --n-lhs 24 --t-end 0.024 --dilim "$DILIM" \
    --root-seed "$TASARIM_TOHUMU" --sahne-tohum "$SAHNE_TOHUM" \
    --kademeler kaba $EK \
    --out "$KOK/kampanya/${KOL}_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "G/$SLURM_ARRAY_TASK_ID ($KOL) rc=$rc"
exit $rc
