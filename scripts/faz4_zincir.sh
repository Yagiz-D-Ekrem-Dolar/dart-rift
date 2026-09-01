#!/bin/bash
# FAZ 4 zinciri — kota yenilendiginde TEK KOMUTLA kosar.
#
# 4.4 -> 4.5 -> 4.6 -> 4.7 (kapi raporu). Her adim bir onceki adimin
# JSON'unu YAZAR, kapi hepsini OKUR. Ara adim duserse kapi zaten
# "kosulmadi" der; zincir sessizce yesil gorunmez.
set -euo pipefail

set -u                      # -e YOK: bir adim duserse kalanlar da kosmali
# Depo koku betigin KENDI konumundan turetiliyor -- Python kosucularla
# ayni kural. Sabit yol, depo tasindiginda sessizce yanlis src'yi bulur.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CIK="$(dirname "$REPO")"
echo "REPO=$REPO"
echo "CIK=$CIK"

echo "##### FAZ 4.4 — DART cozunurluk yakinsamasi #####"
python -u "$REPO/scripts/faz44_dart_yakinsama.py" \
    --steps 3000 --every 250 --out "$CIK/faz44_sonuc.json"
echo "rc44=$?"

echo; echo "##### FAZ 4.5 — gereken simule sure #####"
python -u "$REPO/scripts/faz45_durulma.py" \
    --steps 20000 --every 100 --out "$CIK/faz45_sonuc.json"
echo "rc45=$?"

echo; echo "##### FAZ 4.6 — sentetik kurtarma #####"
# NOT: `ileri_kosu` UYGULANDI ama GPU kismi HIC KOSULMADI (kota). Ilk
# gercek kosuda burasi duserse sasirtici degil; kapi G4-C'yi "kosulmadi"
# sayar ve zincir devam eder. Once `--kuru` ile hattin calistigi
# dogrulanmisti (C1 %100, C2 0.142, C3 4.81x).
python -u "$REPO/scripts/faz46_sentetik_kurtarma.py" \
    --out "$CIK/faz46_sonuc.json"
echo "rc46=$?"

echo; echo "##### FAZ 4.7 — G4 kapi raporu #####"
python -u "$REPO/scripts/faz47_g4_kapi.py" \
    --faz44 "$CIK/faz44_sonuc.json" \
    --faz45 "$CIK/faz45_sonuc.json" \
    --faz46 "$CIK/faz46_sonuc.json" \
    --out "$REPO/docs/G4-KAPI-RAPORU.md"
echo "rc47=$?  (1 = kapi GECILEMEDI, beklenen olabilir)"
