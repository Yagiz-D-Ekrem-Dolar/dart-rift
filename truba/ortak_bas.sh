#!/bin/bash
# ortak_bas.sh -- her TRUBA isinin basinda `source` edilir.
#   Is betigi once KOK'u tanimlar, modulu yukler, PYTHONPATH'i verir; sonra bunu.
#
# 2026-09-16: egitimg16u3 (YagizTRUBA) icin DEPODA yeniden yazildi. Eski kopya
# yalniz TRUBA'daydi (u1/u4) ve u3'ten okunamadi -- bir daha kaybolmasin diye
# surumlu. Eski gorevleri (FAZ4-SIKINTI-RAPORU, "uc duzeltme tek dosyada"):
# tesisat sinavi + kosum surumu kaydi. BILINCLI SAPMA: isin basindaki
# `git pull` KALDIRILDI -- bir dizinin gorevleri farkli kodla kosabiliyordu.
# Kod artik $KOK/SABIT_COMMIT ile sabitlenir.
#
# Cikis kodlari (sessiz yanlis kosu yerine ilk saniyede dur):
#   91 tesisat : nvidia-smi GPU gormuyor
#   92 kod     : calisma agaci kirli ya da SABIT_COMMIT'ten farkli
#   93 python  : ortam python'u 3.10 degil (modul sonrasi bile sistem 3.9'a gidebiliyor)
#   94 paket   : numpy / warp / dartrift ice aktarilamiyor

: "${KOK:?ortak_bas.sh: KOK tanimli degil}"

ORTAM_BIN=/arf/sw/apps/truba-ai/gpu/miniforge3-2024/envs/gpu-2024.0/bin
export PATH="$ORTAM_BIN:$PATH"

if ! nvidia-smi -L >/dev/null 2>&1; then
  echo "TESISAT SINAVI DUSTU: nvidia-smi GPU gormuyor (host $(hostname))"
  exit 91
fi

if ! cd "$KOK/dart-rift" 2>/dev/null; then
  echo "KOD YOK: $KOK/dart-rift"
  exit 92
fi
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "KOD KIRLI: calisma agacinda commit'lenmemis degisiklik var"
  git status --short --untracked-files=no
  exit 92
fi
KOSUM_COMMIT=$(git rev-parse HEAD)
if [ -f "$KOK/SABIT_COMMIT" ] && [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$KOSUM_COMMIT" ]; then
  echo "KOD SURUMU YANLIS: beklenen $(cat "$KOK/SABIT_COMMIT"), bulunan $KOSUM_COMMIT"
  exit 92
fi

if ! python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 10) else 1)'; then
  echo "PYTHON YANLIS: $(command -v python) $(python -V 2>&1)"
  exit 93
fi
if ! python -c 'import numpy, warp, dartrift' >/dev/null 2>&1; then
  echo "PAKET EKSIK:"
  python -c 'import numpy, warp, dartrift'
  exit 94
fi

echo "ortak_bas: host=$(hostname) gpu=[$(nvidia-smi -L | head -1)] python=$(python -V 2>&1)" \
     "commit=$KOSUM_COMMIT is=${SLURM_JOB_ID:-yok}/${SLURM_ARRAY_TASK_ID:-tek}"
cd - >/dev/null || true
