"""A114 — isteğe bağlı gözlemli: krater ölçülemediğinde `β` yaşar.

Varsayılan davranış **değişmedi**: `istege_bagli` / `nan_izinli` boşken tek
bir `nan` hâlâ bütün kaydı düşürür (S4'ün dersi korunuyor).
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from dartrift.inference import forward as F
from dartrift.inference.ensemble import ensemble_kos


def test_GOZLENEBILIRLER_sirasi_kilitli():
    assert F.GOZLENEBILIRLER == ("beta", "krater_derinlik", "ejekta_kutle_kesri")


def _ileri(y):
    return lambda th: np.asarray(y, dtype=np.float64)


def test_varsayilan_tek_nan_butun_kaydi_DUSURUR(tmp_path):
    yol = tmp_path / "a.jsonl"
    d = ensemble_kos(np.zeros((1, 3)), _ileri([3.7, np.nan, 0.006]), yol,
                     root_seed=1, surum="x")
    assert d.dusen == 1 and d.tamamlanan == 0
    kayit = json.loads(yol.read_text(encoding="utf-8").strip())
    assert kayit["y"] is None and "ZORUNLU" in kayit["hata"]


def test_nan_izinli_ile_beta_ve_ejekta_YASIYOR(tmp_path):
    yol = tmp_path / "b.jsonl"
    d = ensemble_kos(np.zeros((1, 3)), _ileri([3.7, np.nan, 0.006]), yol,
                     root_seed=1, surum="x", nan_izinli=(1,))
    assert d.dusen == 0 and d.tamamlanan == 1
    kayit = json.loads(yol.read_text(encoding="utf-8").strip())
    assert kayit["y"][0] == pytest.approx(3.7)      # beta yasadi
    assert kayit["y"][2] == pytest.approx(0.006)    # ejekta kesri yasadi
    assert kayit["y"][1] is None or np.isnan(float(kayit["y"][1]))


def test_nan_izinli_ZORUNLU_bileseni_kurtarmaz(tmp_path):
    """`β` `nan` ise kayıt düşer — `nan_izinli` krateri kapsıyor olsa bile."""
    d = ensemble_kos(np.zeros((1, 3)), _ileri([np.nan, 5.0, 0.006]),
                     tmp_path / "c.jsonl", root_seed=1, surum="x",
                     nan_izinli=(1,))
    assert d.dusen == 1 and d.tamamlanan == 0


def test_nan_izinli_dizini_denetleniyor(tmp_path):
    d = ensemble_kos(np.zeros((1, 3)), _ileri([3.7, 5.0, 0.006]),
                     tmp_path / "d.jsonl", root_seed=1, surum="x",
                     nan_izinli=(7,))
    assert d.dusen == 1                      # ValueError kayda yazildi
    kayit = json.loads((tmp_path / "d.jsonl").read_text(encoding="utf-8").strip())
    assert "aralik disi" in kayit["hata"]


def test_krater_reddi_ISTEGE_BAGLI_degilse_yukseliyor(monkeypatch):
    """`istege_bagli` boşken krater reddi `gozlenebilirleri_cikar`'dan geçer."""
    import dartrift.observables.crater_shape as CS

    def red(*a, **kw):
        raise ValueError("carpma ekseni kutusunda 3 parcacik var")
    monkeypatch.setattr(CS, "crater_profile", red)
    with pytest.raises(ValueError, match="carpma ekseni"):
        _cagir(istege_bagli=())


def test_krater_reddi_ISTEGE_BAGLI_ise_nan_olup_gerekce_KAYDA_giriyor(monkeypatch):
    import dartrift.observables.crater_shape as CS

    def red(*a, **kw):
        raise ValueError("carpma ekseni kutusunda 3 parcacik var")
    monkeypatch.setattr(CS, "crater_profile", red)
    F.A114_UYARILARI.clear()
    y = _cagir(istege_bagli=("krater_derinlik",))
    assert np.isfinite(y[0]) and np.isnan(y[1]) and np.isfinite(y[2])
    assert len(F.A114_UYARILARI) == 1
    assert "carpma ekseni" in F.A114_UYARILARI[0]
    F.A114_UYARILARI.clear()


def _cagir(*, istege_bagli):
    """Küçük sentetik son durum — yalnız gözlemli çıkarıcıyı sınar."""
    rng = np.random.default_rng(7)
    n = 400
    yon = rng.normal(size=(n, 3))
    yon /= np.linalg.norm(yon, axis=1, keepdims=True)
    x0 = yon * 80.0
    st = {"x": x0 + rng.normal(scale=0.1, size=(n, 3)),
          "v": rng.normal(scale=0.01, size=(n, 3)),
          "m": np.full(n, 1.0e7), "rho": np.full(n, 2300.0)}
    return F.gozlenebilirleri_cikar(
        st, impactor_momentum=np.array([0.0, 0.0, 3.56e6]),
        target_mass=4.3e9, target_radius=80.0,
        is_impactor=np.zeros(n, dtype=bool),
        impact_direction=np.array([0.0, 0.0, -1.0]), x_reference=x0,
        krater_ayarlari=F.KRATER_AYARLARI_DART, istege_bagli=istege_bagli)
