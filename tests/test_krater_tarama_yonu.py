"""ADR-0063 — `tarama="icten"`: yüzey **içten dışa** bulunur.

`"distan"` (varsayılan) `phi = esik` eş-yüzeyini dıştan içe tarar ve
eksende duran, kaçmamış ejektanın tepesini yüzey sanar (KAYIT-089:
`d_merkez = -(örtü + 0,913)` m). `"icten"` ise `taban`'dan — kütle
merkezi düzleminden, yani cismin **içinden** — dışa çıkar ve `phi`'nin
eşiğin altına ilk düştüğü yeri alır. Üstteki boşluk ve ondan sonraki
ayrı yığın **yapısal olarak** ıskalanır.

Bu dosyanın bağladığı iddia şudur: `"icten"` bir ayar değil, bir
**tanım**. Örtü nereye konursa konsun ölçüm değişmemeli ve örtüsüz
gerçeğe eşit olmalı.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.crater_shape import krater_yuzey
from dartrift.setup.rubble_generator import lattice_points, particle_volume

S = 0.35
H = 2.0 * S
RHO = 2700.0 / 1.3
#: Ejekta kacmis haldeki GERCEK olcum (ikisi de ayni sayiyi verir).
GERCEK = 0.9216


@pytest.fixture(scope="module")
def levha():
    x = lattice_points(np.array([-7.0, -7.0, -5.0]),
                       np.array([7.0, 7.0, 0.0]), S, "fcc")
    x = x[x[:, 2] <= 1e-9]
    m = np.full(len(x), RHO * particle_volume(S, "fcc"))
    return x, m


def _sahne(levha, *, yukseklik, D=1.0, a=2.0):
    """`yukseklik=None` → ejekta kaçtı; sayı → o yükseklikte bağlı örtü."""
    x0, m = levha
    x = x0.copy()
    s_yan = np.hypot(x[:, 0], x[:, 1])
    z_yuzey = np.where(s_yan < a, -D * (1.0 - (s_yan / a) ** 2), 0.0)
    sil = x[:, 2] > z_yuzey + 1e-9
    v = np.zeros_like(x)
    if yukseklik is None:
        x[sil, 2] += 50.0
        v[sil, 2] = 5.0
    else:
        x[sil, 2] = yukseklik + (x[sil, 2] - x[sil, 2].min())
    return x, x0, m, v


def _olc(levha, *, yukseklik, tarama, **kw):
    x, x0, m, v = _sahne(levha, yukseklik=yukseklik)
    n = len(x)
    return krater_yuzey(x, x0, m=m, h=np.full(n, H), rho=np.full(n, RHO),
                        rho_reference=np.full(n, RHO),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        v=v, merkez=np.array([0.0, 0.0, -2.5]),
                        tarama=tarama, **kw)


# --- varsayilan DEGISMEDI ------------------------------------------------

def test_VARSAYILAN_distan_ve_acikca_distan_AYNI(levha):
    """`tarama` eklenmesi kilitli davranışı değiştirmemeli."""
    x, x0, m, v = _sahne(levha, yukseklik=None)
    n = len(x)
    ortak = dict(m=m, h=np.full(n, H), rho=np.full(n, RHO),
                 rho_reference=np.full(n, RHO),
                 impact_direction=np.array([0.0, 0.0, -1.0]), v=v,
                 merkez=np.array([0.0, 0.0, -2.5]))
    a = krater_yuzey(x, x0, **ortak)
    b = krater_yuzey(x, x0, tarama="distan", **ortak)
    assert a.derinlik_merkez == b.derinlik_merkez
    assert a.hacim == b.hacim
    assert a.tani["tarama"] == "distan"


def test_bilinmeyen_tarama_REDDEDILIYOR(levha):
    with pytest.raises(ValueError, match="distan"):
        _olc(levha, yukseklik=None, tarama="yan")


# --- asil iddia ----------------------------------------------------------

def test_ORTUSUZ_halde_iki_yon_AYNI_sayiyi_veriyor(levha):
    """Örtü yokken yeni tanım eskisini **yeniden üretmeli**.

    Bu kritik: `icten` yeni bir şey ölçmüyor, aynı şeyi başka yerden
    buluyor. Eşit çıkmazsa tanım değişmiş olurdu.
    """
    d = _olc(levha, yukseklik=None, tarama="distan")
    i = _olc(levha, yukseklik=None, tarama="icten")
    assert d.derinlik_merkez == pytest.approx(GERCEK, abs=1e-3)
    assert i.derinlik_merkez == pytest.approx(d.derinlik_merkez, abs=1e-6)
    assert i.hacim == pytest.approx(d.hacim, rel=1e-6)


@pytest.mark.parametrize("yuk", [2.0, 12.0, 30.0, 50.0])
def test_ORTU_NEREDE_olursa_olsun_icten_AYNI_sonucu_veriyor(levha, yuk):
    """Örtü `2 m`'de de `50 m`'de de ölçüm değişmemeli.

    `distan` bu dört halde ADR-0062 ile REDDEDİYOR; `icten` örtüsüz
    gerçeği döndürüyor. Ölçüldü: dördünde de `+0,9216`.
    """
    with pytest.raises(ValueError, match="ORTULU KRATER"):
        _olc(levha, yukseklik=yuk, tarama="distan")
    k = _olc(levha, yukseklik=yuk, tarama="icten")
    assert k.derinlik_merkez == pytest.approx(GERCEK, abs=1e-3)


def test_icten_ortu_yuksekligine_DUYARSIZ(levha):
    """Dört yükseklikte ölçüm **birbirinin aynısı** olmalı.

    `distan`'da eğim `-1,000`'di (örtüyü okuyordu); burada eğim `0`.
    """
    d = [_olc(levha, yukseklik=y, tarama="icten").derinlik_merkez
         for y in (2.0, 12.0, 30.0, 50.0)]
    assert max(d) - min(d) < 1e-6, d
    egim = float(np.polyfit([2.0, 12.0, 30.0, 50.0], d, 1)[0])
    assert abs(egim) < 1e-8, f"egim {egim}"


def test_DEGEN_ortu_krateri_GERCEKTEN_dolduruyor(levha):
    """Kör değil: örtü yüzeye **değiyorsa** ölçüm düşmeli.

    `yukseklik = 0` → perde çukurun ağzında; orada malzeme gerçekten
    krateri dolduruyor ve `icten` bunu görüyor (`0,9216 → 0,9161`).
    """
    k = _olc(levha, yukseklik=0.0, tarama="icten")
    assert k.derinlik_merkez < GERCEK
    assert k.derinlik_merkez == pytest.approx(0.9161, abs=1e-3)


def test_icten_arama_derinligine_BAGLI_DEGIL(levha):
    """`icten` kipte pencere cismin içinden başlar; `arama_derinligi`
    kullanılmaz. Değeri değiştirmek sonucu değiştirmemeli."""
    a = _olc(levha, yukseklik=30.0, tarama="icten", arama_derinligi=10.0)
    b = _olc(levha, yukseklik=30.0, tarama="icten", arama_derinligi=99.0)
    assert a.derinlik_merkez == pytest.approx(b.derinlik_merkez, abs=1e-12)
    assert a.tani["pencere_ref"]["z_alt"] == 0.0


def test_taban_cismin_DISINDAYSA_icten_REDDEDIYOR(levha):
    """`merkez` cismin dışına konursa `icten` tanımsız → sessiz sayı yok."""
    x, x0, m, v = _sahne(levha, yukseklik=None)
    n = len(x)
    with pytest.raises(ValueError):
        krater_yuzey(x, x0, m=m, h=np.full(n, H), rho=np.full(n, RHO),
                     rho_reference=np.full(n, RHO),
                     impact_direction=np.array([0.0, 0.0, -1.0]), v=v,
                     merkez=np.array([0.0, 0.0, 40.0]), tarama="icten")
