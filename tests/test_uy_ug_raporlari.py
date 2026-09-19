"""PROTOKOL-UY ve PROTOKOL-UG kilitli kuralları — sınavlar (koşudan önce)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ug_gecis_raporu as G  # noqa: E402
import uy_yakin_alan_raporu as Y  # noqa: E402


def _npz(kok: Path, ad: str, egri, *, gecerli=True, t_gecis=0.2, n=100):
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    ft = {"beta_hedef": float(egri[-1][2]), "M_ejekta": 1e6,
          "impuls_egrisi": [list(map(float, r)) for r in egri],
          "beta_iki_yontem": {"beta_km": float(egri[-1][2]),
                              "koni_tam_acisi_derece": 150.0},
          "gec_evre": {"t_gecis": t_gecis, "enerji_once": {"e_kin": 3.7e8}}}
    np.savez(d / "nokta_0000_a.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps({"gecerli": gecerli}), m=np.ones(n))


def _egri(beta_son: float, t_son: float, *, beta_300=None):
    """Log aralikli egri; `beta_300` verilirse 300 s'de o deger."""
    ts = np.geomspace(1e-3, t_son, 40)
    if t_son > 300.0:
        ts = np.unique(np.append(ts, 300.0))   # 300 s tam dugum: aradeger karismasin
    bs = np.full_like(ts, beta_son)
    if beta_300 is not None:
        bs = np.where(ts <= 300.0, beta_300, beta_son)
    return [[t, 1.0, b, 1e6] for t, b in zip(ts, bs, strict=True)]


# ---------------------------------------------------------------- UY
def test_UY_esikler_kilitli():
    assert Y.ESIK_KUCUK == 0.05 and Y.ESIK_DUYARLI == 0.15 and Y.T_KIYAS == 300.0
    assert Y.KOLLAR == {"kaba": "W2_Y10_g0p2", "orta": "UY_orta", "ic": "UY_ic"}


def test_beta_aninda_log_aradeger_ve_KIRPMA_YOK():
    e = [[100.0, 1, 3.0, 0], [1000.0, 1, 4.0, 0]]
    # log10(300) = 2,477 -> 3 + 0,477
    assert Y.beta_aninda(e, 300.0) == pytest.approx(3.0 + np.log10(3.0), rel=1e-12)
    assert np.isnan(Y.beta_aninda(e, 50.0))          # egri disi: uydurma yok
    assert np.isnan(Y.beta_aninda(e, 2000.0))
    assert Y.beta_aninda(e, 1000.0) == 4.0


def _uy(kok, bk, bo, bi, **kw):
    _npz(kok, "W2_Y10_g0p2", _egri(bk - 0.02, 600.0, beta_300=bk))
    _npz(kok, "UY_orta", _egri(bo, 300.0), **kw)
    _npz(kok, "UY_ic", _egri(bi, 300.0), **kw)
    return Y.yargi(Y.topla(kok))


def test_UY_kaba_kol_300s_degerini_okur_SON_degeri_degil(tmp_path):
    out = _uy(tmp_path, 3.70, 3.70, 3.70)
    assert out["kollar"]["kaba"]["beta_300"] == pytest.approx(3.70)
    assert out["kollar"]["kaba"]["beta_son"] == pytest.approx(3.68)
    assert out["genel"] == "IKI NOKTADA FARK KUCUK"


@pytest.mark.parametrize("bo,genel", [(3.80, "IKI NOKTADA FARK KUCUK"),
                                      (3.95, "COZUNURLUK TERIMI GEREKLI"),
                                      (3.20, "COZUNURLUGE DUYARLI")])
def test_UY_uc_yargi(tmp_path, bo, genel):
    out = _uy(tmp_path, 3.70, bo, 3.70)
    assert out["genel"] == genel
    assert out["sigma_cozunurluk"] == pytest.approx(abs(bo - 3.70) / (bo - 1.0))


