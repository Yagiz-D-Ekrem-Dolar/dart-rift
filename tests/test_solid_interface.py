"""ADR-0041 §5 boşluk 3 ölçümü — IC ve yargı mantığı (GPU gerekmez)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.solid_interface import (BASALT_SOLID, KUTU, RHO0,
                                                 _malzeme, _sok_yaricapi,
                                                 build_two_zone_solid_ic,
                                                 judge)


def _uc_kol(n=16, lam=2, r_ic=0.15, per_particle_h=True):
    h = 2.0 / n
    return (build_two_zone_solid_ic(n, 1, r_ic, h),
            build_two_zone_solid_ic(n, lam, r_ic, h,
                                    per_particle_h=per_particle_h),
            build_two_zone_solid_ic(n * lam, 1, r_ic, h / lam))


def test_enerji_uc_kolda_AYNI() -> None:
    """Farklı enerji = farklı problem. `1e-3` değil, `1e-12` isteniyor."""
    e = [k["energy_injected"] for k in _uc_kol()]
    assert (max(e) - min(e)) / max(e) < 1e-12, e


def test_kutle_sapmasi_KUCUK_ama_SIFIR_DEGIL() -> None:
    """Küre sınırı iki kafesle mükemmel döşenmez — susulmaz, ölçülür."""
    m = [k["total_mass"] for k in _uc_kol()]
    sapma = (max(m) - min(m)) / max(m)
    assert 0.0 < sapma < 0.005, sapma


def test_lam1_TEK_populasyon() -> None:
    """Boşluk kontrolü: `lam=1` iki bölgeli değildir, `h` tekdüzedir."""
    k = build_two_zone_solid_ic(16, 1, 0.15, 0.125)
    assert k["h_min"] == k["h_max"] == 0.125
    assert len(k["m"]) == 16 ** 3
    assert np.all(k["m"] == k["m"][0])


def test_A_prime_ince_bolgeye_KUCUK_h_veriyor() -> None:
    """A′'nın tanımı: ince bölge `h/λ` alır."""
    k = build_two_zone_solid_ic(16, 2, 0.15, 0.125, per_particle_h=True)
    assert k["h_min"] == pytest.approx(0.0625)
    assert k["h_max"] == pytest.approx(0.125)
    assert k["per_particle_h"] is True


def test_kontrol_kolu_TEK_h_kullaniyor() -> None:
    """`per_particle_h=False` A′'yı kapatır — katkıyı yalıtan kontrol kolu."""
    k = build_two_zone_solid_ic(16, 2, 0.15, 0.125, per_particle_h=False)
    assert k["h_min"] == k["h_max"] == pytest.approx(0.125)
    # Ama kutle DAGILIMI hala iki bolgeli -- yalnizca h degisti.
    assert len(np.unique(k["m"])) == 2


def test_kutle_yerel_hucre_hacminden() -> None:
    """ADR-0030'un değişmezi: `m = ρ₀·dx³`, bölgeye göre."""
    k = build_two_zone_solid_ic(16, 2, 0.15, 0.125)
    kutleler = np.unique(k["m"])
    assert kutleler[1] / kutleler[0] == pytest.approx(8.0, rel=1e-12)
    assert kutleler[1] == pytest.approx(RHO0 * (KUTU / 16) ** 3, rel=1e-12)


def test_gecersiz_girdiler_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError):
        build_two_zone_solid_ic(16, 0, 0.15, 0.125)
    with pytest.raises(ValueError):
        build_two_zone_solid_ic(16, 2, 0.6, 0.125)
    with pytest.raises(ValueError):
        build_two_zone_solid_ic(16, 2, 0.001, 0.125)   # ince bölge boş


def test_sok_yaricapi_sikismamis_ise_PATLIYOR() -> None:
    """Sessizce `0.0` dönmek, "şok yok"u "şok merkezde" diye raporlardı."""
    x = np.array([[0.1, 0.0, 0.0], [0.2, 0.0, 0.0]])
    with pytest.raises(RuntimeError):
        _sok_yaricapi(x, np.array([RHO0, RHO0]))


def test_sok_yaricapi_EN_DIS_sikisani_buluyor() -> None:
    x = np.array([[0.1, 0.0, 0.0], [0.3, 0.0, 0.0], [0.4, 0.0, 0.0]])
    rho = np.array([2.0 * RHO0, 2.0 * RHO0, RHO0])
    assert _sok_yaricapi(x, rho) == pytest.approx(0.3)


def _kol(r, m=1.0, e=1.0):
    return {"r_measured": r, "total_mass": m, "energy_injected": e,
            "N": 1, "h_min": 1.0, "h_max": 1.0, "n_injected": 1,
            "rho_max": 1.0, "n_steps": 1}


def test_yargi_parantez_ICINDE_zararsiz() -> None:
    y = judge(_kol(0.20), _kol(0.25), _kol(0.30), 2, 0.15, 1.0)
    assert y["yargi"] == "arayuz_zararsiz"
    assert y["tasma_rel"] == 0.0


def test_yargi_parantez_DISINDA_bedelli() -> None:
    y = judge(_kol(0.20), _kol(0.40), _kol(0.30), 2, 0.15, 1.0)
    assert y["yargi"] == "arayuz_bedelli"
    assert y["tasma_rel"] > 0.0


def test_yargi_kollar_ayirt_EDILEMEZSE_belirsiz() -> None:
    """Parantez sıfır genişlikteyse ölçüt boştur."""
    y = judge(_kol(0.30), _kol(0.30), _kol(0.3001), 2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"
    assert y["kollar_ayirt_edilebilir"] is False


def test_yargi_enerji_FARKLIYSA_belirsiz() -> None:
    y = judge(_kol(0.20, e=1.0), _kol(0.25, e=1.1), _kol(0.30, e=1.0),
              2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"
    assert y["enerji_esit"] is False


def test_yargi_kutle_BUYUKSE_belirsiz() -> None:
    y = judge(_kol(0.20, m=1.0), _kol(0.25, m=2.0), _kol(0.30, m=1.0),
              2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"
    assert y["kutle_ihmal_edilebilir"] is False


def test_malzeme_bayraklari_GERCEKTEN_geciyor() -> None:
    """Ayrıştırma kolları gerçekten farklı malzeme kuruyor mu?"""
    assert BASALT_SOLID.strength.enabled
    assert BASALT_SOLID.porosity.enabled
    assert BASALT_SOLID.damage.enabled
    m = _malzeme(True, False, False)
    assert m.strength.enabled and not m.porosity.enabled and not m.damage.enabled
