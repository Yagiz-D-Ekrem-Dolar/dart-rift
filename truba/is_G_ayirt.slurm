#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J G_ayirt
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --array=0-5
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
# BU SINAV BUGUNE KADAR HIC GECERLI YAPILMADI (rapor A46):
# surucu `sahne_taban=None` gonderiyordu, `build_scene` varsayilani
# `M0` idi ve `M0` dalinda BLOK YERLESTIRILMIYOR. Yani theta'nin
# uc bileseninden IKISI sahneye hic ulasmiyordu.
#
# Olculdu (duzeltmeden SONRA, uretim olceginde):
#   theta=(1,05; 1e4; 0,10) -> 1109 blok parcacigi, matris a0 1,5896
#   theta=(1,30; 1e4; 0,40) -> 3448 blok parcacigi, matris a0 1,6430
#   ayni theta, tohum 999   -> 1055 blok parcacigi, matris a0 1,5844
# yani theta etkisi gerceklem gurultusunden ~44 kat buyuk.
#
# GURULTU TABANI: ayni 24 nokta IKI root_seed ile kosuluyor.
# root_seed blok YERLESIMINI belirledigi icin ikinci tohum ayni
# fizigin farkli gerceklemesidir.
#   F = Var(theta'lar arasi) / ortalama(gerceklemeler arasi)
#
# AV: F kampanyasinin KAZANANI. Sebep (A53/A56): uretim AV'sinde
# kaba olcekte gozlenebilir HIC VAR OLMUYOR (Rb_R1: n_kacan = 0).
# Once var olmali ki ayirt edip etmedigi sorulabilsin.
# ============================================================

# --- F KAMPANYASI SONUCUNA GORE DOLDURULACAK ---
# Varsayilan uretim; F "AV gercek kontrol parametresi" derse
# 0.1/0.2 yapilacak ve bu satir commit'lenerek degistirilecek.
AV="${G_AV:---alpha-av 0.1 --beta-av 0.2}"

# Kaba merdiven: olculen 5 dk/nokta (Rb_R1 00:05:06, N = 17 201).
# `--kademeler kaba` kisayolu SURUCUDE tanimli (MERDIVEN_KABA);
# burada elle yazmak A26 sinifi olcek uyusmazligi riski tasirdi.

# 24 nokta / 3 dilim = 8 nokta/gorev; iki tohum = 6 gorev
# TASARIM tohumu IKI KOLDA DA AYNI -- yoksa iki kol FARKLI theta'lar
# ornekler ve `ayirt_raporu` hicbir eslesme bulamaz (rapor A57).
# Degisen tek sey SAHNE gerceklemesi: `--sahne-tohum`.
TASARIM_TOHUMU=20260906

case $SLURM_ARRAY_TASK_ID in
  0) DILIM="0/3"; SAHNE_TOHUM=20260906 ;;
  1) DILIM="1/3"; SAHNE_TOHUM=20260906 ;;
  2) DILIM="2/3"; SAHNE_TOHUM=20260906 ;;
  3) DILIM="0/3"; SAHNE_TOHUM=99991111 ;;
  4) DILIM="1/3"; SAHNE_TOHUM=99991111 ;;
  5) DILIM="2/3"; SAHNE_TOHUM=99991111 ;;
  *) echo "bilinmeyen gorev"; exit 1 ;;
esac

echo "=============================================================="
echo "G/$SLURM_ARRAY_TASK_ID  dilim=$DILIM  tasarim=$TASARIM_TOHUMU  sahne=$SAHNE_TOHUM  AV='$AV'"
echo ""
echo "ON KOSULLAR (biri duserse sonuc OKUNMAZ):"
echo "  1) n_kacan_hedef >= 1 olan nokta orani >= %80"
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
    --kademeler kaba $AV \
    --out "$KOK/kampanya/G_sahne${SAHNE_TOHUM}.jsonl"
rc=$?
echo "G/$SLURM_ARRAY_TASK_ID rc=$rc"
exit $rc
