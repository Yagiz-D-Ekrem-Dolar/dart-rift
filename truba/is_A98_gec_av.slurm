#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J A98_AV
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=16:00:00
#SBATCH --array=0-4
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/A98_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/A98_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# ============================================================
# PROTOKOL A98 (docs/truba/PROTOKOL-A98-GEC-EVRE-AV.md)  gorev 0-4
#   UY ile AYNI sahne/malzeme/gecis (0,2 s); yalniz GEC EVRE AV'si ve
#   merdiven degisir; gorev 4 yalniz MERMI parcacik sayisini (6400) degistirir.
#   Hepsinde AV tanisi (--av-tanisi-her 50).
#
# SABITLENMIS AGAC (KAYIT-067 dersi). AGAC ZORUNLU, temiz ve
# SABIT_COMMIT ile ayni commit.
# ZORUNLU_EXPORT: AGAC
# ============================================================
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi (sabit worktree)"; exit 2; fi
if [ ! -d "$AGAC/src/dartrift" ]; then echo "HATA: AGAC '$AGAC' bir dart-rift agaci degil"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC $AGAC_COMMIT, SABIT_COMMIT $(cat "$KOK/SABIT_COMMIT")"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_a98_$SLURM_ARRAY_TASK_ID"
# ortak_bas.sh PYTHONPATH'ten SONRA: `import dartrift` sinavi AGAC'i gorur.
source "$KOK/ortak_bas.sh"
cd "$AGAC"

i=$SLURM_ARRAY_TASK_ID
AD=(A98_k_av1 A98_k_av01 A98_o_av01 A98_k_av0 A98_k_p6400)
MERD=("kaba" "kaba" "48:2.8 24:1.4 12:0.7 6:0.35 3:0.175" "kaba" "kaba")
# Gec evre AV'si: gorev 0 VARSAYILAN (bayrak verilmez -> W2 fizigi aynen).
GAV=("" "--gec-evre-alpha-av 0.1 --gec-evre-beta-av 0.2" \
     "--gec-evre-alpha-av 0.1 --gec-evre-beta-av 0.2" \
     "--gec-evre-alpha-av 0.0 --gec-evre-beta-av 0.0" "")
# Mermi parcacik sayisi: yalniz gorev 4 (istenen 6400; SAHNE 800).
MER=("" "" "" "" "--mermi-parcacik 6400")
if [ "$i" -ge 5 ]; then echo "HATA: gorev $i tanimsiz"; exit 3; fi

TAS="$KOK/kampanya/A98_tasarim_$i.json"
echo '{"theta": [[1.15, 10.0, 0.0]]}' > "$TAS.$SLURM_JOB_ID.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin"
KIYAS="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 \
--mu-f 0.6 --yercekimi ${MER[$i]}"

echo "A98/$i  ${AD[$i]}  merdiven='${MERD[$i]}'  gec_av='${GAV[$i]}'  mermi='${MER[$i]}'  kod: $AGAC_COMMIT  agac: $AGAC"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 300 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --spacing 7.0 --kademeler ${MERD[$i]} $ORTAK $KIYAS \
    --gec-evre-t 0.2 --gec-evre-A 1.0e5 ${GAV[$i]} \
    --dondurma-k 3.0 --dondurma-her 200 --av-tanisi-her 50 \
    --impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
    --out "$KOK/kampanya/${AD[$i]}.jsonl"
rc=$?
echo "A98/$i (${AD[$i]}) rc=$rc"
exit $rc