def test_UY_ic_payi_tani(tmp_path):
    out = _uy(tmp_path, 3.70, 3.30, 3.40)
    assert out["ic_payi"] == pytest.approx(0.75)


def test_UY_OKUNMAZ_gecersiz_ya_da_300s_ulasmamis(tmp_path):
    out = _uy(tmp_path / "a", 3.7, 3.7, 3.7, gecerli=False)
    assert out["genel"].startswith("OKUNMAZ") and set(out["gecersiz"]) == {"orta", "ic"}
    _npz(tmp_path / "b", "W2_Y10_g0p2", _egri(3.7, 600.0))
    _npz(tmp_path / "b", "UY_orta", _egri(3.7, 250.0))      # sure asimi
    _npz(tmp_path / "b", "UY_ic", _egri(3.7, 300.0))
    out = Y.yargi(Y.topla(tmp_path / "b"))
    assert out["genel"].startswith("OKUNMAZ") and out["ulasmadi"] == ["orta"]


def test_UY_CLI(tmp_path, capsys):
    _uy(tmp_path, 3.70, 3.72, 3.71)
    yol = tmp_path / "S_UY.json"
    assert Y.main(["--kok", str(tmp_path), "--json", str(yol)]) == 0
    assert json.loads(yol.read_text(encoding="utf-8"))["genel"] == "IKI NOKTADA FARK KUCUK"
    assert "GENEL" in capsys.readouterr().out


# ---------------------------------------------------------------- UG
def test_UG_esik_ve_kollar_kilitli():
    assert G.ESIK == 0.05 and G.T_END == 600.0
    assert G.KOLLAR[0.2] == "W2_Y10_g0p2" and G.KOLLAR[5.0] == "UG_Y10_g5p0"


def _ug(kok, b02, b1, b25, b5, t5=600.0):
    for g, b, t in ((0.2, b02, 600.0), (1.0, b1, 600.0), (2.5, b25, 600.0),
                    (5.0, b5, t5)):
        _npz(kok, G.KOLLAR[g], _egri(b, t), t_gecis=g)
    return G.yargi(G.topla(kok))


def test_UG_YAKINSAMIS_ve_uretim_EN_KUCUK_yeterli_t(tmp_path):
    out = _ug(tmp_path, 3.667, 4.07, 4.14, 4.16)
    assert out["genel"] == "GECIS YAKINSAMIS"
    assert out["uretim_t_gecis"] == 1.0          # |3,07-3,16|/3,16 = 0,028
    assert "sigma_gecis" not in out


def test_UG_YAKINSIYOR_uretim_5(tmp_path):
    out = _ug(tmp_path, 3.0, 3.6, 4.2, 4.5)
    assert out["genel"] == "YAKINSIYOR" and out["uretim_t_gecis"] == 5.0
    assert out["sigma_gecis"] == pytest.approx(0.3 / 3.2)


def test_UG_YAKINSAMA_YOK_uretim_belirlenemedi(tmp_path):
    out = _ug(tmp_path, 3.0, 3.2, 3.4, 4.2)
    assert out["genel"] == "YAKINSAMA YOK" and out["uretim_t_gecis"] is None


def test_UG_kisa_kol_OKUNMAZ(tmp_path):
    out = _ug(tmp_path, 3.0, 3.2, 3.4, 3.4, t5=450.0)
    assert out["genel"].startswith("OKUNMAZ") and out["kisa"] == ["5"]


def test_UG_CLI(tmp_path, capsys):
    _ug(tmp_path, 3.667, 4.07, 4.14, 4.16)
    yol = tmp_path / "S_UG.json"
    assert G.main(["--kok", str(tmp_path), "--json", str(yol)]) == 0
    d = json.loads(yol.read_text(encoding="utf-8"))
    assert d["genel"] == "GECIS YAKINSAMIS" and d["uretim_t_gecis"] == 1.0
    assert "uretim" in capsys.readouterr().out
