"""A115 — çıkarım hattı provası: üç vekil kipi ve SBC'nin değişmezi.

Sınavlar **küçük** ayarlarla koşar (hız); A115'in kayıttaki sayıları
`n_sbc = 200` ile ölçüldü ve burada yeniden üretilmez.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prova_cikarim as PR  # noqa: E402


def test_olculen_sabitler_KAYIT073_ile_ayni():
    assert PR.P_BETA == pytest.approx(-0.0760)
    assert PR.P_M == pytest.approx(-0.3206)
    assert PR.P_KOS == pytest.approx(0.0585)
    assert PR.SIGMA_GERCEKLEM_BETA == 0.033 and PR.SIGMA_GERCEKLEM_M == 0.15
    # ADR-0054'un hedefi
    assert PR.BETA_GOZLEM == pytest.approx(3.5418)


def test_ileri_olculen_noktalari_veriyor():
    """`Y₀ = 10 Pa`'da W2'nin ölçülen değerleri (katsayı terimleri sıfır).

    `M_ejekta` ve `kos_ort`'un önçarpanları `10 Pa` noktasına **sabitlendi**,
    o yüzden tam geçer. `β`'nın önçarpanı ise **uydurmadan** geliyor ve
    uydurmanın ölçülen artığı `%5,3` (KAYIT-073) — bu yüzden `10 Pa`'da
    `3,91` verir, ölçülen `4,07` değil. Fark uydurmanın kendisi, hata değil.
    """
    th = np.array([[PR.ORTA_AB, 10.0, PR.ORTA_F]])
    y = PR.ileri(th, PR.SENARYOLAR["ayrik"], ucuncu=True)[0]
    assert 10.0 ** y[0] + 1.0 == pytest.approx(4.0699, rel=0.06)   # beta (uydurma)
    assert 10.0 ** y[1] == pytest.approx(3.0290e7, rel=1e-3)       # M_ejekta (sabit)
    assert 10.0 ** y[2] == pytest.approx(0.71922, rel=1e-3)        # kos_ort (sabit)


def test_ileri_Y0_ussu_OLCULEN_degerle_uyusuyor():
    kat = PR.SENARYOLAR["ayrik"]
    th = np.array([[PR.ORTA_AB, 1.0, PR.ORTA_F], [PR.ORTA_AB, 100.0, PR.ORTA_F]])
    y = PR.ileri(th, kat)
    assert (y[1, 0] - y[0, 0]) / 2.0 == pytest.approx(PR.P_BETA, abs=1e-12)
    assert (y[1, 1] - y[0, 1]) / 2.0 == pytest.approx(PR.P_M, abs=1e-12)


def test_SBC_degismezi_uretici_olabilirlikle_AYNI_sigmayi_kullaniyor():
    """A115 (d): ilk sürümdeki kurgu hatası geri gelmesin.

    Üretici `sigma` (olabilirliğin paydası) ile gürültü eklemeli; `olcek`
    (yalnız gerçeklem) ile eklerse PIT zorunlu olarak AŞIRI TEMKİNLİ çıkar.
    """
    import inspect
    kaynak = inspect.getsource(PR.prova)
    i = kaynak.index("def uret(")
    govde = kaynak[i:i + 700]
    assert "scale=sigma" in govde
    assert "scale=olcek" not in govde


@pytest.mark.parametrize("kip", ["ikinci", "gp", "tam"])
def test_uc_vekil_kipi_kosuyor(kip):
    out = PR.prova("ayrik", n_tasarim=40, n_grid=12, n_sbc=10, vekil_kipi=kip)
    assert out["vekil_kipi"] == kip
    assert out["gozlemli_sayisi"] == 2 and out["parametre_sayisi"] == 3
    assert len(out["eksenler"]) == 3
    assert out["genel"] in ("HAT CALISIYOR", "HAT KALIBRE DEGIL")
    assert "sonuc DEGIL" in out["UYARI"]
    if kip == "gp":
        assert out["gp_bilgi"] is not None
        assert all(g["varyans_carpani"] >= 1.0 for g in out["gp_bilgi"])
    if kip == "tam":
        assert out["vekil_loo_sd"] == [0.0, 0.0]      # vekil YOK


def test_TAM_model_posterior_makinesini_sinar():
    """A115 (c)1: tam modelle `Y₀` öğrenilmeli — makine çalışıyor demek."""
    out = PR.prova("ayrik", n_tasarim=40, n_grid=16, n_sbc=10, vekil_kipi="tam")
    y0 = next(e for e in out["eksenler"] if e["ad"] == "Y0")
    assert y0["daralma"] > 0.5 and y0["genel"] == "TANIMLANABILIR"


def test_fisher_ucuncu_ozdeger_SIFIR_iki_gozemliyle():
    """ADR-0051 §2c aritmetiği: 2 gözlemli, 3 parametre → bir yön boş."""
    out = PR.prova("ayrik", n_tasarim=40, n_grid=12, n_sbc=10, vekil_kipi="tam")
    lam = sorted(out["fisher"]["ozdegerler"], reverse=True)
    assert lam[2] == pytest.approx(0.0, abs=1e-6)
    assert out["fisher"]["ust_sinir"] == 2
    assert out["fisher"]["ogrenilen_yon_sayisi"] <= 2


def test_gecersiz_senaryo():
    with pytest.raises(ValueError, match="senaryo"):
        PR.prova("yok", n_tasarim=20, n_grid=10, n_sbc=10)


# ------------------------------------------------- ADR-0058 §3: korelasyon
def test_korelasyon_matrisi_ve_denetimi():
    R = PR._korelasyon(2, 0.8)
    assert R.shape == (2, 2)
    assert R[0, 0] == 1.0 and R[0, 1] == pytest.approx(0.8)
    assert np.all(np.linalg.eigvalsh(R) > 0.0)       # pozitif tanimli
    assert np.allclose(PR._korelasyon(3, 0.0), np.eye(3))
    for kotu in (1.0, -1.0, 1.5):
        with pytest.raises(ValueError, match="rho"):
            PR._korelasyon(2, kotu)


def test_rho_arttikca_alpha_b_DARALIYOR_Y0_degismiyor():
    """ADR-0058 §3'ün ölçümü: `R = I` almak bilgiyi yanlış yere dağıtıyor."""
    dar = {}
    for rho in (0.0, 0.8):
        out = PR.prova("ayrik", n_tasarim=40, n_grid=20, n_sbc=10,
                       vekil_kipi="tam", rho=rho)
        dar[rho] = {e["ad"]: e["daralma"] for e in out["eksenler"]}
        assert out["rho"] == pytest.approx(rho)
    # alpha_b belirgin sekilde daha cok daraliyor
    assert dar[0.8]["boulder_alpha0"] > dar[0.0]["boulder_alpha0"] + 0.15
    # Y0 neredeyse degismiyor (korelasyon oradan bilgi almiyor)
    assert abs(dar[0.8]["Y0"] - dar[0.0]["Y0"]) < 0.05
