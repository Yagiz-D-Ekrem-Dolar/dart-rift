#!/bin/bash
#SBATCH -A egitimg16
#SBATCH -p kolyoz-cuda
#SBATCH -J HAVUZ_INCE
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#   `--time` 2 gun DEGIL 3 gun (KAYIT-085): ilk kosumda 48 saatle
#   gonderildi ve nokta 20 ile 44 duvara carpti -- ikisi de ~58 saat
#   istiyordu. Bolumun kendi siniri `3-00:00:00` (sinfo ile dogrulandi),
#   yani 48 bizim kendi sectigimiz gereksiz bir kisittı.
#SBATCH --time=3-00:00:00
#SBATCH --array=0-11%4
#   kolyoz11 (KAYIT-085): nokta 78, 87, 92 orada "nvidia-smi GPU
#   gormuyor" ile dustu. kolyoz13 ayni aileden, README'de kayitli.
#SBATCH --exclude=kolyoz19,kolyoz9,kolyoz11,kolyoz13
#SBATCH -o /arf/scratch/egitimg16u1/driftclaude/ciktilar/HAVUZ_INCE_%A_%a.out
#SBATCH -e /arf/scratch/egitimg16u1/driftclaude/ciktilar/HAVUZ_INCE_%A_%a.err

set -uo pipefail
KOK=/arf/scratch/egitimg16u1/driftclaude
mkdir -p "$KOK/ciktilar" "$KOK/kampanya"
module load apps/truba-ai/gpu-2024.0

# ======================================================================
# IC ICE INCE TASARIM (ADR-0059 S3.2) -- havuz okunmadan once yazildi
# ======================================================================
# NE ICIN: `96` kaba noktanin `12`'si `3,5 m`'de TEKRAR kosulur. Amac
# `3,5 m`'de yakinsamak DEGIL; `7 m -> 3,5 m` FARKINI olcmektir:
#
#     y_orta(x) = rho * f_kaba(x) + delta(x)
#
# `delta` bu 12 noktadan ogrenilip vekil uzerinden 96 noktanin hepsine
# tasinir (Kennedy-O'Hagan AR(1)). Ic ice olmasi SART: `delta`nin
# ozyinelemeli kestirimi ancak ince kume kabanin ALT KUMESI ise tamdir.
#
# NEDEN GEREKLI: PROTOKOL-M/U0, kaba -> orta gecisinde `beta` icin
# `-%13`'luk bir KAYMA olctu. `sigma` bunu varyans olarak tasir; varyans
# bir kaymayi soguramaz. Ince kosu atlanirsa Kapi 2 degerlendirilemez ve
# bilinen bir yanlilik gurultu gibi gosterilmis olur (ADR-0059 gerekcesi).
#
# DEGISEN TEK SEY COZUNURLUK: asagidaki `ORTAK` satiri `is_HAVUZ.slurm`
# ile BIREBIR AYNIDIR; yalniz `--spacing` ve `--kademeler` farklidir.
# Baska bir sey degisirse `delta` cozunurluk degil, karisim olcer.
#
#   kaba  : --spacing 7.0  --kademeler kaba   (48:5.6 24:2.8 12:1.4 6:0.7 3:0.35)
#   orta  : --spacing 3.5  --kademeler orta   (48:2.8 24:1.4 12:0.7 6:0.35 3:0.175)
#
# SURE: olculen kaba ~5,0 GPU-sa/nokta; kaba->orta maliyet orani ~3,5
# (PROTOKOL-UY2) -> ~17,6 GPU-sa/nokta. Is siniri 48 saat birakildi:
# 24 saatte pay ~6 saat kalirdi, yeni is 3 gune kadar izinli.
# Gorev basina TEK nokta (kabada 4'tu) -- orta nokta 24 saate sigmaz.
#
# ZORUNLU_EXPORT: AGAC
if [ -z "${AGAC:-}" ]; then echo "HATA: AGAC verilmedi"; exit 2; fi
AGAC_COMMIT=$(git -C "$AGAC" rev-parse HEAD)
if [ -n "$(git -C "$AGAC" status --porcelain --untracked-files=no)" ]; then
  echo "HATA: AGAC kirli"; exit 92; fi
if [ "$(tr -d '[:space:]' < "$KOK/SABIT_COMMIT")" != "$AGAC_COMMIT" ]; then
  echo "HATA: AGAC/SABIT_COMMIT uyusmuyor"; exit 92; fi
