"""Konfigürasyon değerleri FİZİKSEL OLARAK MAKUL aralıkta mı?

NEDEN VAR. Şema her fiziksel büyüklüğü yalnızca `> 0` diye doğruluyor. Bir
değer **yanlış birimde** yazılırsa (km/s yerine m/s, g/cm³ yerine kg/m³,
MPa yerine Pa) doğrulamadan geçer ve fiziği **1000 kat** kaydırır — hiçbir
yerde hata vermeden.

Bu varsayımsal bir senaryo değil: proje bu hatayı **bir kez zaten yaşadı.**
PDS şekil modelleri kilometre cinsindendir; metre saymak Dimorphos'u 7,5 cm
yarıçaplı bir cisme çevirmiş ve kütlesini 1e9 kat küçültmüştü —
`docs/EKSIKLER.md` §7'de kayıtlı. O yol `units="km"` ile açık hâle getirildi,
ama **aynı sınıf başka her yerde açıktı.**

Ayrıca `dartrift/units.py` boyut kontrolü ve dönüşüm sağlıyor, fakat üretim
kodunda **hiç kullanılmıyor** (yalnızca kendi testi ve sabit-kaynağı testi
import ediyor). Yani güvence var, bağlı değil.

Bu dosya davranış değiştirmez; 10³ mertebesindeki birim hatalarını yakalar.
Aralıklar GENİŞ seçildi — amaç makul değerleri kısıtlamak değil, birim
hatasını yakalamak. Her aralığın gerekçesi yanında yazılıdır.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
URETIM = ["p3_dimorphos.yaml", "p3_scene.yaml", "p2_basalt.yaml"]


def _cfg(ad: str):
    from dartrift.config import load_config

    yol = REPO / "configs" / ad
    if not yol.is_file():
        pytest.skip(f"config yok: {ad}")
    return load_config(yol)


# (yol, alt, ust, gerekce) — alt/ust birim hatasini yakalayacak kadar genis
ARALIKLAR = [
    ("physics.tillotson.rho0", 1.0e3, 1.0e4,
     "kati kaya yogunlugu [kg/m^3]; g/cm^3 yazilirsa 2.7 cikar ve alt siniri gecer"),
    ("physics.strength.shear_G", 1.0e6, 1.0e12,
     "kesme modulu [Pa]; GPa yazilirsa 22.7 cikar"),
    ("physics.strength.YM", 1.0e3, 1.0e12, "yuksek basinc dayanim siniri [Pa]"),
    ("physics.porosity.Pe", 1.0e2, 1.0e11, "elastik esik [Pa]; MPa yazilirsa 1 cikar"),
    ("physics.porosity.Ps", 1.0e3, 1.0e12, "tam sikisma basinci [Pa]"),
    ("scene.target.bulk_density", 5.0e2, 8.0e3,
     "yigin yogunlugu [kg/m^3]; g/cm^3 yazilirsa 1.8 cikar. Alt sinir aerojel, "
     "ust sinir metal — ikisi de bir moloz yigini icin imkansiz"),
    ("scene.target.spacing", 1.0e-3, 1.0e4, "parcacik araligi [m]"),
    ("scene.impactor.mass", 1.0, 1.0e5,
     "mermi kutlesi [kg]; ton yazilirsa 0.5794 cikar"),
    ("scene.impactor.speed", 1.0e2, 1.0e5,
     "carpma hizi [m/s]; km/s yazilirsa 6.1449 cikar — DART 6144.9 m/s"),
    ("scene.impactor.density", 5.0e2, 2.0e4, "mermi yogunlugu [kg/m^3]"),
]


def _al(cfg, yol: str):
    o = cfg
    for parca in yol.split("."):
        o = getattr(o, parca, None)
        if o is None:
            return None
    return o


@pytest.mark.parametrize("ad", URETIM)
@pytest.mark.parametrize(("yol", "alt", "ust", "gerekce"), ARALIKLAR)
def test_deger_fiziksel_aralikta(ad, yol, alt, ust, gerekce):
    """Birim hatasi (10^3 mertebesi) bu araliklarin disina duser."""
    v = _al(_cfg(ad), yol)
    if v is None:
        pytest.skip(f"{ad}: {yol} yok")
    assert alt <= v <= ust, f"{ad}: {yol} = {v!r}, beklenen [{alt}, {ust}] — {gerekce}"


@pytest.mark.parametrize("ad", URETIM)
def test_gozenekli_yigin_katidan_YOGUN_OLAMAZ(ad):
    """`bulk_density <= tillotson.rho0` — gozenek yogunlugu DUSURUR.

    Bu yalnizca bir birim kontrolu degil, ADR-0030'un on sartidir: matris
    distansiyonu `alpha_m = rho0*(1-f) / (rho_hedef - f*rho0/alpha_b)`
    formulunden cozuluyor ve `alpha_m >= 1` olmasi gerekiyor. Yigin
    yogunlugu katiyi asarsa cozum FIZIKSEL DEGIL.
    """
    cfg = _cfg(ad)
    yigin = _al(cfg, "scene.target.bulk_density")
    rho0 = _al(cfg, "physics.tillotson.rho0")
    if yigin is None or rho0 is None:
        pytest.skip(f"{ad}: alanlar yok")
    assert yigin <= rho0, (
        f"{ad}: yigin yogunlugu {yigin} > kati yogunluk {rho0}; gozeneklilik "
        "yogunlugu DUSURUR, artiramaz (ADR-0030)")


@pytest.mark.parametrize("ad", URETIM)
def test_crush_egrisi_sirali(ad):
    """`Pe < Ps` — elastik esik, tam sikisma basincinin ALTINDA olmali.

    Ters yazilirsa `crush_alpha` icindeki `(Ps - P)/(Ps - Pe)` payda isaret
    degistirir ve egri anlamsizlasir. Sema bunu denetlemiyor.
    """
    cfg = _cfg(ad)
    pe, ps = _al(cfg, "physics.porosity.Pe"), _al(cfg, "physics.porosity.Ps")
    if pe is None or ps is None:
        pytest.skip(f"{ad}: porozite alanlari yok")
    assert pe < ps, f"{ad}: Pe={pe} >= Ps={ps}"


@pytest.mark.parametrize("ad", URETIM)
def test_kohezyon_yuksek_basinc_siniri_altinda(ad):
    """`Y0 < YM` — Lundborg paydasinda `(YM - Y0)` var; esitlik sonsuza gider.

    Cozucu bunu zaten reddediyor (`WarpSolid3D.__init__`), ama o KOSU
    zamanindadir. Burada KONFIGURASYON duzeyinde yakalanir.
    """
    cfg = _cfg(ad)
    y0, ym = _al(cfg, "physics.strength.Y0"), _al(cfg, "physics.strength.YM")
    if y0 is None or ym is None:
        pytest.skip(f"{ad}: dayanim alanlari yok")
    assert y0 < ym, f"{ad}: Y0={y0} >= YM={ym}"


@pytest.mark.parametrize("ad", URETIM)
def test_blok_yaricap_araligi_sirali(ad):
    cfg = _cfg(ad)
    rmin, rmax = _al(cfg, "scene.target.r_min"), _al(cfg, "scene.target.r_max")
    if rmin is None or rmax is None:
        pytest.skip(f"{ad}: blok yaricap alanlari yok")
    assert rmin < rmax, f"{ad}: r_min={rmin} >= r_max={rmax}"
    sp = _al(cfg, "scene.target.spacing")
    if sp is not None:
        # bloklar parcacik araligindan BUYUK olmali, yoksa ayriklastirilamaz
        assert rmin >= sp, f"{ad}: r_min={rmin} < spacing={sp} — blok cozulemez"


def test_units_modulu_uretimde_kullanilmiyor_KAYITLI():
    """Bilinen sinir: `dartrift.units` uretim kodunda BAGLI DEGIL.

    Modul boyut kontrolu ve donusum sagliyor ama yalnizca testler import
    ediyor. Bu test o gercegi KAYIT ALTINA alir — birisi baglarsa duser ve
    kayit guncellenir. Sessiz bir "guvence var saniyorduk" durumu olusmaz.
    """
    import subprocess

    r = subprocess.run(
        ["git", "grep", "-l", "-E", r"from \.units import|from dartrift\.units import",
         "--", "src/"],
        cwd=REPO, capture_output=True, text=True)
    kullananlar = [x for x in r.stdout.split() if x]
    assert kullananlar == [], (
        f"`units` artik uretimde kullaniliyor: {kullananlar}. "
        "docs/EKSIKLER.md'deki 'baglanmamis guvence' kaydini guncelleyin.")
