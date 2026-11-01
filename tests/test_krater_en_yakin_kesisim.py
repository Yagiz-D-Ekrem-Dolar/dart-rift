"""ADR-0064 — `tarama="en_yakin"`: yüzey, **referansa en yakın** kesişim.

`"distan"` örtüye takılır (ADR-0062 reddeder), `"icten"` cismin
**içindeki boşluğa** takılır ve hiçbir kapı onu yakalamaz — ADR-0062'nin
kapısı yalnız **yukarı** sapmayı görür. Üretimde bu, idx 87'de
`+36,49` m "derinlik" demekti (iş `6892196`: eksendeki kesişimler
`22,5` ve `107,0` m, referans yüzey `59,63` m).

`"en_yakin"` bütün aşağı kesişimleri toplar ve **aynı ışının referans
yüzeyine** en yakın olanı seçer. Yeni bir uzunluk ölçeği yoktur:
ölçüt, nokta başına ölçülmüş referans yüzeyin kendisidir.

**Bu dosyadaki bütün sayılar ölçüldü, varsayılmadı.** Beklenen değeri
önce yazıp sonra ölçmek bu projede bir kez yanlış sınav üretti
(KAYIT-089 §2).
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.crater_shape import (
    _doluluk_kesisimi,
    krater_yuzey,
)
from dartrift.setup.rubble_generator import lattice_points, particle_volume

S = 0.35
H = 2.0 * S
RHO = 2700.0 / 1.3
#: Ortusuz, bosluksuz GERCEK olcum -- uc tanimin da verdigi sayi.
GERCEK = 0.9216
#: `icten`in ic bosluga dustugunde verdigi sayi (olculdu).
ICTEN_COKUYOR = 0.0000
#: Tabanin bu kadar asagisindan taranir; ic bosluk bunun UZERINDE.
MERKEZ_Z = -4.5


@pytest.fixture(scope="module")
def levha():
    x = lattice_points(np.array([-7.0, -7.0, -5.0]),
                       np.array([7.0, 7.0, 0.0]), S, "fcc")
    x = x[x[:, 2] <= 1e-9]
    m = np.full(len(x), RHO * particle_volume(S, "fcc"))
    return x, m


def _sahne(levha, *, ortu, bosluk, D=1.0, a=2.0, r_bos=3.0):
    """`ortu=None` → ejekta kaçtı; sayı → o yükseklikte **bağlı** örtü.

    `bosluk=(alt, ust)` → eksen çevresinde cismin **içinde** boşluk.
    """
    x0, m = levha
    x = x0.copy()
    s_yan = np.hypot(x[:, 0], x[:, 1])
    z_yuzey = np.where(s_yan < a, -D * (1.0 - (s_yan / a) ** 2), 0.0)
    sil = x[:, 2] > z_yuzey + 1e-9
    v = np.zeros_like(x)
    if ortu is None:
        x[sil, 2] += 50.0
        v[sil, 2] = 5.0
    else:
        x[sil, 2] = ortu + (x[sil, 2] - x[sil, 2].min())
    tut = np.ones(len(x), bool)
    if bosluk is not None:
        alt, ust = bosluk
        tut = ~((x[:, 2] > alt) & (x[:, 2] < ust) & (s_yan < r_bos) & ~sil)
    return x[tut], x0[tut], m[tut], v[tut]


def _olc(levha, *, ortu, bosluk, tarama, **kw):
    x, x0, m, v = _sahne(levha, ortu=ortu, bosluk=bosluk)
    n = len(x)
    return krater_yuzey(x, x0, m=m, h=np.full(n, H), rho=np.full(n, RHO),
                        rho_reference=np.full(n, RHO),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        v=v, merkez=np.array([0.0, 0.0, MERKEZ_Z]),
                        tarama=tarama, **kw)


# --- varsayilan DEGISMEDI (ADR-0064 §3.5) --------------------------------

def test_VARSAYILAN_hala_distan_ve_bit_AYNI(levha):
    """`en_yakin` eklenmesi kilitli davranışı değiştirmemeli."""
    x, x0, m, v = _sahne(levha, ortu=None, bosluk=None)
    n = len(x)
    ortak = dict(m=m, h=np.full(n, H), rho=np.full(n, RHO),
                 rho_reference=np.full(n, RHO),
                 impact_direction=np.array([0.0, 0.0, -1.0]), v=v,
                 merkez=np.array([0.0, 0.0, MERKEZ_Z]))
    a = krater_yuzey(x, x0, **ortak)
    b = krater_yuzey(x, x0, tarama="distan", **ortak)
    assert a.derinlik_merkez == b.derinlik_merkez
    assert np.array_equal(a.profil, b.profil, equal_nan=True)


def test_gecersiz_yon_UC_adi_da_soyluyor():
    with pytest.raises(ValueError, match="en_yakin"):
        _doluluk_kesisimi(np.zeros((1, 3)), np.ones(1), np.ones(1),
                          taban=np.zeros(3), a=np.array([0.0, 0.0, 1.0]),
                          z_ust=1.0, z_alt=0.0, adim=0.1, esik=0.5,
                          yon="uydurma")


def test_en_yakin_z_hedef_YOKSA_nan():
    """`z_hedef` olmadan "en yakın" tanımsız -- sessiz sayı yerine `nan`."""
    d = _doluluk_kesisimi(np.zeros((1, 3)), np.ones(1), np.ones(1),
                          taban=np.zeros(3), a=np.array([0.0, 0.0, 1.0]),
                          z_ust=1.0, z_alt=0.0, adim=0.1, esik=0.5,
                          yon="en_yakin", z_hedef=None)
    assert np.isnan(d)


# --- OLCULEN davranis ----------------------------------------------------

def test_ortusuz_bosluksuz_UC_TANIM_DA_AYNI(levha):
    """Kusursuz sahnede üç tanım da aynı sayıyı vermeli."""
    d = {t: _olc(levha, ortu=None, bosluk=None, tarama=t).derinlik_merkez
         for t in ("distan", "icten", "en_yakin")}
    for t, v in d.items():
        assert v == pytest.approx(GERCEK, abs=5e-4), f"{t}: {v}"


def test_ic_bosluk_ICTENi_COKERTIYOR_en_yakin_KURTARIYOR(levha):
    """ADR-0064 §3.2'nin ölçümü: `icten` iç boşluğa düşüyor."""
    ic = _olc(levha, ortu=None, bosluk=(-3.5, -3.0),
              tarama="icten").derinlik_merkez
    ey = _olc(levha, ortu=None, bosluk=(-3.5, -3.0),
              tarama="en_yakin").derinlik_merkez
    assert ic == pytest.approx(ICTEN_COKUYOR, abs=5e-4)
    assert ey == pytest.approx(GERCEK, abs=5e-4)


