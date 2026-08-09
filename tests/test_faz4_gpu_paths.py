"""FAZ 4 ölçüm modüllerinin **GPU yolları** (CUDA yoksa atlanır).

Bu dosya olmadan `resolution_scaling` ve `shock_interface`'in koşucu
fonksiyonları hiçbir testten çağrılmıyordu: yerelde GPU yok, TRUBA'da ise
yalnızca elle yazılmış betiklerden çağrılıyorlardı. Yani **kapsam boşluğu**
— ve tam da B1'in (`dt` çapraz kontrolü hiç yoktu) tekrarı.

Testler **küçük** çözünürlük kullanır: amaç fizik ölçmek değil, kod yolunun
**koşulabilir ve tutarlı** olduğunu göstermek. Fiziksel ölçümler
KAYIT-023/E3'te ayrıca yapıldı.
"""
from __future__ import annotations

import pytest


def _cuda_ya_da_atla() -> str:
    from dartrift.particles import warp_available, warp_devices

    if not warp_available():
        pytest.skip("warp yok")
    dev = [d for d in warp_devices() if str(d).startswith("cuda")]
    if not dev:
        pytest.skip("CUDA yok")
    return str(dev[0])


def test_resolution_scaling_tek_kosu() -> None:
    """`run_single` hem olağan hem **sabit `h`** kolunda koşabiliyor mu?"""
    from dartrift.validation.resolution_scaling import run_single

    dev = _cuda_ya_da_atla()
    olagan = run_single(32, None, dev)
    sabit = run_single(32, 2.0 / 32.0, dev)
    # n=32'de sabit h TAM olarak olagan h'dir -> iki kol AYNI kosudur.
    assert olagan["h"] == pytest.approx(sabit["h"])
    assert olagan["r_measured"] == pytest.approx(sabit["r_measured"], rel=1e-12)
    assert olagan["h_over_dx"] == pytest.approx(2.0)
    assert 0.2 < olagan["r_measured"] < 0.3, olagan
    assert olagan["n_steps"] > 50


def test_resolution_scaling_kol_platoyu_okuyor() -> None:
    """`run_arm` platoyu ve **oturmuşluğu** raporluyor mu?"""
    from dartrift.validation.resolution_scaling import run_arm

    dev = _cuda_ya_da_atla()
    kol = run_arm((32, 40, 48), None, dev)
    assert len(kol["rows"]) == 3
    assert kol["plateau"] > 0.0
    assert 0.0 <= kol["last_rel_change"] < 1.0
    assert isinstance(kol["settled"], bool)


def test_resolution_scaling_dogrulama() -> None:
    from dartrift.validation.resolution_scaling import run_arm

    with pytest.raises(ValueError, match="en az 3"):
        run_arm((32, 40), None, "cpu")
    with pytest.raises(ValueError, match="artan"):
        run_arm((48, 32, 64), None, "cpu")


def test_shock_interface_iki_bolgeli_kosu() -> None:
    """İki bölgeli Sedov gerçekten koşuyor ve makul bir yarıçap veriyor mu?"""
    from dartrift.validation.shock_interface import (build_two_zone_sedov_ic,
                                                     run_shock_interface)

    dev = _cuda_ya_da_atla()
    r = run_shock_interface(n_coarse=32, lam=2, r_inner=0.15, device=dev)
    for kol in ("uniform_coarse", "two_zone", "uniform_fine"):
        d = r[kol]
        assert 0.15 < d["r_measured"] < 0.35, (kol, d)
        assert d["n_steps"] > 50, (kol, d)
    # Uc kol AYNI h ile kosmali — tasarimin cekirdegi budur.
    assert (r["uniform_coarse"]["h"] == r["two_zone"]["h"]
            == r["uniform_fine"]["h"])
    # Enerji uc kolda ayni: farkli olsaydi FARKLI PROBLEM cozulmus olurdu.
    assert r["energy_injection_matches"] is True, r
    # Iki bolgeli kolda gercekten IKI kutle var mi (bos test olmasin)?
    ic = build_two_zone_sedov_ic(32, 2, 0.15, 2.0 / 32.0)
    assert len(set(ic["m"].round(15))) == 2
    assert r["verdict"] in {"interface_harmless", "interface_costs",
                            "inconclusive"}


# ---------------------------------------------------------------------------
# `--gozeneksiz` kontrol kolu (CPU — GPU gerekmiyor)
# ---------------------------------------------------------------------------

