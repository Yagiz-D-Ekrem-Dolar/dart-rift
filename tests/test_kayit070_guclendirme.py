"""KAYIT-070 — β(t) şekli, kütle tutarlılığı, A85'siz aralık, gerçeklem terimleri."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference import tarih_esleme as H
from dartrift.inference.design import ParamSpace
from dartrift.inference.posterior import grid_posterior
from dartrift.observables import dart_gozlemleri as D
from dartrift.observables.impuls_sekli import SEKIL_ANLARI, impuls_sekli


def _egri(t, b):
    return [[ti, 1.0, bi, 0.0] for ti, bi in zip(t, b, strict=True)]


# ------------------------------------------------------------ impuls sekli
def test_sekil_normalize_ve_kesir_anlari():
    t = np.geomspace(1e-3, 300.0, 60)
    b = 1.0 + 3.0 * t / (t + 1.0)              # yariya 1 s'de ulasan egri
    d = impuls_sekli(_egri(t, b), t_ref=300.0)
    assert d["beta_ref"] == pytest.approx(1.0 + 3.0 * 300 / 301, rel=1e-12)
    # s(t) = (t/(t+1)) / (300/301); s = 0,5 -> t/(t+1) = 0,49834 -> t = 0,99338
    assert d["t50"] == pytest.approx(0.99338, rel=5e-3)
    assert d["s_1s"] == pytest.approx(0.5 * 301 / 300, rel=5e-3)
    assert set(f"s_{a:g}s" for a in SEKIL_ANLARI) <= set(d)


def test_sekil_OLCULEN_dejenerelik_ciftini_ayiriyor():
    """Y0=1 kaba ve Y0=10 keskin cekirdek: AYNI beta, FARKLI sekil (KAYIT-070)."""
    t = np.geomspace(1e-3, 300.0, 60)
    # olculen t50: 1,60 s (Y0=1) ve 0,62 s (keskin cekirdek); ikisi de beta 4,023
    yavas = 1.0 + 3.023 * (t / (t + 1.60)) / (300 / 301.60)
    hizli = 1.0 + 3.023 * (t / (t + 0.62)) / (300 / 300.62)
    a = impuls_sekli(_egri(t, yavas), t_ref=300.0)
    b = impuls_sekli(_egri(t, hizli), t_ref=300.0)
    assert a["beta_ref"] == pytest.approx(b["beta_ref"], rel=1e-9)   # ayni beta
    assert b["t50"] < 0.5 * a["t50"]                                  # farkli sekil
    assert b["s_1s"] - a["s_1s"] > 0.10


def test_sekil_dogrulamasi():
    t = np.geomspace(1e-3, 10.0, 20)
    e = _egri(t, 1.0 + t)
    with pytest.raises(ValueError, match="t_ref"):
        impuls_sekli(e, t_ref=300.0)
    with pytest.raises(ValueError):
        impuls_sekli(e[:2], t_ref=1.0)
    with pytest.raises(ValueError, match="kesir"):
        impuls_sekli(e, t_ref=1.0, kesirler=(1.5,))


# -------------------------------------------------------- kutle tutarliligi
def test_kutle_tutarliligi_olculen_iki_sahne():
    assert D.GOZLEM_KUTLESI == 4.3e9
    kure = D.kutle_tutarliligi(4.1666e9)          # R = 82 m, rho = 1800
    assert kure["tutarli"] and kure["bagil_fark"] == pytest.approx(-0.0310, abs=5e-4)
    elips = D.kutle_tutarliligi(3.3563e9)         # gercek sekil, ayni rho
    assert not elips["tutarli"] and "TUTARSIZ" in elips["not"]
    assert elips["bagil_fark"] == pytest.approx(-0.2195, abs=5e-4)
    # gercek sekilde kutleyi tutturan yogunluk gozlenen yogunluga esit olmali
    rho = D.yogunluk_kutleyi_tutturan(D.DIMORPHOS_SEKIL["hacim_m3"])
    assert rho == pytest.approx(2376.0, abs=1.0)
    with pytest.raises(ValueError):
        D.kutle_tutarliligi(0.0)


# ------------------------------------------------------------- A85 yan yana
class _V:
    sigma = 0.0

    def __init__(self, w):
        self.w = np.asarray(w, float)

    def predict(self, x):
        return np.atleast_2d(x) @ self.w


def test_aralik_kesin_duz_dagilimda_TAM_ve_hdi_DEGISMEDI():
    uzay = ParamSpace(names=("a", "b"), lo=(0.0, 0.0), hi=(1.0, 1.0),
                      log=(False, False))
    # bilgisiz gozlem -> kenar dagilim duz
    post = grid_posterior(uzay, [_V((0.0, 0.0))], [0.0], 1.0, n_grid=41)
    lo, hi = post.aralik_kesin(0, 0.68)
    assert lo == pytest.approx(0.16, abs=2e-3) and hi == pytest.approx(0.84, abs=2e-3)
    # eski yontem yarim bolme kayik (A85): ayni duz dagilimda sola cekiyor
    lo_eski, hi_eski = post.hdi(0)
    assert lo_eski < lo - 1e-3 and hi_eski < hi - 1e-3
    with pytest.raises(ValueError):
        post.aralik_kesin(0, 1.5)


# ------------------------------------------------ olculmus gerceklem terimi
def test_gerceklem_terimleri_kayitta_ve_kaynakli():
    for ad, beklenen in (("gerceklem_beta", 0.033), ("gerceklem_M_ejekta", 0.15)):
        deger, kaynak = H.MODEL_EKSIKLIGI_KAYNAKLI[ad]
        assert deger == pytest.approx(beklenen) and "KAYIT-070" in kaynak
    r = H.model_eksikligi_kaynakli(2.67, ["gerceklem_beta"])
    assert r["sigma"] == pytest.approx(2.67 * 0.033, rel=1e-9)


def test_hedef_sekli_OLCULEN_terim_eski_satirin_yaninda():
    """KAYIT-072: σ_şekil ölçüldü (0,009); literatürden ödünç 0,20 yerinde kalır."""
    eski, kaynak_e = H.MODEL_EKSIKLIGI_KAYNAKLI["hedef_sekli"]
    yeni, kaynak_y = H.MODEL_EKSIKLIGI_KAYNAKLI["hedef_sekli_olculen"]
    assert eski == 0.20 and "OLCULMEDI" in kaynak_e
    assert yeni == pytest.approx(0.009) and "DY2 vs DK" in kaynak_y
    # olculen terim, odunc terimden 20 kat kucuk
    assert yeni < eski / 20
    r = H.model_eksikligi_kaynakli(2.75, ["hedef_sekli_olculen", "gerceklem_beta"])
    assert r["sigma"] == pytest.approx(2.75 * np.hypot(0.009, 0.033), rel=1e-9)


def test_plato_OLCULEN_DART_terim_eski_satirin_yaninda():
    """KAYIT-072 §5 (A110): plato terimi DART sahnesinde ölçüldü (`0,016`).

    Eski `0,01` **kıyas** sahnesinin (W2, küre) eğrisindendi ve DART sahnesinin
    kalan yolunu (`%1,64`) karşılamıyor. Eski satır yerinde kalır.
    """
    eski, kaynak_e = H.MODEL_EKSIKLIGI_KAYNAKLI["plato"]
    yeni, kaynak_y = H.MODEL_EKSIKLIGI_KAYNAKLI["plato_olculen_DART"]
    assert eski == 0.01 and "W2" in kaynak_e
    assert yeni == pytest.approx(0.016) and "A110" in kaynak_y
    assert yeni > eski          # DART sahnesi kiyastan YAVAS oturuyor
    r = H.model_eksikligi_kaynakli(2.748, ["plato_olculen_DART"])
    assert r["sigma"] == pytest.approx(2.748 * 0.016, rel=1e-9)


def test_DY2_yargisi_olculen_plato_terimine_SAGLAM():
    """Kilitli DY2 yargısı (`I = 1,40`), plato 0,01 → 0,016 ile DEĞİŞMEZ.

    Kural 6: yargı koşudan önceki terimlerle hesaplandı ve öyle kalır. Bu
    sınav yalnız **duyarlılığı** gösterir: ölçülen terim yargıyı çevirmiyor.
    """
    beta, b = 3.7479718161136306, 2.7479718161136306
    for plato in ("plato", "plato_olculen_DART"):
        sm = H.model_eksikligi_kaynakli(
            b, ["gerceklem_beta", "cozunurluk_uzak", plato, "carpma_yeri"])
        uygunsuzluk = abs(beta - 3.12) / np.hypot(0.34, sm["sigma"])
        assert uygunsuzluk < 3.0                 # her iki terimle de ULASIYOR
        assert uygunsuzluk == pytest.approx(1.40, abs=0.01)


def test_KAYIT074_uc_olculmus_terim_eski_satirlarin_yaninda():
    """KAYIT-074: `mermi_geometrisi` ve iki `gerçeklem` terimi DART'ta ölçüldü."""
    cift = (("mermi_geometrisi", 0.15, "mermi_geometrisi_olculen", 0.134),
            ("gerceklem_beta", 0.033, "gerceklem_beta_DART", 0.013),
            ("gerceklem_M_ejekta", 0.15, "gerceklem_M_ejekta_DART", 0.129))
    for eski_ad, eski_v, yeni_ad, yeni_v in cift:
        e, ke = H.MODEL_EKSIKLIGI_KAYNAKLI[eski_ad]
        y, ky = H.MODEL_EKSIKLIGI_KAYNAKLI[yeni_ad]
        assert e == pytest.approx(eski_v)            # ESKI SATIR YERINDE
        assert y == pytest.approx(yeni_v) and "KAYIT-074" in ky
        assert "KAYIT-07" in ke or "L9" in ke or "KAYIT-070" in ke
    # beta'nin gerceklem sacilmasi 2,5 kat kuculdu; M_ejekta'nin kuculmedi
    assert 0.033 / 0.013 > 2.4
    assert 0.15 / 0.129 < 1.3


def test_mermi_olculen_terimi_PROTOKOL_DY_paydasina_GIRMEZ():
    """ADR-0056'nın mantığı: daha kaba bir yaklaşım, alternatif gerçek değildir.

    `0,134` bir **üst sınır** ve koşullu duyarlılık olarak raporlanır; kilitli
    yargının paydasını şişirmek için kullanılmaz.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import dy_dart_raporu as DY
    assert "mermi_geometrisi" not in DY.TERIMLER
    assert "mermi_geometrisi_olculen" not in DY.TERIMLER
    _, kaynak = H.MODEL_EKSIKLIGI_KAYNAKLI["mermi_geometrisi_olculen"]
    assert "paydaya girmez" in kaynak
