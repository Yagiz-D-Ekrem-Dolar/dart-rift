"""Aynı fiziksel sabit birden çok yerde yazılı — hepsi TUTMAK ZORUNDA.

NEDEN VAR. Bu turda bulunan beş kusurun ortak imzası şuydu:

  K7  yığın yoğunluğu   : `bulk_density` (kütle) vs `alpha0` (yoğunluk)
  K10 başlangıç distansiyonu : `pile.alpha0` (dizi) vs `porosity.alpha0` (skaler)
  K11 mermi yoğunluğu   : `impactor_density` vs `rho0_solid`/`alpha0`
  K12 yığın yoğunluğu   : mesh hacmi vs dolu hacim (aynı AD)
  K13 blok kesri        : kütle kesri vs hacim kesri (aynı AD)

**Üçü de üretim değerlerinde TESADÜFEN tutuyordu** ve ayrışma sessizdi.

Yerçekimi sabiti `G` ise YEDİ ayrı yerde yazılı; DART kütle/hız sabitleri hem
modülde hem konfigürasyonlarda. Ölçüldü: şu an hepsi tutuyor. Bu test o
eşitliği KİLİTLER — "şu an aynı" bir güvence değildir, sınanan bir eşitlik
güvencedir.

Bu dosya davranış değiştirmez; yalnızca sessiz ayrışmayı imkânsız kılar.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def kanonik_G() -> float:
    """Tek doğruluk kaynağı: `dartrift.units.G`."""
    from dartrift.units import G

    return float(getattr(G, "value", getattr(G, "magnitude", G)))


def test_G_butun_bildirimleri_ayni(kanonik_G):
    """G yedi yerde yazili; hepsi kanonik degerle AYNI olmali.

    Olculdu (bu turda): yedi bildirimin hepsi 6.6743e-11 — tek deger.
    Biri degisirse bu test duser ve ayrisma SESSIZ kalmaz.
    """
    from dartrift.cpu_reference.materials import GravityParams
    from dartrift.setup.settling import G_GRAV

    MT = importlib.import_module("dartrift.observables.momentum_transfer")
    PI = importlib.import_module("dartrift.observables.period_interface")

    kayit = {
        "cpu_reference.materials.GravityParams.G": GravityParams().G,
        "setup.settling.G_GRAV": G_GRAV,
        "observables.escape_speed": inspect.signature(
            MT.escape_speed).parameters["G"].default,
        "observables.momentum_transfer": inspect.signature(
            MT.momentum_transfer).parameters["G"].default,
        "observables.period_change": inspect.signature(
            PI.period_change).parameters["G"].default,
        "observables.beta_from_period_change": inspect.signature(
            PI.beta_from_period_change).parameters["G"].default,
    }
    sapan = {k: v for k, v in kayit.items() if v != kanonik_G}
    assert not sapan, (
        f"G kanonik degerden ({kanonik_G!r}) sapan bildirimler: {sapan}. "
        "Tek dogruluk kaynagi `dartrift.units.G`.")


def test_config_semasinin_G_varsayilani_kanonik(kanonik_G):
    import dartrift.config as C

    # Sema sinifinin ADI surumle degisebilir; bu yuzden ada gore degil,
    # "G alani tasiyor mu" diye ARANIR. Ad degisirse test sessizce
    # atlanmaz — aday bulunamazsa duser.
    adaylar = [
        obj for obj in vars(C).values()
        if isinstance(obj, type) and hasattr(obj, "model_fields")
        and "G" in getattr(obj, "model_fields", {})
    ]
    assert adaylar, "config semasinda G alani tasiyan sinif bulunamadi"
    for cls in adaylar:
        varsayilan = cls.model_fields["G"].default
        assert varsayilan == kanonik_G, (cls.__name__, varsayilan)


@pytest.mark.parametrize("ad", ["p3_dimorphos.yaml", "p3_scene.yaml", "p2_basalt.yaml"])
def test_configlerdeki_G_kanonik(ad, kanonik_G):
    """YAML'a elle yazilan G de kanonikle tutmali."""
    from dartrift.config import load_config

    yol = REPO / "configs" / ad
    if not yol.is_file():
        pytest.skip(f"config yok: {ad}")
    g = load_config(yol).physics.gravity.G
    assert g == kanonik_G, f"{ad}: G={g!r}, kanonik {kanonik_G!r}"


@pytest.mark.parametrize("ad", ["p3_dimorphos.yaml", "p3_scene.yaml"])
def test_DART_sabitleri_config_ile_ayni(ad):
    """`DART_MASS`/`DART_SPEED` hem modulde hem config'de yazili.

    `DART_MOMENTUM` modul sabitinden turer ve gozlenebilir oz-sinamalarinda
    kullanilir; config ondan ayrisirsa sentetik sinav ile gercek sahne farkli
    momentumla calisir ve karsilastirma sessizce anlamini yitirir.
    """
    from dartrift.config import load_config
    from dartrift.setup.impactor import DART_MASS, DART_MOMENTUM, DART_SPEED

    yol = REPO / "configs" / ad
    if not yol.is_file():
        pytest.skip(f"config yok: {ad}")
    imp = load_config(yol).scene.impactor
    assert imp.mass == DART_MASS, (ad, imp.mass, DART_MASS)
    assert imp.speed == DART_SPEED, (ad, imp.speed, DART_SPEED)
    assert DART_MOMENTUM == pytest.approx(DART_MASS * DART_SPEED, rel=1e-15)


@pytest.mark.parametrize("ad", ["p3_dimorphos.yaml", "p3_scene.yaml"])
def test_mermi_yogunlugu_katı_yogunluktan_buyuk_degil(ad):
    """ADR-0032: alpha = rho0/impactor_density >= 1 olmali.

    Config bu sarti ihlal ederse sahne kurulumu HATA verir; testin amaci
    bunun kosudan ONCE, config duzeyinde gorulmesidir.
    """
    from dartrift.config import load_config

    yol = REPO / "configs" / ad
    if not yol.is_file():
        pytest.skip(f"config yok: {ad}")
    cfg = load_config(yol)
    rho0 = cfg.physics.tillotson.rho0
    assert cfg.scene.impactor.density <= rho0, (
        f"{ad}: mermi yogunlugu {cfg.scene.impactor.density} > rho0 {rho0}; "
        "ADR-0032 geregi distansiyon 1'in altina duserdi")