def _faz48_modulu():
    import importlib.util as iu
    from pathlib import Path
    yol = Path(__file__).resolve().parents[1] / "scripts" / "faz48_iki_asama.py"
    s = iu.spec_from_file_location("_faz48", yol)
    m = iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_gozeneksiz_kol_sahnesi_KATI_ve_TUTARLI():
    """Kontrol kolu cismi patlatarak *"krater oluştu"* dememeli.

    İki ayrı tuzak ölçüldü (rapor A14):

    1. Sadece P-α'yı kapatmak: `rho` başlangıcı `rho0/alpha0` kaldığı
       için cisim `-4,74 GPa` gerilmede başlıyordu.
    2. Sadece `alpha0 = 1` demek: gerilme gitti ama `m/V = 1537` iken
       `rho = 2700` oldu — SPH hacim elemanı `%76` yanlış.

    Doğrusu sahneyi **katı** kurmak. Bu test ikisini birden sınar:
    `alpha0 = 1`, `m/V == rho` ve `P(t=0) == 0`.
    """
    import numpy as np
    from dartrift.cpu_reference.materials import tillotson_pressure
    from dartrift.setup.rubble_generator import particle_volume
    from dartrift.setup.scene import build_scene

    m48 = _faz48_modulu()
    V = particle_volume(7.0)

    for gozeneksiz in (False, True):
        kb = build_scene(spacing=7.0, device="cpu",
                         **m48._sahne_kolu(gozeneksiz))
        a0 = np.asarray(kb.alpha0)
        mat = m48._mat(gozeneksiz)
        rho_bas = mat.tillotson.rho0 / a0

        # (a) gozeneksiz kolda sahne gercekten kati mi
        if gozeneksiz:
            assert np.allclose(a0, 1.0), f"alpha0 {a0.min()}..{a0.max()}"
            m48._alpha0_denetle(a0, True)          # hata vermemeli

        # (b) kutle ile yogunluk UYUSUYOR mu (SPH hacim elemani).
        # YALNIZCA HEDEF: mermi kendi (cok daha ince) araligiyla kuruldu,
        # onun kutlesini hedefin hucre hacmine bolmek anlamsiz. Bu ayrimi
        # testin kendisi yakaladi -- elle bakarken medyan gizlemisti.
        hedef = ~np.asarray(kb.is_impactor, dtype=bool)
        mv = np.asarray(kb.m)[hedef] / V
        assert np.allclose(mv, rho_bas[hedef], rtol=1e-9), (
            f"gozeneksiz={gozeneksiz}: m/V {np.median(mv):.1f} != "
            f"rho {np.median(rho_bas[hedef]):.1f}")

        # (c) t=0 gerilmesiz mi
        arg = rho_bas if gozeneksiz else rho_bas * a0
        P = np.asarray(tillotson_pressure(arg, np.zeros(len(a0)),
                                          mat.tillotson))
        if not gozeneksiz:
            P = P / a0
        assert np.allclose(P, 0.0, atol=1.0), f"P max {np.abs(P).max():.3e}"


def test_alpha0_denetle_kati_olmayan_sahneyi_YAKALAR():
    """Sahne katı kurulmadıysa gözeneksiz kol sessizce koşmamalı."""
    import numpy as np
    import pytest as _pt
    m48 = _faz48_modulu()
    with _pt.raises(ValueError, match="alpha0 != 1"):
        m48._alpha0_denetle(np.array([1.0, 1.5]), True)
    # gozenekli kolda ayni dizi SORUN DEGIL
    m48._alpha0_denetle(np.array([1.0, 1.5]), False)


def test_duzeltilmemis_alpha0_GERCEKTEN_gerilme_uretiyordu():
    """Düzeltmenin gerekçesi ölçülmüş bir sayı; kaybolmasın."""
    import numpy as np
    from dartrift.cpu_reference.materials import tillotson_pressure

    m48 = _faz48_modulu()
    mat = m48._mat(True)                      # P-alpha KAPALI
    rho = mat.tillotson.rho0 / 1.30           # ama alpha0 DUZELTILMEMIS
    P = float(np.asarray(tillotson_pressure(
        np.array([rho]), np.array([0.0]), mat.tillotson)).ravel()[0])
    assert P < -1.0e9, f"beklenen buyuk gerilme, {P:.3e} cikti"
