"""`asama2_sahnesi` — ADR-0043'ün 3. adımının birleştirmesi.

Sınanan asıl şey **çifte sayım**: aşama-1'in maddesi ile aşama-2'nin
aynı bölgedeki parçacıkları ikisi birden kalırsa o bölgenin kütlesi iki
katına çıkar ve ADR-0030 delinir.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.setup.two_stage import asama2_sahnesi


class _SahteA2:
    """Aşama-2 sahnesi yerine geçen asgari nesne.

    **FCC kafes**, rastgele bulut değil. İlk sürüm `±40 m` kutusuna
    `400` rastgele nokta koyuyordu ve `r = 3 m` içine düşen beklenen
    sayı `0,09`'du — yani çakışma testi *"hiçbir şey atılmadı"* diye
    düşüyordu. Kusur testte değil **fikstürdeydi**: gerçek aşama-2 bir
    kafes ve `r = 3 m` içinde (ölçülmüş) **2** parçacığı var.
    """

    def __init__(self, r=40.0, s2=3.5):
        from dartrift.setup.rubble_generator import lattice_points
        self.x = lattice_points(np.full(3, -r), np.full(3, r), s2, "fcc")
        n = len(self.x)
        self.v = np.zeros((n, 3))
        self.m = np.full(n, 5.0)
        self.alpha0 = np.full(n, 1.6)
        self.Y0 = np.full(n, 1.0e5)
        self.is_boulder = np.zeros(n, bool)
        self.is_impactor = np.zeros(n, bool)
        self.h = np.full(n, 2.0 * s2)
        self.spacing_fine = s2
        self.impact_point = np.zeros(3)


def _a1(n=900, r=3.0, seed=7):
    """Aşama-1'in `t₁` anındaki ince bulutu (genişlemiş)."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, r, size=(n, 3))
    durum = {"x": x, "v": rng.normal(0.0, 50.0, size=(n, 3)),
             "u": rng.uniform(1e3, 1e5, n)}
    return (durum, np.ones(n, bool), np.full(n, 0.02),
            np.full(n, 1.5), np.full(n, 2.0e5), np.zeros(n, bool))


def _kur(r_ince_a1=3.0, **kw):
    d, ince, m, a0, y0, bl = _a1(**kw)
    return asama2_sahnesi(d, ince, m, a0, y0, bl, _SahteA2(), r_ince_a1)


# ------------------------------------------------------- cifte sayim

def test_asama2nin_CAKISAN_parcaciklari_ATILIYOR():
    """En sinsi hata: aynı bölgenin kütlesi **iki kez** sayılır."""
    s = _kur(r_ince_a1=3.0)
    t = s.diagnostics
    assert t["n_asama2_atilan"] > 0, "hicbir sey atilmadi — cifte sayim var"
    a2 = _SahteA2()
    d = np.linalg.norm(a2.x, axis=1)
    assert t["n_asama2_atilan"] == int((d < 3.0).sum())
    assert t["n_asama2_tutulan"] == int((d >= 3.0).sum())
    assert t["n_toplam"] == t["n_aktarilan"] + t["n_asama2_tutulan"]


def test_aktarim_KUTLE_kaybetmiyor():
    t = _kur().diagnostics
    assert t["aktarim_kutle_hatasi"] < 1e-14, t["aktarim_kutle_hatasi"]
    assert t["kutle_hata"] < 1e-14
    assert t["momentum_hata"] < 1e-12
    assert t["enerji_hata"] < 1e-12


def test_toplam_kutle_ELLE_hesapla_ile_ayni():
    s = _kur()
    a2 = _SahteA2()
    d = np.linalg.norm(a2.x, axis=1)
    bek = 900 * 0.02 + float(a2.m[d >= 3.0].sum())
    assert float(s.m.sum()) == pytest.approx(bek, rel=1e-14)


# --------------------------------------------------------- yapi

def test_kaynak_etiketi_iki_grubu_ayiriyor():
    s = _kur()
    assert set(np.unique(s.kaynak)) == {0, 1}
    nk = s.diagnostics["n_aktarilan"]
    assert int((s.kaynak == 0).sum()) == nk
    assert np.all(s.h[:nk] == pytest.approx(2.0 * 3.5))


def test_butun_diziler_AYNI_uzunlukta():
    s = _kur()
    n = s.n
    for ad in ("x", "v", "m", "e", "h", "alpha0", "Y0", "is_boulder",
               "is_impactor", "kaynak"):
        assert len(getattr(s, ad)) == n, ad
    assert s.x.shape == (n, 3) and s.v.shape == (n, 3)


def test_komsu_tanisi_raporlaniyor():
    """Aşama-2 bunları SPH ile ilerletecek; komşu sayısı görünmeli."""
    t = _kur().diagnostics
    assert "komsu" in t and t["komsu"]["n"] == t["n_aktarilan"]
    assert t["komsu"]["komsu_medyan"] >= 0.0


def test_atama_mesafesi_bir_hucrenin_altinda():
    """Lagrange'cı site üretiminin **yapısal** güvencesi."""
    t = _kur().diagnostics
    assert t["atama_mesafe_max"] / t["s_asama2"] < 1.0


# ---------------------------------------------------------- korumalar

def test_patlamis_asama1_REDDEDILIYOR():
    d, ince, m, a0, y0, bl = _a1()
    d["v"][5] = np.nan
    with pytest.raises(ValueError, match="sonlu değil"):
        asama2_sahnesi(d, ince, m, a0, y0, bl, _SahteA2(), 3.0)


def test_ic_enerji_YOKSA_acik_hata():
    d, ince, m, a0, y0, bl = _a1()
    del d["u"]
    with pytest.raises(KeyError, match="özgül iç enerji"):
        asama2_sahnesi(d, ince, m, a0, y0, bl, _SahteA2(), 3.0)


def test_ince_parcacik_yoksa_reddediliyor():
    d, ince, m, a0, y0, bl = _a1()
    with pytest.raises(ValueError, match="ince parçacık yok"):
        asama2_sahnesi(d, np.zeros(len(m), bool), m, a0, y0, bl,
                       _SahteA2(), 3.0)


def test_yaricap_sahneden_BUYUKSE_reddediliyor():
    """Her şeyi atmak sessizce boş bir sahne üretmemeli."""
    d, ince, m, a0, y0, bl = _a1()
    with pytest.raises(ValueError, match="tamamı atılıyor"):
        asama2_sahnesi(d, ince, m, a0, y0, bl, _SahteA2(), 1.0e6)
