"""Protokol W raporu — kilitli kural (koşudan önce yazıldı) sınavları."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import w_kiyas_raporu as W  # noqa: E402


def _npz(dizin: Path, ad: str, beta: float, *, gecerli=True, beta_km=None,
         gecis_adimi=12):
    d = dizin / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    ft = {"beta_hedef": beta, "M_ejekta": 1.0e6,
          "beta_iki_yontem": {"beta_km": beta if beta_km is None else beta_km,
                              "mermi_bagsiz_kesri": 0.01,
                              "koni_tam_acisi_derece": 120.0},
          "gec_evre": {"adim_gecis": gecis_adimi, "A_gec": 1.0e5},
          "dondurulmus": 3}
    gc = {"gecerli": gecerli,
          "degerler": {"t": 600.0, "e_tot_bagil_sapma": -0.01}}
    np.savez(d / "nokta_0000_abc.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps(gc))


def _kampanya(tmp: Path, betalar: dict, **kw):
    """`betalar = {(Y0, t_gecis): beta}`."""
    for (y0, tg), b in betalar.items():
        _npz(tmp, f"W_Y{y0:g}_g{tg:g}_kaba_sahne1".replace(".", "p"), b, **kw)
    return tmp


def _ad(y0, tg):
    return (y0, tg)


def test_L1_TABLOSU_kodda_kilitli():
    assert W.L1_BETA == {50.0: 3.63, 10.0: 4.18, 1.0: 4.66}
    assert W.ORAN_ALT == 0.5 and W.ORAN_UST == 2.0
    assert W.SAGLAMLIK_ESIGI == 0.20
    assert W.T_GECIS == (0.2, 1.0)


def test_TUTTU_L1_degerleri_birebir_verilince(tmp_path):
    b = {}
    for y0, bl in W.L1_BETA.items():
        for tg in W.T_GECIS:
            b[_ad(y0, tg)] = bl
    v = W.topla(_kampanya(tmp_path, b))
    out = W.yargi(v)
    out.update(W.kapsam(v))
    assert out["genel"] == "KIYAS TUTTU"
    assert out["egilim"] and out["saglamlik"] and out["tam"]
    assert all(abs(s["oran"] - 1.0) < 1e-9 for s in out["satirlar"].values())


def test_FAKTOR_IKI_bandinin_ICI_ve_DISI(tmp_path):
    # her Y0'da (beta-1) L1'in 0,55 kati -> bandda
    b = {_ad(y, t): 1.0 + 0.55 * (W.L1_BETA[y] - 1.0)
         for y in W.L1_BETA for t in W.T_GECIS}
    out = W.yargi(W.topla(_kampanya(tmp_path, b)))
    assert out["genel"] == "KIYAS TUTTU", out
    # 0,45 kati -> uc satir da DUSUK -> TUTMADI
    b2 = {_ad(y, t): 1.0 + 0.45 * (W.L1_BETA[y] - 1.0)
          for y in W.L1_BETA for t in W.T_GECIS}
    out2 = W.yargi(W.topla(_kampanya(tmp_path / "b2", b2)))
    assert out2["genel"].startswith("TUTMADI"), out2
    assert out2["egilim"]


def test_EGILIM_bozulunca_TUTMADI(tmp_path):
    b = {_ad(50.0, t): 4.5 for t in W.T_GECIS}
    b.update({_ad(10.0, t): 3.5 for t in W.T_GECIS})
    b.update({_ad(1.0, t): 3.0 for t in W.T_GECIS})
    out = W.yargi(W.topla(_kampanya(tmp_path, b)))
    assert not out["egilim"]
    assert out["genel"].startswith("TUTMADI")


def test_TEK_satir_band_disi_KISMI(tmp_path):
    b = {}
    for y0, bl in W.L1_BETA.items():
        for tg in W.T_GECIS:
            b[_ad(y0, tg)] = bl
    b[_ad(50.0, W.T_GECIS[0])] = 1.0 + 0.3 * (W.L1_BETA[50.0] - 1.0)
    b[_ad(50.0, W.T_GECIS[1])] = 1.0 + 0.3 * (W.L1_BETA[50.0] - 1.0)
    out = W.yargi(W.topla(_kampanya(tmp_path, b)))
    assert out["genel"].startswith("KISMI"), out
    assert out["egilim"]


def test_SAGLAMLIK_gecis_anina_duyarliysa_KIYAS_TUTMUYOR(tmp_path):
    b = {}
    for y0, bl in W.L1_BETA.items():
        b[_ad(y0, 0.2)] = bl
        b[_ad(y0, 1.0)] = 1.0 + 1.5 * (bl - 1.0)      # %50 fark
    out = W.yargi(W.topla(_kampanya(tmp_path, b)))
    assert not out["saglamlik"]
    assert out["genel"].startswith("KISMI")


def test_GECERSIZ_kosu_OKUNMAZ_ve_kapsam_EKSIK(tmp_path):
    b = {_ad(y, t): W.L1_BETA[y] for y in W.L1_BETA for t in W.T_GECIS}
    v = W.topla(_kampanya(tmp_path, b, gecerli=False))
    out = W.yargi(v)
    out.update(W.kapsam(v))
    assert out["genel"].startswith("OKUNMAZ")
    assert out["tam"] is False and len(out["gecersiz"]) == 6


def test_EKSIK_kosu_kapsamda_YAZILIYOR(tmp_path):
    b = {_ad(y, W.T_GECIS[0]): W.L1_BETA[y] for y in W.L1_BETA}
    v = W.topla(_kampanya(tmp_path, b))
    k = W.kapsam(v)
    assert k["tam"] is False
    assert sorted(k["eksik"]) == sorted(["Y1:g1", "Y10:g1", "Y50:g1"])


def test_TANI_alanlari_rapora_giriyor(tmp_path):
    b = {_ad(y, t): W.L1_BETA[y] for y in W.L1_BETA for t in W.T_GECIS}
    out = W.yargi(W.topla(_kampanya(tmp_path, b, beta_km=2.5)))
    s = out["satirlar"]["Y10"]
    assert s["beta_km"] == pytest.approx(2.5)
    assert s["koni_tam_acisi_derece"] == pytest.approx(120.0)
    assert s["dondurulmus"] == 3


def test_CLI_json_yaziyor(tmp_path, capsys):
    b = {_ad(y, t): W.L1_BETA[y] for y in W.L1_BETA for t in W.T_GECIS}
    _kampanya(tmp_path, b)
    yol = tmp_path / "S_W.json"
    assert W.main(["--kok", str(tmp_path), "--json", str(yol)]) == 0
    veri = json.loads(yol.read_text(encoding="utf-8"))
    assert veri["genel"] == "KIYAS TUTTU"
    assert "KIYAS TUTTU" in capsys.readouterr().out
