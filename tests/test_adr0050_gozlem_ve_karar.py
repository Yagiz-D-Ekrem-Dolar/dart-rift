"""ADR-0050 — gözlem sabitleri, yeniden şekillenme, tarih eşleme, blok çözünürlüğü."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.tarih_esleme import (
    KESME,
    MODEL_EKSIKLIGI,
    makul_mu,
    model_eksikligi_sigma,
    uygunsuzluk,
)
from dartrift.observables.dart_gozlemleri import (
    EJEKTA_KUTLESI,
    GOZLEMLER,
    KONI_ACISI,
    cheng_beta,
)
from dartrift.observables.period_interface import (
    YENIDEN_SEKILLENME_S,
    dart_beta_budget,
)
from dartrift.setup.blok_cozunurluk import blok_cozunurluk_tanisi

P_DART = 3.5601e6


# ------------------------------------------------------------ gozlemler
def test_cheng_bagintisi_2400te_yayimlanan_degeri_veriyor():
    r = cheng_beta(2400.0)
    assert r["beta"] == pytest.approx(3.61 - 0.03, abs=1e-12)
    assert r["beta_alt"] < r["beta"] < r["beta_ust"]


def test_cheng_beta_KUTLEYLE_olcekleniyor():
    a = cheng_beta(hedef_kutlesi=4.16e9)
    b = cheng_beta(hedef_kutlesi=2 * 4.16e9)
    assert (b["beta"] + 0.03) == pytest.approx(2 * (a["beta"] + 0.03), rel=1e-12)
    # sahne kutlemizde gozlenen beta, depodaki kilitli 3,12'den BUYUK
    assert 3.3 < a["beta"] < 3.6


def test_cheng_beta_GECERSIZ_cagri_REDDEDILIYOR():
    with pytest.raises(ValueError, match="yogunluk YA DA"):
        cheng_beta()
    with pytest.raises(ValueError, match="yogunluk YA DA"):
        cheng_beta(2400.0, hedef_kutlesi=4e9)
    with pytest.raises(ValueError, match="pozitif"):
        cheng_beta(-1.0)


def test_gozlemler_KAYNAK_ve_TEYIT_tasiyor():
    for g in GOZLEMLER:
        assert g.kaynak and g.teyit in ("tam_metin", "sayfa_ozeti", "arama_ozeti")
        assert g.sigma > 0.0
    assert EJEKTA_KUTLESI.deger == pytest.approx(1.6e7)
    assert KONI_ACISI.deger == pytest.approx(140.0)


# ------------------------------------------------- yeniden sekillenme
def test_yeniden_sekillenme_gozlenen_betayi_DUSURUYOR_ve_kilitliyi_BOZMUYOR():
    b = dart_beta_budget(P_DART)
    # kilitli deger (Protokol U/V bunun uzerinden yargi verdi) DEGISMEDI
    assert b["beta"] == pytest.approx(3.2228, abs=1e-3)
    s = b["yeniden_sekillenme"]
    assert s["dt_sekil_s"] == list(YENIDEN_SEKILLENME_S)
    assert s["beta_125s"] < b["beta"] and s["beta_250s"] < s["beta_125s"]
    assert 0.05 < s["bagil_dusus_125s"] < 0.08
    assert 0.10 < s["bagil_dusus_250s"] < 0.15
    assert "arama ozeti" in s["kaynak"]


# ----------------------------------------------------- tarih eslemesi
def test_uygunsuzluk_model_eksikligi_PAYDAYA_giriyor():
    dar = uygunsuzluk(2.0, 3.0, sigma_gozlem=0.34)
    genis = uygunsuzluk(2.0, 3.0, sigma_gozlem=0.34, sigma_model=0.3)
    assert float(dar) == pytest.approx(1.0 / 0.34, rel=1e-12)
    assert float(genis) < float(dar)
    assert float(genis) == pytest.approx(
        1.0 / np.sqrt(0.34 ** 2 + 0.3 ** 2), rel=1e-12)


def test_model_eksikligi_BILESENLERI_kare_toplamiyla():
    s = model_eksikligi_sigma(1.0)
    bek = np.sqrt(sum(v * v for v in MODEL_EKSIKLIGI.values()))
    assert s == pytest.approx(bek, rel=1e-12)
    # `beta - 1` uzerinden: 1,05'lik ejekta katkisinda mutlak sigma
    assert model_eksikligi_sigma(1.05) == pytest.approx(1.05 * bek, rel=1e-12)


def test_model_eksikligi_GECERSIZ_bilesen_REDDEDILIYOR():
    with pytest.raises(ValueError, match="bagil sigma"):
        model_eksikligi_sigma(1.0, {"kotu": -0.1})


def test_uygunsuzluk_gecersiz_sigma_REDDEDILIYOR():
    with pytest.raises(ValueError, match="sigma_gozlem"):
        uygunsuzluk(1.0, 2.0, sigma_gozlem=0.0)
    with pytest.raises(ValueError, match="negatif"):
        uygunsuzluk(1.0, 2.0, sigma_gozlem=0.3, sigma_model=-1.0)


def test_makul_mu_U_ORNEGI_model_eksikligiyle_ELENMIYOR():
    """U'nun en iyi kolu (`β − 1 = 1,05`) `|z| = 3,4` ile elenmişti.
    Model eksikliği payda ya girince uygunsuzluk `3`'ün altına iner —
    bu, U'nun kilitli yargısını DEĞİŞTİRMEZ; yeni protokolde kuralın
    neden koşudan önce yazılması gerektiğini gösterir."""
    gozlem, sig = 2.121, 0.341          # beta-1 ve sigma (U/V kaydi)
    model = 1.049
    i_eski = float(uygunsuzluk(model, gozlem, sigma_gozlem=sig))
    sm = model_eksikligi_sigma(model)
    k = makul_mu(model, gozlem, sigma_gozlem=sig, sigma_model=sm)
    assert i_eski > 3.0
    assert k["I"][0] < i_eski
    assert k["kesme"] == KESME
    assert k["n_makul"] in (0, 1)


# ------------------------------------------------- blok cozunurlugu
def test_blok_cozunurlugu_sayiyor_ve_COZULMEMISI_isaretliyor():
    rng = np.random.default_rng(0)
    x = rng.uniform(-10, 10, (20000, 3))
    m = np.full(len(x), 2.0)
    merkezler = np.array([[0.0, 0.0, 0.0], [5.0, 5.0, 5.0]])
    yaricaplar = np.array([3.0, 0.4])
    t = blok_cozunurluk_tanisi(x, m, merkezler, yaricaplar)
    assert t["n_blok"] == 2
    assert t["n_parcacik_max"] > 30 > t["n_parcacik_min"]
    assert t["n_cozulmemis"] == 1
    assert 0.0 < t["cozulmemis_kutle_payi"] < 0.2


def test_blok_cozunurlugu_BOS_alanda_tanimli():
    t = blok_cozunurluk_tanisi(np.zeros((3, 3)), np.ones(3),
                               np.zeros((0, 3)), np.zeros(0))
    assert t["n_blok"] == 0 and t["n_cozulmemis"] == 0


def test_blok_cozunurlugu_UYUMSUZ_girdi_REDDEDILIYOR():
    with pytest.raises(ValueError, match="ayni olmali"):
        blok_cozunurluk_tanisi(np.zeros((3, 3)), np.ones(3),
                               np.zeros((2, 3)), np.ones(3))