def test_URETIM_DURUMU_ortu_VE_ic_bosluk_birlikte(levha):
    """İdx 6 ve 87'nin durumu: krater **örtülü** ve içinde **boşluk**.

    Üç tanımın yalnız biri doğru sayıyı veriyor.
    """
    with pytest.raises(ValueError, match="ORTULU KRATER"):
        _olc(levha, ortu=30.0, bosluk=(-3.5, -3.0), tarama="distan")
    ic = _olc(levha, ortu=30.0, bosluk=(-3.5, -3.0),
              tarama="icten").derinlik_merkez
    ey = _olc(levha, ortu=30.0, bosluk=(-3.5, -3.0),
              tarama="en_yakin").derinlik_merkez
    assert ic == pytest.approx(ICTEN_COKUYOR, abs=5e-4), (
        "`icten` ortulu+boslukta cokuyor; bu kusurun kaydi")
    assert ey == pytest.approx(GERCEK, abs=5e-4), (
        "`en_yakin` ikisini birlikte asmali -- ADR-0064'un tek iddiasi")


@pytest.mark.parametrize("ortu", [12.0, 30.0])
@pytest.mark.parametrize("bosluk", [(-4.0, -3.0), (-3.5, -3.0)])
def test_en_yakin_ORTU_ve_BOSLUK_nereye_konursa_AYNI(levha, ortu, bosluk):
    """`en_yakin` bir ayar değil **tanım**: konumdan bağımsız olmalı."""
    d = _olc(levha, ortu=ortu, bosluk=bosluk,
             tarama="en_yakin").derinlik_merkez
    assert d == pytest.approx(GERCEK, abs=5e-4)


def test_GERI_ALMA_KOSULU_tek_kesisimde_en_yakin_distan_ile_AYNI(levha):
    """ADR-0064 §5: boşluk yoksa kesişim tektir, iki tanım **aynı**.

    Üretim havuzunda çapraz doğrulanan `66` noktanın `%95,5`'inde
    kesişim tekti (iş `6892196`); yani bu eşitlik orada da geçerli
    olmalı. Bozulursa kip geri alınır.
    """
    a = _olc(levha, ortu=None, bosluk=None, tarama="distan")
    b = _olc(levha, ortu=None, bosluk=None, tarama="en_yakin")
    assert b.derinlik_merkez == pytest.approx(a.derinlik_merkez, rel=1e-9)


def test_tani_tarama_adini_tasiyor(levha):
    d = _olc(levha, ortu=None, bosluk=None, tarama="en_yakin")
    assert d.tani["tarama"] == "en_yakin"
