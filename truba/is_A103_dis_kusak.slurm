#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J A103
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=16:00:00
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/A103_%j.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/A103_%j.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0


# ============================================================
# PROTOKOL A103 (docs/truba/PROTOKOL-A103-DIS-KUSAK.md)  tek is
#   UY/A98 ile AYNI sahne, malzeme, gecis (0,2 s), AV (1, 2), kod (A98
#   agaci, SABIT_COMMIT); YALNIZ merdiven: 12-48 m kusagi 2x ince, ic
#   12 m kaba ile ayni. Merdivende ayni aralikli iki ardisik kademe
#   yasak (lam iceri dogru kesin artmali) -> "24:1.4" 6-24 m'yi kapsar.
#   AV tanisi A98 gibi (R0: fizige dokunmuyor).
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
export WARP_CACHE_PATH="$KOK/.warp_cache_a103"
# ortak_bas.sh PYTHONPATH'ten SONRA: `import dartrift` sinavi AGAC'i gorur.
source "$KOK/ortak_bas.sh"
cd "$AGAC"

AD=A103_dis2
MERD="48:2.8 24:1.4 6:0.7 3:0.35"
TAS="$KOK/kampanya/A103_tasarim.json"
echo '{"theta": [[1.15, 10.0, 0.0]]}' > "$TAS.$SLURM_JOB_ID.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin"
KIYAS="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 \
--mu-f 0.6 --yercekimi"

echo "A103  $AD  merdiven='$MERD'  kod: $AGAC_COMMIT  agac: $AGAC"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 300 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --spacing 7.0 --kademeler $MERD $ORTAK $KIYAS \
    --gec-evre-t 0.2 --gec-evre-A 1.0e5 \
    --dondurma-k 3.0 --dondurma-her 200 --av-tanisi-her 50 \
    --impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
    --out "$KOK/kampanya/$AD.jsonl"
rc=$?
echo "A103 ($AD) rc=$rc"
exit $rc
