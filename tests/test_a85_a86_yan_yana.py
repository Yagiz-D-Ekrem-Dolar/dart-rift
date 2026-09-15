"""A85 (aralık yarım hücre), A87 (yamuk uç düğüm) ve A86 (sebepsiz krater `nan`).

Kilitli yargılar değişmez: P raporu eski `hdi68`/`hdi95` ile karar verir,
yamuk aralıklar `*_yamuk` alanlarına yazılır. `gozlem_vektoru` değerleri
bit-aynı kalır; yalnız istenirse sebep yazılır.
"""
from __future__ import annotations

import importlib
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))


def _yukle(ad):
    spec = importlib.util.spec_from_file_location(ad, _KOK / "scripts" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


pr = _yukle("p_kalibrasyon_raporu")
dg = _yukle("dart_gozlem_posterior")
gv = _yukle("gozlem_vektoru")
ps = _yukle("p_sekil_verisi")


class _SahtePost:
    """Tek eksenli kenar dağılımı; üç eksen aynı."""

    def __init__(self, m, n_eksen=3):
        self._m = np.asarray(m, float) / np.sum(m)
        e = np.linspace(0.0, 1.0, len(m))
        self.grid_u = (e,) * n_eksen
        self.hdi_u = np.array([[0.2, 0.4]] * n_eksen)
        self.width_u = self.hdi_u[:, 1] - self.hdi_u[:, 0]
        self.mean_u = np.full(n_eksen, 0.3)

    def marginal(self, j):
        return self._m

    def pinned(self, j):
        return False


# --------------------------------------------------------------------- A85
def test_yamuk_aralik_duz_dagilimda_TAM_eski_aralik_KAYIK():
    p = _SahtePost(np.ones(41))
    assert pr._aralik_yamuk(p, 0, 0.16, 0.84) == pytest.approx((0.16, 0.84), abs=1e-12)
    lo, hi = pr._aralik(p, 0, 0.16, 0.84)
    # A85: iki uç da sola kayık (41 düğümde alt uç 0,021, üst uç 0,004 u)
    assert lo < 0.16 - 0.01 and hi < 0.84


def test_yamuk_aralik_D_betigindeki_hesapla_AYNI():
    rng = np.random.default_rng(7)
    for _ in range(5):
        m = rng.gamma(2.0, size=33)
        p = _SahtePost(m)
        for a, b in ((0.16, 0.84), (0.025, 0.975)):
            assert pr._aralik_yamuk(p, 1, a, b) == pytest.approx(
                dg._orta_nokta_aralik(m / m.sum(), p.grid_u[1], a, b), abs=1e-14)


# --------------------------------------------------------------------- A87
@pytest.mark.parametrize("n", [5, 21, 41])
def test_A87_duz_dagilimda_UC_kantiller_de_TAM(n):
    """İlk yamuk sürümü iç kantillerde tamdı, uçlarda değil (21 düğümde 0,025 → 0,0167)."""
    e = np.linspace(0.0, 1.0, n)
    for q in np.linspace(0.001, 0.499, 37):
        assert dg._orta_nokta_aralik(np.ones(n), e, q, 1 - q) == pytest.approx(
            (q, 1 - q), abs=1e-12)
        assert ps.pit(np.ones(n), e, q) == pytest.approx(q, abs=1e-12)
    assert ps.pit(np.ones(n), e, 0.0) == 0.0 and ps.pit(np.ones(n), e, 1.0) == pytest.approx(1.0)


def test_A87_dogrusal_yogunlukta_DUGUMLERDE_birikim_TAM():
    """`p(u) = 2u` → `F(u) = u²`; yamuk kuralı doğrusal yoğunluğu düğümlerde tam integreler."""
    n = 21
    e = np.linspace(0.0, 1.0, n)
    for k in (1, 7, 19):
        q = e[k] ** 2
        assert dg._orta_nokta_aralik(2 * e, e, q, q)[0] == pytest.approx(e[k], abs=1e-12)
        assert ps.pit(2 * e, e, e[k]) == pytest.approx(q, abs=1e-12)


def test_vaka_yamuk_alanlarini_YANINA_yazar_kilitliler_ayni():
    p = _SahtePost(np.ones(21))
    v = pr._vaka(lambda y, c: p, [0.0], [0.5, 0.5, 0.5], 0, (1.0,))
    c = v["carpan"][1.0]
    assert c["hdi68"] == p.hdi_u.tolist()                             # kilitli: degismedi
    assert c["hdi95"][0] == pytest.approx(pr._aralik(p, 0, 0.025, 0.975))
    assert c["hdi68_yamuk"][0] == pytest.approx((0.16, 0.84), abs=1e-12)
    assert c["hdi95_yamuk"][2] == pytest.approx((0.025, 0.975), abs=1e-12)


def _vakalar(eski68, yamuk68, n=10, u=0.5):
    return [{"gercek_u": [u] * 3, "carpan": {1.0: {
        "hdi68": [eski68] * 3, "hdi95": [eski68] * 3,
        "hdi68_yamuk": [yamuk68] * 3, "hdi95_yamuk": [yamuk68] * 3,
        "genislik": [eski68[1] - eski68[0]] * 3, "cakili": [False] * 3}}} for _ in range(n)]


def test_eksen_yargisi_kilitli_karar_DEGISMEZ_yamuk_karar_YANINDA():
    y = pr.eksen_yargisi(_vakalar([0.40, 0.495], [0.41, 0.505]), 0)
    assert y["kapsama68"] == 0.0 and y["karar"] == "ASIRI GUVENLI"     # kilitli hesap
    assert y["kapsama68_yamuk"] == 1.0 and y["karar_yamuk"] == "COZULUYOR (TEMKINLI)"
    assert y["medyan_genislik_yamuk"] == pytest.approx(0.095)


def test_eski_JSON_vakalarinda_yamuk_alan_YOK_ve_hata_yok():
    v = _vakalar([0.4, 0.6], [0.4, 0.6])
    for x in v:
        del x["carpan"][1.0]["hdi68_yamuk"], x["carpan"][1.0]["hdi95_yamuk"]
    y = pr.eksen_yargisi(v, 0)
    assert y["karar"] == "COZULUYOR (TEMKINLI)" and "karar_yamuk" not in y


# --------------------------------------------------------------------- A86
def _sahte_durum(n=6):
    z = np.zeros((n, 3))
    return {"mermi_kesri": np.zeros(n), "m": np.ones(n), "R": 1.0, "x": z, "v": z,
            "ehat": np.array([0.0, 0.0, 1.0]), "p_imp": 1.0, "x_referans": z}


@pytest.fixture
def _sahte_operatorler(monkeypatch):
    # `dartrift.observables` paketi `momentum_transfer` adli FONKSIYONU disa
    # aktariyor: `import ... as mt` modul yerine onu getiriyordu (ilk surum
    # AttributeError verdi). Modulleri sys.modules uzerinden al.
    cs = importlib.import_module("dartrift.observables.crater_shape")
    md = importlib.import_module("dartrift.observables.momentum_defteri")
    mt = importlib.import_module("dartrift.observables.momentum_transfer")

    def krater(d):
        raise ValueError("eksen isininda yuzey bulunamadi (pencere: 79,5..91,0 m)")

    monkeypatch.setattr(cs, "krater_yuzey_durumdan", krater)
    monkeypatch.setattr(md, "momentum_defteri", lambda *a, **k: {
        "beta_hedef": 1.49, "M_ejekta": 2.0, "P_ejekta_eksenel": 3.0})
    monkeypatch.setattr(mt, "escape_speed", lambda M, R: 0.1)
    return cs


def test_A86_krater_istisnasinin_SEBEBI_yaziliyor_degerler_BIT_AYNI(_sahte_operatorler):
    eski = gv.gozlem_vektoru(_sahte_durum())
    sebep = {}
    yeni = gv.gozlem_vektoru(_sahte_durum(), sebepler=sebep)
    assert sebep["krater"].startswith("ValueError: eksen isininda yuzey bulunamadi")
    assert eski.keys() == yeni.keys() == set(gv.GOZLEMLER)
    for k in gv.GOZLEMLER:
        a, b = eski[k], yeni[k]
        assert (math.isnan(a) and math.isnan(b)) or a == b, k
    assert math.isnan(yeni["V_krater"]) and yeni["beta_hedef"] == 1.49


def test_A86_basarili_krater_TAMAM_yazar(monkeypatch, _sahte_operatorler):
    class _K:
        derinlik_merkez, derinlik, hacim, yaricap, hacim_degisimi = 3.69, 4.0, 51.8, 2.8, 0.1

    monkeypatch.setattr(_sahte_operatorler, "krater_yuzey_durumdan", lambda d: _K())
    sebep = {}
    out = gv.gozlem_vektoru(_sahte_durum(), sebepler=sebep)
    assert sebep == {"krater": "TAMAM"} and out["V_krater"] == 51.8
