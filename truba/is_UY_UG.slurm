#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J UY_UG
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-3
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/UYUG_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/UYUG_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# ============================================================
# PROTOKOL UY (docs/truba/PROTOKOL-UY-YAKIN-ALAN.md)  gorev 0-1
# PROTOKOL UG (docs/truba/PROTOKOL-UG-GECIS-ANI.md)   gorev 2-3
#   W2_Y10 ile AYNI sahne/malzeme; UY merdiveni, UG gecis anini degistirir.
#
# SABITLENMIS AGAC (KAYIT-067 dersi): kod tembel ice aktariliyor; kosu
# surerken $KOK/dart-rift guncellenirse kosunun sonundaki ice aktarimlar
# YENI kodu okuyabilir. Bu is kendi git worktree'sinden kosar; AGAC
# ZORUNLU ve SABIT_COMMIT ile ayni commit'te, temiz olmali.
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
export WARP_CACHE_PATH="$KOK/.warp_cache_uyug$SLURM_ARRAY_TASK_ID"
# ortak_bas.sh PYTHONPATH'ten SONRA: `import dartrift` sinavi AGAC'i gorur.
source "$KOK/ortak_bas.sh"
cd "$AGAC"

i=$SLURM_ARRAY_TASK_ID
AD=(UY_orta UY_ic UG_Y10_g2p5 UG_Y10_g5p0)
TEND=(300 300 600 600)
GEC=(0.2 0.2 2.5 5.0)
MERD=("48:2.8 24:1.4 12:0.7 6:0.35 3:0.175" \
      "48:5.6 24:2.8 12:0.7 6:0.35 3:0.175" \
      "kaba" "kaba")
if [ "$i" -ge 4 ]; then echo "HATA: gorev $i tanimsiz"; exit 3; fi

TAS="$KOK/kampanya/UYUG_tasarim_$i.json"
echo '{"theta": [[1.15, 10.0, 0.0]]}' > "$TAS.$SLURM_JOB_ID.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin"
KIYAS="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 \
--mu-f 0.6 --yercekimi"

echo "UYUG/$i  ${AD[$i]}  merdiven='${MERD[$i]}'  t_gecis=${GEC[$i]}  t_end=${TEND[$i]}  kod: $AGAC_COMMIT  agac: $AGAC"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end "${TEND[$i]}" --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --spacing 7.0 --kademeler ${MERD[$i]} $ORTAK $KIYAS \
    --gec-evre-t "${GEC[$i]}" --gec-evre-A 1.0e5 \
    --dondurma-k 3.0 --dondurma-her 200 \
    --impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
    --out "$KOK/kampanya/${AD[$i]}.jsonl"
rc=$?
echo "UYUG/$i (${AD[$i]}) rc=$rc"
exit $rc
