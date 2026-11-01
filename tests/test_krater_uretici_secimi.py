"""ADR-0065 — `krater_derinlik`'in üreticisi **yan yana** seçilir.

A19 (2026-08-21'den beri açık) şunu ölçmüştü: krater çıkarıcısı
**yokken var, varken yok** diyor. Çaresi (`krater_yuzey`) bir yıl önce
yazıldı, sınandı — ve **üretime bağlanmadı** (A116'nın deseni:
*"yazılmış ama bağlanmamış modül"*). `forward.py` hâlâ
`crater_profile`'ı çağırıp sonucu `y[1] = krater_derinlik` yapıyordu.

Bu dosya bağlamanın **kendisini** sınar:

1. Varsayılan `"profil"` ve **bit-aynı** (ADR-0065 §5 geri alma koşulu).
2. Geçersiz üretici adı **reddedilir**.
3. `"yuzey"`, durumda `h` yoksa **neyin eksik olduğunu söyleyerek**
   reddeder — sessiz `KeyError` değil.
4. Hangi üreticinin kullanıldığı **kütüğe** yazılır (ADR-0065 §3.2).
   A19'un asıl zararı sayının yanlış olması değil, hangi çıkarıcıdan
   geldiğinin **görünmemesi**ydi; KAYIT-088 tam bu yüzden iki ayrı
   çıkarıcıyı karıştırdı.

A19'un iki senaryosunun `krater_yuzey` ile **geçtiği**
`test_krater_bos_sinav.py`'nin sonunda, `xfail`lerin yanında sınanıyor.
"""
from __future__ import annotations

import numpy as np
import pytest

import dartrift.inference.forward as F


def _durum(n: int = 400, *, h: bool = False) -> dict:
    rng = np.random.default_rng(7)
    yon = rng.normal(size=(n, 3))
    yon /= np.linalg.norm(yon, axis=1, keepdims=True)
    x0 = yon * 80.0
    st = {"x": x0 + rng.normal(scale=0.1, size=(n, 3)),
          "v": rng.normal(scale=0.01, size=(n, 3)),
          "m": np.full(n, 1.0e7), "rho": np.full(n, 2300.0)}
    if h:
        st["h"] = np.full(n, 6.0)
    return st, x0


def _cikar(st, x0, **kw):
    n = len(st["x"])
    return F.gozlenebilirleri_cikar(
        st, impactor_momentum=np.array([0.0, 0.0, 3.56e6]),
        target_mass=4.3e9, target_radius=80.0,
        is_impactor=np.zeros(n, dtype=bool),
        impact_direction=np.array([0.0, 0.0, 1.0]),
        x_reference=x0, **kw)


def test_VARSAYILAN_profil_ve_acikca_profil_BIT_AYNI() -> None:
    """ADR-0065 §5: varsayılan yol **bit-aynı** kalmalı."""
    st, x0 = _durum()
    a = _cikar(st, x0, istege_bagli=("krater_derinlik",))
    b = _cikar(st, x0, krater_uretici="profil",
               istege_bagli=("krater_derinlik",))
    assert np.array_equal(a, b, equal_nan=True)


def test_gecersiz_uretici_IKI_adi_da_soyluyor() -> None:
    st, x0 = _durum()
    with pytest.raises(ValueError, match="profil"):
        _cikar(st, x0, krater_uretici="uydurma",
               istege_bagli=("krater_derinlik",))
    with pytest.raises(ValueError, match="yuzey"):
        _cikar(st, x0, krater_uretici="uydurma",
               istege_bagli=("krater_derinlik",))


def test_yuzey_h_YOKSA_neyin_eksik_oldugunu_SOYLUYOR() -> None:
    """Sessiz `KeyError` yerine gerekçeli red (sessiz varsayılan yok)."""
    st, x0 = _durum(h=False)
    with pytest.raises(ValueError, match="yumusatma boyu"):
        _cikar(st, x0, krater_uretici="yuzey",
               istege_bagli=("krater_derinlik",))
    with pytest.raises(ValueError, match=r"\['h'\]"):
        _cikar(st, x0, krater_uretici="yuzey",
               istege_bagli=("krater_derinlik",))


def test_yuzey_h_VARSA_cagriliyor() -> None:
    """`h` verilince `krater_yuzey` yolu gerçekten koşuyor.

    Bu sentetik sahnede sayının **değeri** sınanmıyor (tek tabakalı
    rastgele kabuk gerçek bir krater değil); sınanan şey yolun
    bağlanmış olması: `profil` ile **aynı sayıyı** vermemeli, yoksa
    iki çıkarıcı ayırt edilemez.
    """
    st, x0 = _durum(h=True)
    p = _cikar(st, x0, krater_uretici="profil",
               istege_bagli=("krater_derinlik",))
    y = _cikar(st, x0, krater_uretici="yuzey",
               istege_bagli=("krater_derinlik",))
    # `beta` ve ejekta kesri AYNI kalmali -- uretici yalniz y[1]'i etkiler.
    assert p[0] == pytest.approx(y[0], rel=1e-12)
    assert p[2] == pytest.approx(y[2], rel=1e-12)
    ad = F.GOZLENEBILIRLER.index("krater_derinlik")
    assert not (np.isfinite(p[ad]) and np.isfinite(y[ad])
                and p[ad] == y[ad]), (
        "iki cikarici AYNI sayiyi verdi -- yol baglanmamis olabilir")


def test_KUTUGE_hangi_uretici_kullanildigi_yaziliyor() -> None:
    """ADR-0065 §3.2: varsayılan artık **sessiz değil**."""
    st, x0 = _durum()
    F.KRATER_URETICI_KUTUGU.clear()
    _cikar(st, x0, istege_bagli=("krater_derinlik",))
    assert len(F.KRATER_URETICI_KUTUGU) == 1
    satir = F.KRATER_URETICI_KUTUGU[0]
    assert "krater_uretici=profil" in satir
    assert "A19" in satir, "varsayilan yolun A19 uyarisi kutukte olmali"
    F.KRATER_URETICI_KUTUGU.clear()


def test_A114_kanali_KIRLETILMEDI() -> None:
    """Üretici kütüğü, A114'ün `nan` sayacından **ayrı** olmalı.

    `test_a114_istege_bagli_gozlemli` o kanalda **tam bir** girdi
    bekliyor; üreticiyi oraya yazmak onu kırardı.

    Dikkat: A114 kanalı bu sahnede **boş değil** ve olmamalı —
    `crater_profile` burada haklı olarak düşüyor (*"hiçbir kutuda 5
    parçacık yok"*) ve o `nan` gerekçesi kanalın **asıl işi**. Sınanan
    şey kanalın boşluğu değil, **üretici satırının oraya sızmaması**.
    """
    st, x0 = _durum()
    F.A114_UYARILARI.clear()
    F.KRATER_URETICI_KUTUGU.clear()
    _cikar(st, x0, istege_bagli=("krater_derinlik",))
    sizan = [u for u in F.A114_UYARILARI if "krater_uretici" in u]
    assert not sizan, f"uretici satiri A114 kanalina sizdi: {sizan}"
    assert len(F.KRATER_URETICI_KUTUGU) == 1
    F.A114_UYARILARI.clear()
    F.KRATER_URETICI_KUTUGU.clear()
