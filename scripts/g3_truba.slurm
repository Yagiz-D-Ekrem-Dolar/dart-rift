#!/bin/bash
# G3 kapisi + G0/G1/G2 regresyonu, TRUBA kolyoz-cuda (H100).
#
# Calistirma:  sbatch scripts/g3_truba.slurm
#
# NOT (ADR-0005 / KAYIT-009): --exclude bayragi BETIGIN ICINDE durur, komut
# satirinda degil. Bir kere "bayragi hatirla" diye yorum birakilmisti ve
# unutuldu; kolyoz13'e dusen is CUDA error 999 ile cikti 2 verdi ve kapi
# basarisizligi gibi gorundu. Dugum arizasi kapi sonucu DEGILDIR.
#SBATCH -J drift_g3
#SBATCH -p kolyoz-cuda
#SBATCH -C H100
#SBATCH -N 1
#SBATCH -n 1
# KUME KURALI: kolyoz-cuda kuyrugu cekirdek sayisinin 16'NIN KATI olmasini
# sart kosar. `-c 8` denendi ve reddedildi:
#   "kolyoz-cuda kuyruguna gonderilen islerin cekirdek sayisi 16 ve katlari
#    olmalidir / CPU count specification invalid"
# Yani cekirdek sayisi kucultulemez; kuyrukta beklerken kisilabilecek tek
# kalem SURE'dir. Olculen kosu ~45 dk oldugu icin 2 saat fazlasiyla yeter
# (6 saat istemek bos yere cekirdek x sure butcesi tuketiyordu).
#SBATCH -c 16
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=g3_%j.out
#SBATCH --error=g3_%j.out
#SBATCH --exclude=kolyoz13,palamut5,palamut6

set -uo pipefail
REPO=/arf/scratch/egitimg16/driftclaude/dart-rift
PYLIB=/arf/scratch/egitimg16/driftclaude/pylib
LOCAL="${TMPDIR:-/tmp}/drift_${SLURM_JOB_ID}"
mkdir -p "$LOCAL/warp_cache"
trap 'rm -rf "$LOCAL"' EXIT

module purge
module load apps/truba-ai/gpu-2024.0
echo "== dugum: $(hostname) =="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

# TRUBA kurali: /arf'a pip/conda kurulumu YOK. Paketler acilmis tekerlek
# olarak PYTHONPATH uzerinden gelir.
export PYTHONPATH="$PYLIB:$REPO/src:$REPO/tests:${PYTHONPATH:-}"
export DARTRIFT_WARP_CACHE="$LOCAL/warp_cache"
export WARP_CACHE_PATH="$LOCAL/warp_cache"

# Warp-CUDA saglik kontrolu: nvidia-smi GPU'yu gorse bile Warp acamayabilir.
# Bu bir DUGUM ARIZASIDIR, kapi sonucu DEGILDIR -> EX_TEMPFAIL(75).
if ! python3 -u -c "
import sys, warp as wp
wp.init()
d=[str(x) for x in wp.get_devices()]
print('cihazlar:', d)
sys.exit(0 if any(t.startswith('cuda') for t in d) else 1)
"; then
    echo "HATA: warp CUDA cihazi acamiyor — DUGUM ARIZASI, sonuc DEGIL." >&2
    exit 75
fi

cd "$REPO"
HEAD=$(git rev-parse --short HEAD)
echo "== depo commit: $HEAD =="

echo "########## G3 KAPISI (DR-RIFT-P3 §7) ##########"
python3 -u scripts/run_g3_gate.py --device cuda:0 --run-dir "$REPO/gate_runs/g3_truba_${HEAD}_${SLURM_JOB_ID}"
G3RC=$?
echo "== G3 rc=$G3RC =="

echo "########## G0+G1+G2 REGRESYON ##########"
python3 -u scripts/run_g0_gate.py --run-dir "$REPO/gate_runs/g0_truba_${HEAD}_${SLURM_JOB_ID}"
echo "== G0 rc=$? =="
python3 -u scripts/run_g1_gate.py --device cuda:0 --run-dir "$REPO/gate_runs/g1_truba_${HEAD}_${SLURM_JOB_ID}"
echo "== G1 rc=$? =="
python3 -u scripts/run_g2_gate.py --device cuda:0 --run-dir "$REPO/gate_runs/g2_truba_${HEAD}_${SLURM_JOB_ID}"
echo "== G2 rc=$? =="

# G3 cikis kodlari: 0 = tam gecti, 1 = kaldi, 2 = degerlendirilmedi (CUDA yok),
# 3 = kanitlanabilir kriterler gecti ama en az biri KANITLANAMADI (C7/PDS).
echo "== TUM KAPILAR BITTI, G3 rc=$G3RC =="

# SLURM YANILTMASI — OKUMADAN GECMEYIN:
# `sacct` yalnizca "COMPLETED / FAILED" ayrimi yapar. rc=3 sifir olmadigi icin
# is FAILED gorunur, oysa kanitlanabilir kriterlerin HEPSI gecmistir.
# Cikis kodu bilerek sifir DEGILDIR: "temiz gecis" olmadigi dogrudur ve bunu
# 0 yapip gizlemek, kanitlanamayan bir kriteri gecmis saymak olurdu.
# Dogru okuma yeri: gate_runs/g3_*/G3_report.md icindeki verdikt.
case "$G3RC" in
  0) echo "SLURM NOTU: G3 TAM GECTI (rc=0)." ;;
  3) echo "SLURM NOTU: G3 KISMI (rc=3) — kanitlanabilir kriterler GECTI, en az"
     echo "            biri KANITLANAMADI (C7/PDS verisi yok). sacct bunu FAILED"
     echo "            gosterir; kapi BASARISIZ DEGILDIR. Raporu okuyun." ;;
  1) echo "SLURM NOTU: G3 GERCEKTEN KALDI (rc=1) — kriter basarisiz." ;;
  2) echo "SLURM NOTU: G3 DEGERLENDIRILMEDI (rc=2) — CUDA yok." ;;
  *) echo "SLURM NOTU: beklenmeyen G3 cikis kodu $G3RC." ;;
esac
exit $G3RC
