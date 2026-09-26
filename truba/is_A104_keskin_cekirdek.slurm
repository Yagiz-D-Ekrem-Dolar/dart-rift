#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J A104
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=16:00:00
#SBATCH --array=0-1
#SBATCH --exclude=kolyoz19,kolyoz9
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/A104_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/A104_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0


# ============================================================
# PROTOKOL A104 (docs/truba/PROTOKOL-A104-KESKIN-CEKIRDEK.md)  gorev 0-1
#   UY/A98/A103 ile AYNI sahne, malzeme, gecis (0,2 s), AV (1, 2); YALNIZ
#   h/s = 1,5 (keskin cekirdek). Kod: agac_a104 = SABIT_COMMIT b738992 +
#   YALNIZ h_orani (yan dal a104-taban) -> UY fizigi, tek eksen.
#   gorev 0: kaba merdiven (A104_k15), gorev 1: orta merdiven (A104_o15).
#
# SABITLENMIS AGAC. AGAC ve AGAC_COMMIT ZORUNLU; agac temiz ve beklenen
# commit'te olmali. SABIT_COMMIT'e DOKUNULMAZ (ortak_bas ana agaci denetler).
# ZORUNLU_EXPORT: AGAC AGAC_COMMIT
# ============================================================
if [ -z "${AGAC:-}" ] || [ -z "${AGAC_COMMIT:-}" ]; then
  echo "HATA: AGAC ve AGAC_COMMIT verilmeli"; exit 2; fi
if [ ! -d "$AGAC/src/dartrift" ]; then echo "HATA: AGAC '$AGAC' bir dart-rift agaci degil"; exit 2; fi
BULUNAN=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$BULUNAN" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC $BULUNAN, beklenen $AGAC_COMMIT"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_a104_$SLURM_ARRAY_TASK_ID"
# ortak_bas.sh PYTHONPATH'ten SONRA: `import dartrift` sinavi AGAC'i gorur.
source "$KOK/ortak_bas.sh"
cd "$AGAC"

i=$SLURM_ARRAY_TASK_ID
AD=(A104_k15 A104_o15)
MERD=("kaba" "48:2.8 24:1.4 12:0.7 6:0.35 3:0.175")
if [ "$i" -ge 2 ]; then echo "HATA: gorev $i tanimsiz"; exit 3; fi

TAS="$KOK/kampanya/A104_tasarim_$i.json"
echo '{"theta": [[1.15, 10.0, 0.0]]}' > "$TAS.$SLURM_JOB_ID.tmp" \
  && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"

ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin"
KIYAS="--model-sinifi M0 --hedef-yaricapi 75.0 --yigin-yogunlugu 1600.0 \
--mermi-kutlesi 500.0 --mermi-hizi 6000.0 --mermi-yogunlugu 1000.0 \
--mu-f 0.6 --yercekimi"

echo "A104/$i  ${AD[$i]}  merdiven='${MERD[$i]}'  h/s=1.5  kod: $BULUNAN  agac: $AGAC"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 300 --root-seed 20260906 --sahne-tohum 20260906 \
    --tasarim-dosyasi "$TAS" --spacing 7.0 --kademeler ${MERD[$i]} $ORTAK $KIYAS \
    --gec-evre-t 0.2 --gec-evre-A 1.0e5 --h-orani 1.5 \
    --dondurma-k 3.0 --dondurma-her 200 --av-tanisi-her 50 \
    --impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
    --out "$KOK/kampanya/${AD[$i]}.jsonl"
rc=$?
echo "A104/$i (${AD[$i]}) rc=$rc"
exit $rc