export PYTHONPATH="$KOK/pylib:$AGAC/src"
export WARP_CACHE_PATH="$KOK/.warp_cache_ince$SLURM_ARRAY_TASK_ID"
source "$KOK/ortak_bas.sh"
cd "$AGAC"

N_HAVUZ=96
AD=HAVUZ_INCE_g1p0

# --- 12 indis: ADR-0059 S3.2'nin kilitli secimi ----------------------
# Tercih edilen yol indisleri KODA hesaplatmakti (A116 deseni: kod zaten
# uretiyorsa betige sabit yazma). AMA bu calisma agaci SABIT_COMMIT
# d96c4ee6'ya sabitli ve `ic_ice_tasarim` modulu o commit'ten SONRA
# yazildi -- TRUBA'da yok. Agaci ilerletmek, bekleyen KABA gorevlerin
# (18-23) SABIT_COMMIT denetiminden dusmesine yol acardi (exit 92);
# havuz koserken agac DEGISTIRILMEZ.
#
# Bu yuzden liste sabit. Kaynagi:
#   tests/test_ic_ice_tasarim.py::test_KILITLI_12_nokta_kaydi
# Guvenligi ise asagidaki KANARYA saglar: tasarimin kaymadigini
# `design.py` ile dogrular (o modul bu commit'te VAR). Indis listesi
# dogru ama tasarim kaymis olsaydi, yanlis theta kosulurdu; kanarya tam
# bunu yakalar.
INDISLER=(11 20 33 44 45 57 58 62 74 78 87 92)
BEKLENEN_AB="1.2978 1.0081 1.2723 1.0175 1.1422 1.1359 1.1760 1.0045 1.2846 1.0331 1.0126 1.2810"

KANARYA=$(python - <<'PY'
from dartrift.inference.design import DART_UZAYI_S4, lhs_design
d = lhs_design(DART_UZAYI_S4, 96, root_seed=20260906)
idx = [11, 20, 33, 44, 45, 57, 58, 62, 74, 78, 87, 92]
assert len(d) == 96, f"tasarim 96 nokta degil: {len(d)}"
print(" ".join(f"{d[i][0]:.4f}" for i in idx))
PY
)
if [ "$KANARYA" != "$BEKLENEN_AB" ]; then
  echo "HATA: tasarim kaymis -- 12 noktanin alpha_b degerleri tutmuyor"
  echo "  beklenen: $BEKLENEN_AB"
  echo "  bulunan : $KANARYA"
  exit 93
fi
if [ "${#INDISLER[@]}" -ne 12 ]; then
  echo "HATA: 12 indis bekleniyordu, ${#INDISLER[@]} geldi"; exit 93; fi
IDX=${INDISLER[$SLURM_ARRAY_TASK_ID]}

# `--dilim i/n` ADIMLI secer (arange(n) % n_s == i_s), yani `i/96` tam
# olarak `i`. noktayi kosar. Kaba havuz `i/24` kullanir: 4 nokta/gorev.
ORTAK="--akma-kipi ara --matris-cekme-yok --malzeme-kaynagi geometri \
--mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh \
--dayanim-kesme --yogunluk-tabani --onsel-disi-izin --yercekimi \
--gec-evre-t 1.0 --gec-evre-A 1.0e5 --dondurma-k 3.0 --dondurma-her 200 \
--impuls-log --beta-km --azami-adim 40000000 --adim-bildir 20000 \
--model-sinifi M1 --mermi-kutlesi 579.4 --mermi-hizi 6144.9 \
--mermi-yogunlugu 1000.0 --carpma-acisi 17.0 --mu-f 0.6 --mermi-uc-kure \
--hedef-yari-eksenler 88.5 87.0 58.0 --yigin-yogunlugu 2306.1 \
--spacing 3.5 --kademeler orta \
--uzay-s4 --n-lhs $N_HAVUZ --dilim $IDX/$N_HAVUZ \
--blok-rmin 14.0 --blok-rmax 56.0 \
--istege-bagli-gozlemli krater_derinlik"

echo "HAVUZ_INCE gorev $SLURM_ARRAY_TASK_ID -> nokta $IDX/$N_HAVUZ  kod: $AGAC_COMMIT"
# shellcheck disable=SC2086
python scripts/faz5_ensemble_merdiven.py --device cuda:0 \
    --t-end 600 --root-seed 20260906 --sahne-tohum 20260906 \
    $ORTAK \
    --out "$KOK/kampanya/${AD}.jsonl"
rc=$?
echo "HAVUZ_INCE nokta $IDX rc=$rc"
exit $rc
