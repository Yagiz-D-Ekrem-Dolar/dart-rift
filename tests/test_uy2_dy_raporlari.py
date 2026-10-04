"""PROTOKOL-UY2 ve PROTOKOL-DY kilitli kuralları — koşudan önce sınandı."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dy_dart_raporu as DY  # noqa: E402
import uy2_kesisim_raporu as U2  # noqa: E402


def _egri(beta, t_son, n=40):
    t = np.geomspace(1e-3, t_son, n)
    b = 1.0 + (beta - 1.0) * t / (t + 0.8)          # son degeri beta'ya yakinsayan
    b[-1] = beta
    return [[float(ti), 1.0, float(bi), 1e6] for ti, bi in zip(t, b, strict=True)]


def _npz(kok: Path, ad: str, beta, t_son, *, gecerli=True, n=100):
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    ft = {"beta_hedef": beta, "M_ejekta": 2.0e7, "impuls_egrisi": _egri(beta, t_son),
          "beta_iki_yontem": {"beta_km": beta + 0.02}}
    np.savez(d / "nokta_0000_a.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps({"gecerli": gecerli}), m=np.ones(n))


# ------------------------------------------------------------------- UY2
def test_UY2_sabitler_kilitli():
    assert U2.T_KIYAS == 300.0 and U2.ESIK_BAGIMSIZ_DEGIL == 0.05
    assert U2.DELTA_02 == 0.098
    assert U2.KOLLAR == {"kaba": "W2_Y10_g1p0", "orta": "UY2_orta_g1p0"}


def _uy2(kok, b_kaba, b_orta, **kw):
    # kaba kol 600 s kosar, orta kol 300 s; ikisi de 300 s'de okunur
    _npz(kok, "W2_Y10_g1p0", b_kaba, 600.0)
    _npz(kok, "UY2_orta_g1p0", b_orta, 300.0, **kw)
    return U2.yargi(U2.topla(kok))


@pytest.mark.parametrize("b_orta,genel,merdiven", [
    (4.15, "EKSENLER BAGIMSIZ DEGIL", "kaba"),
    (4.35, "AZALIYOR", "kaba + cok dogruluklu"),
    (4.70, "EKSENLER BAGIMSIZ", "orta")])
def test_UY2_uc_yargi_ve_uretim_karari(tmp_path, b_orta, genel, merdiven):
    out = _uy2(tmp_path / genel.replace(" ", "_"), 4.10, b_orta)
    assert out["genel"] == genel and out["uretim_merdiveni"] == merdiven
    if genel != "OKUNMAZ":
        assert out["sigma_cozunurluk"] == pytest.approx(out["delta_kesisim"])


def test_UY2_OKUNMAZ_ve_sekil_tanisi(tmp_path):
    out = _uy2(tmp_path / "a", 4.10, 4.15, gecerli=False)
    assert out["genel"].startswith("OKUNMAZ") and out["uretim_merdiveni"] is None
    out2 = _uy2(tmp_path / "b", 4.10, 4.15)
    assert "d_s_1s" in out2["sekil"] and out2["sekil"]["t50_orani"] > 0


# -------------------------------------------------------------------- DY
def test_DY_sabitler_kilitli():
    assert DY.BETA_GOZLEM == 3.12 and DY.SIGMA_GOZLEM == 0.34 and DY.KESME == 3.0
    assert DY.TERIMLER == ("gerceklem_beta", "cozunurluk_uzak", "plato", "carpma_yeri")


@pytest.mark.parametrize("beta,genel", [
    (3.20, "MODEL GOZLEME ULASIYOR"),
    (2.85, "MODEL GOZLEME ULASIYOR"),      # I < 3 ve bandin ust yarisinda
    (2.00, "MODEL ULASMIYOR"),
    (5.50, "MODEL ASIYOR")])
def test_DY_yargilari(tmp_path, beta, genel):
    kok = tmp_path / f"{beta}"
    _npz(kok, DY.AD, beta, 600.0)
    out = DY.yargi(DY.oku(kok))
    assert out["genel"] == genel
    assert out["payda"] > DY.SIGMA_GOZLEM          # model eksikligi paydayi buyutur


def test_DY_OKUNMAZ_beta_YAZILMAZ(tmp_path):
    _npz(tmp_path, DY.AD, 3.2, 600.0, gecerli=False)
    out = DY.yargi(DY.oku(tmp_path))
    assert out["genel"].startswith("OKUNMAZ") and "beta" not in out
    kok2 = tmp_path / "kisa"
    _npz(kok2, DY.AD, 3.2, 200.0)                  # 600 s'ye ulasmamis
    out2 = DY.yargi(DY.oku(kok2))
    assert out2["genel"].startswith("OKUNMAZ") and "beta" not in out2
    assert DY.yargi(DY.oku(tmp_path / "yok"))["genel"].startswith("OKUNMAZ")


def test_DY_sigma_model_OLCULMUS_terimlerden(tmp_path):
    _npz(tmp_path, DY.AD, 3.20, 600.0)
    out = DY.yargi(DY.oku(tmp_path))
    beklenen = (3.20 - 1.0) * np.sqrt(0.033**2 + 0.004**2 + 0.01**2 + 0.10**2)
    assert out["sigma_model"] == pytest.approx(beklenen, rel=1e-9)


# --------------------------------------------- PROTOKOL-DY §6.3: sigma_sekil
def test_DY_onek_secilebiliyor(tmp_path):
    _npz(tmp_path, DY.AD_DY2, 3.4, 600.0)
    out = DY.yargi(DY.oku(tmp_path, DY.AD_DY2))
    assert out["genel"] == "MODEL GOZLEME ULASIYOR"
    assert DY.oku(tmp_path, DY.AD) is None          # eski kol yok


def test_sigma_sekil_kilitli_formul(tmp_path):
    _npz(tmp_path, DY.AD_DY2, 4.20, 600.0)          # b = 3,20
    _npz(tmp_path, DY.AD_DK, 3.80, 600.0)           # b = 2,80
    s = DY.sigma_sekil(DY.oku(tmp_path, DY.AD_DY2), DY.oku(tmp_path, DY.AD_DK))
    assert s["genel"] == "OLCULDU"
    assert s["sigma_sekil"] == pytest.approx(abs(3.20 - 2.80) / 3.20)
    assert s["eski_literatur_terimi"] == 0.20
    assert "ORTA" in s["yorum"]            # 0,4/3,2 = 0,125 -> orta bant


def test_sigma_sekil_uc_yorum(tmp_path):
    for b_kure, anahtar in ((4.19, "KUCUK"), (4.00, "ORTA"), (3.50, "BUYUK")):
        kok = tmp_path / f"{b_kure}"
        _npz(kok, DY.AD_DY2, 4.20, 600.0)
        _npz(kok, DY.AD_DK, b_kure, 600.0)
        s = DY.sigma_sekil(DY.oku(kok, DY.AD_DY2), DY.oku(kok, DY.AD_DK))
        assert anahtar in s["yorum"], (b_kure, s["sigma_sekil"], s["yorum"])


def test_sigma_sekil_gecersiz_kolda_OKUNMAZ(tmp_path):
    _npz(tmp_path, DY.AD_DY2, 4.20, 600.0)
    _npz(tmp_path, DY.AD_DK, 3.80, 600.0, gecerli=False)
    s = DY.sigma_sekil(DY.oku(tmp_path, DY.AD_DY2), DY.oku(tmp_path, DY.AD_DK))
    assert s["sigma_sekil"] is None and s["genel"].startswith("OKUNMAZ")
    assert DY.sigma_sekil(None, None)["sigma_sekil"] is None


def test_CLI_kure_kol_ile_sekil_olcumu(tmp_path, capsys):
    _npz(tmp_path, DY.AD_DY2, 4.20, 600.0)
    _npz(tmp_path, DY.AD_DK, 3.80, 600.0)
    yol = tmp_path / "S_DY2.json"
    assert DY.main(["--kok", str(tmp_path), "--ad", DY.AD_DY2,
                    "--kure-kol", DY.AD_DK, "--json", str(yol)]) == 0
    d = json.loads(yol.read_text(encoding="utf-8"))
    assert d["kol_adi"] == DY.AD_DY2
    assert d["sekil_olcumu"]["sigma_sekil"] == pytest.approx(0.4 / 3.2)
    assert "sigma_sekil" in capsys.readouterr().out
