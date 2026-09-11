"""Protokol L raporu — **sonuçlardan önce** sınanır.

Eşikler koşudan önce kilitlendi. Sınavlar, raporun bilinen doğrusal
modellerde doğru tekil değerleri ve doğru yargıyı verdiğini gösteriyor.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))


def _yukle(ad):
    spec = importlib.util.spec_from_file_location(ad, _KOK / "scripts" / f"{ad}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dr = _yukle("duyarlilik_raporu")
gv = _yukle("gozlem_vektoru")


def test_esikler_protokol_metniyle_AYNI():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-L-DUYARLILIK.md").read_text(
        encoding="utf-8")
    assert dr.AYIRT_ESIGI == 2.0 and "`≥ 2`" in m
    assert dr.ZAYIF_ESIGI == 1.0 and "`1 – 2`" in m
    assert dr.TUREV_TEKRAR_ESIGI == 0.5 and "`> 0,5`" in m
    assert dr.EN_AZ_GERCEKLEME == 4 and "`≥ 4`" in m


def test_tasarim_ONSEL_icinde_ve_simetrik():
    from dartrift.inference.design import DART_UZAYI_S3 as U

    t = dr.tasarim()
    assert len(t) == 7 and "merkez" in t
    lo, hi = np.asarray(U.lo), np.asarray(U.hi)
    for th in t.values():
        assert np.all(np.asarray(th) >= lo) and np.all(np.asarray(th) <= hi)
    a, y, f = t["merkez"]
    assert t["log10_Y0+"][1] == pytest.approx(10 ** (np.log10(y) + 0.5))
    assert t["boulder_alpha0-"][0] == pytest.approx(a - 0.075)
    assert t["f_boulder+"][2] == pytest.approx(f + 0.075)


def _sentetik(A, sigma, *, tohumlar=("s0", "s1"), n_merkez=6, gurultu=0.0,
              tohum=0, tohum_farki=None):
    """`y = A · u + ε`, `u` birim-ölçekli parametre sapması."""
    rng = np.random.default_rng(tohum)
    A = np.asarray(A, float)
    k = A.shape[0]
    g = {}
    for i in range(n_merkez):
        g[("merkez", f"m{i}")] = rng.normal(0.0, sigma, k)
    for t_i, t in enumerate(tohumlar):
        B = A if tohum_farki is None or t_i == 0 else A * tohum_farki
        for j, ad in enumerate(dr.EKSENLER):
            for isr in (+1, -1):
                u = np.zeros(3)
                u[j] = isr
                g[(ad + ("+" if isr > 0 else "-"), t)] = (
                    B @ u + rng.normal(0.0, gurultu, k))
    return g


def test_bilinen_dogrusal_modelde_tekil_degerler_GERI_KAZANILIYOR():
    A = np.array([[4.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 2.5],
                  [1.0, 1.0, 1.0]])
    sigma = np.ones(4)
    J = dr.jakobiyen(_sentetik(A, 0.0), sigma)["J"]
    np.testing.assert_allclose(J, A, atol=1e-12)
    y = dr.yargi(J, [0.0, 0.0, 0.0])
    np.testing.assert_allclose(y["tekil"], np.linalg.svd(A, compute_uv=False))
    assert y["karar"] == "UC EKSEN AYRISIYOR"


def test_tek_eksene_duyarli_gozlemde_TEK_YON():
    A = np.array([[0.0, 5.0, 0.0], [0.0, 3.0, 0.0], [0.0, 1.0, 0.0]])
    y = dr.yargi(dr.jakobiyen(_sentetik(A, 0.0), np.ones(3))["J"], [0, 0, 0])
    assert y["karar"] == "TEK YON"
    # zayif yon Y0 eksenine DIK olmali
    assert abs(y["zayif_yon"][1]) < 1e-9


def test_esik_SINIRLARI():
    for s3, beklenen in ((2.0, "UC EKSEN AYRISIYOR"), (1.999, "IKI YON")):
        y = dr.yargi(np.diag([5.0, 3.0, s3]), [0, 0, 0])
        assert y["karar"] == beklenen
    y = dr.yargi(np.diag([5.0, 1.5, 0.5]), [0, 0, 0])
    assert y["etiket"] == ["AYIRT EDILEBILIR", "ZAYIF", "GURULTU ALTINDA"]


def test_turev_tohumlar_arasi_TUTARSIZSA_isaretleniyor():
    A = np.diag([4.0, 3.0, 2.5])
    g = _sentetik(A, 0.0, tohum_farki=np.array([[1, 1, 1], [1, 1, 1],
                                                [1, 1, 3.0]]).T)
    jk = dr.jakobiyen(g, np.ones(3))
    y = dr.yargi(jk["J"], jk["tekrar"])
    assert "f_boulder" in y["turev_gurultude"]
    assert "log10_Y0" not in y["turev_gurultude"]


def test_az_gerceklemede_OKUNMAZ():
    A = np.diag([4.0, 3.0, 2.5])
    r = dr.rapor(_sentetik(A, 1.0, n_merkez=3), ["a", "b", "c"])
    assert r["karar"] == "OKUNMAZ" and "gerceklemesi" in r["sebep"]


def test_sabit_gozlem_DUSURULUYOR_ve_yaziliyor():
    A = np.array([[4.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 2.5],
                  [0.0, 0.0, 0.0]])
    g = _sentetik(A, 1.0, gurultu=0.0)
    for k in g:
        g[k][3] = 7.0                         # hic degismeyen gozlem
    r = dr.rapor(g, ["a", "b", "c", "sabit"])
    assert "sabit" in r["dusen_gozlemler"]
    assert r["gozlemler"] == ["a", "b", "c"]


def test_beyazlatma_GURULTUYE_bolunuyor():
    A = np.diag([4.0, 4.0, 4.0])
    y1 = dr.yargi(dr.jakobiyen(_sentetik(A, 0.0), np.full(3, 1.0))["J"], [0] * 3)
    y2 = dr.yargi(dr.jakobiyen(_sentetik(A, 0.0), np.full(3, 4.0))["J"], [0] * 3)
    assert y1["tekil"][2] == pytest.approx(4.0)
    assert y2["tekil"][2] == pytest.approx(1.0)
    assert y2["karar"] == "HICBIR YON"


def test_tasarim_dosyasi_yazimi(tmp_path):
    p = tmp_path / "t.json"
    dr.main(["--kok", str(tmp_path), "--kol", "x", "--tasarim-yaz", str(p)])
    d = json.loads(p.read_text())
    assert len(d["theta"]) == 7 and d["adlar"][0] == "merkez"
    dr.main(["--kok", str(tmp_path), "--kol", "x", "--tasarim-yaz", str(p),
             "--sadece-merkez"])
    assert len(json.loads(p.read_text())["theta"]) == 1


# --- ejekta egimi --------------------------------------------------------

def test_ejekta_egimi_BILINEN_us_yasayi_geri_kazaniyor():
    """`M(>v) ∝ v^(-3μ)`, `μ = 0,45` — ters dönüşümle örneklenmiş hızlar."""
    rng = np.random.default_rng(1)
    n = 20000
    mu, v_esc = 0.45, 0.1
    v = v_esc * (1.0 - rng.random(n)) ** (-1.0 / (3.0 * mu))
    yon = rng.normal(size=(n, 3))
    yon /= np.linalg.norm(yon, axis=1)[:, None]
    x0 = 50.0 * yon
    x = x0 + 0.5 * yon                     # disari cikmis
    vv = v[:, None] * yon
    m = np.ones(n)
    assert gv.ejekta_egimi(x, vv, m, x0, v_esc=v_esc) == pytest.approx(mu, abs=0.03)


def test_ejekta_yoksa_egim_TANIMSIZ():
    x0 = np.random.default_rng(2).normal(size=(100, 3))
    assert np.isnan(gv.ejekta_egimi(x0, np.zeros_like(x0), np.ones(100), x0,
                                    v_esc=0.1))
