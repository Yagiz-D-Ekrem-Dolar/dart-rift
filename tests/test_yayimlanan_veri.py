"""`docs/sonuclar/` altındaki **yayımlanmış** CSV'ler tutarlı mı?

2026-11-04'te ölçüldü: dört yayımlanmış veri dosyasına **hiçbir sınav
gönderme yapmıyordu**.

| dosya | kim dayanıyor |
|---|---|
| `havuz_96.csv` | raporun `β` sayıları, `havuz_posterior_girdi` |
| `havuz_krater_96.csv` | KAYIT-090 |
| `havuz_krater_tarama_96.csv` | **mühürlü krater ön kaydı** (`uretim66`) |
| `havuz_posterior_girdi.csv` | posterior, tarih eşlemesi, iki ön kayıt |

Yani mühürün ve raporun dayandığı sayılar denetlenmiyordu. Bu,
`test_hera_tahmin.py`'nin aynı sınıfı: sınav **üretilmiş geçici** bir
şeyi doğruluyor, **yayımlanmış** olanı değil (A33: *sınav geçti, kusur
duruyordu*).

## Ne denetlenir — ve ne DENETLENMEZ

Denetlenen şey verinin **doğru fizik** olduğu değil; o sınanamaz ve
burada iddia edilmiyor. Denetlenen şey **tutarlılık**:

1. **Kural 8 — sayım:** dördü de `96` satır.
2. **Dizin tam:** `kuresel`/`idx` tam olarak `0..95`, tekrarsız.
3. **θ kilitli tasarımla aynı:** CSV'lerdeki `(α_b, Y₀, f)`,
   `lhs_design(DART_UZAYI_S4, 96, root_seed=20260906)` ile uyuşmalı.
   Bu, yayımlanan verinin **tasarlanan** veri olduğunu bağlar.
4. **Dosyalar arası θ uyumu.**
5. **Mühürle uyum:** `uretim66`'nın `kullanilan`/`dislanan` sayıları,
   CSV'nin `capraz_dogrulandi` dağılımından **türetilmiş** olmalı.
6. **Düzyazıyla uyum:** `docs/sonuclar/README.md`'nin andığı sayılar.

## Tolerans niçin `1e-9` değil

CSV'ler θ'yı altı haneye yuvarlayarak yazıyor. Ölçülen en büyük bağıl
fark `1,7e-5` (2026-11-04). Tolerans **ölçümden** seçildi: `1e-4`.
`1e-9` isteseydim sınav yuvarlamayı kusur sanardı.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402

SONUC = REPO / "docs" / "sonuclar"
N_NOKTA = 96
TOHUM = 20260906
#: CSV'ler theta'yi ALTI haneye yuvarliyor; olculen en buyuk bagil
#: fark 1,7e-5 (2026-11-04). Tolerans olcumden secildi.
TOL = 1e-4
#: `kuresel` ve theta tasiyan dosyalar.
THETALI = ("havuz_96.csv", "havuz_krater_96.csv",
           "havuz_krater_tarama_96.csv")
TUM = THETALI + ("havuz_posterior_girdi.csv",)


def _oku(ad: str) -> list[dict]:
    with (SONUC / ad).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tasarim() -> np.ndarray:
    return np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA, root_seed=TOHUM),
                      dtype=np.float64)


def test_BOSLUK_dort_dosya_da_var() -> None:
    """BOŞLUK KONTROLÜ (ADR-0040): dosya yoksa sınav boş doğru sınar."""
    eksik = [a for a in TUM if not (SONUC / a).is_file()]
    assert not eksik, f"yayimlanmis veri dosyasi YOK: {eksik}"


@pytest.mark.parametrize("ad", TUM)
def test_KURAL8_dosya_96_satir(ad: str) -> None:
    R = _oku(ad)
    assert len(R) == N_NOKTA, f"{ad}: {len(R)} satir, {N_NOKTA} bekleniyordu"


@pytest.mark.parametrize("ad", TUM)
def test_dizin_TAM_ve_TEKRARSIZ(ad: str) -> None:
    R = _oku(ad)
    anahtar = "kuresel" if "kuresel" in R[0] else "idx"
    idx = [int(r[anahtar]) for r in R]
    assert len(set(idx)) == len(idx), f"{ad}: tekrar eden {anahtar}"
    assert sorted(idx) == list(range(N_NOKTA)), (
        f"{ad}: dizin 0..{N_NOKTA - 1} degil")


@pytest.mark.parametrize("ad", THETALI)
def test_theta_KILITLI_tasarimla_ayni(ad: str) -> None:
    """Yayımlanan veri, **tasarlanan** veri mi?"""
    T = _tasarim()
    R = _oku(ad)
    enb, nerede = 0.0, -1
    for r in R:
        k = int(r["kuresel"])
        th = np.array([float(r["alpha_b"]), float(r["Y0"]), float(r["f"])])
        d = float(np.max(np.abs(th - T[k]) / np.maximum(np.abs(T[k]), 1e-30)))
        if d > enb:
            enb, nerede = d, k
    assert enb <= TOL, (
        f"{ad}: theta kilitli tasarimdan sapiyor -- en buyuk bagil fark "
        f"{enb:.3e} (nokta {nerede}), tolerans {TOL:.0e}")


def test_dosyalar_arasi_theta_UYUSUYOR() -> None:
    a = {int(r["kuresel"]): (float(r["alpha_b"]), float(r["Y0"]),
                             float(r["f"])) for r in _oku(THETALI[0])}
    for ad in THETALI[1:]:
        b = {int(r["kuresel"]): (float(r["alpha_b"]), float(r["Y0"]),
                                 float(r["f"])) for r in _oku(ad)}
        assert set(a) == set(b), f"{ad}: dizin kumesi farkli"
        for k in a:
            for i, (x, y) in enumerate(zip(a[k], b[k], strict=True)):
                assert abs(x - y) <= TOL * max(abs(x), 1e-30), (
                    f"{ad} nokta {k} bilesen {i}: {x} vs {y}")


def test_capraz_dagilimi_TOPLAMI_96() -> None:
    R = _oku("havuz_krater_tarama_96.csv")
    c = Counter(r["capraz_dogrulandi"] for r in R)
    assert sum(c.values()) == N_NOKTA, c
    # Siniflarin adlari da civili: yeni bir sinif sessizce eklenmesin.
    assert set(c) == {"EVET_distan_ile", "EVET_60m_ile",
                      "HAYIR_tek_tani", "olculmedi"}, sorted(c)


def test_MUHURLU_kayit_CSV_ile_tutuyor() -> None:
    """`uretim66`'nın sayıları CSV'den **türetilebilir** olmalı.

    Mühür bir iddia taşıyor: `66` nokta kullanıldı, `30` dışlandı. O
    iddia yayımlanmış veriden çıkmalı, yoksa mühür doğrulanabilir ama
    **izlenemez** olur.
    """
    kayit = json.loads(
        (REPO / "docs" / "onkayit"
         / "ONKAYIT_HERA_KRATER_uretim66.json").read_text(encoding="utf-8"))
    nk = kayit["nokta_kumesi"]
    c = Counter(r["capraz_dogrulandi"]
                for r in _oku("havuz_krater_tarama_96.csv"))
    kullanilan = c["EVET_distan_ile"] + c["EVET_60m_ile"]
    assert nk["beklenen"] == N_NOKTA
    assert nk["kullanilan"] == kullanilan, (
        f"muhur {nk['kullanilan']} diyor, CSV {kullanilan} veriyor")
    assert nk["dislanan"] == N_NOKTA - kullanilan
    # Kaydin kendi dagilim dokumu de tutmali.
    dag = nk.get("capraz_dagilim", {})
    for ad in ("EVET_distan_ile", "EVET_60m_ile"):
        if ad in dag:
            assert dag[ad] == c[ad], f"{ad}: muhur {dag[ad]}, CSV {c[ad]}"


def test_DUZYAZI_sayilari_veriyle_tutuyor() -> None:
    """`docs/sonuclar/README.md`'nin andığı sayılar CSV'den çıkmalı."""
    metin = (SONUC / "README.md").read_text(encoding="utf-8")
    c = Counter(r["capraz_dogrulandi"]
                for r in _oku("havuz_krater_tarama_96.csv"))
    kullanilan = c["EVET_distan_ile"] + c["EVET_60m_ile"]
    assert f"{kullanilan}" in metin, (
        f"README kullanilan nokta sayisini ({kullanilan}) anmiyor")
    assert f"{N_NOKTA}" in metin
