"""Sayısal geçerlilik ↔ fizik tanıları AYRI (uzman Soru 11)."""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from dartrift.observables.gecerlilik import (
    AKMA_TAVANI,
    ENERJI_BAYRAK_ESIGI,
    fizik_tanilari,
    kutle_agirlikli_yuzdelik,
    sayisal_gecerlilik,
)


def _st(n=10):
    rng = np.random.default_rng(0)
    return {"x": rng.normal(size=(n, 3)), "v": rng.normal(size=(n, 3)),
            "u": np.ones(n), "rho": np.full(n, 1500.0), "P": np.zeros(n),
            "S": np.zeros((n, 3, 3))}


def _kw(**deg):
    kw = dict(st=_st(), t=0.024, t_end=0.024,
              enerji={"e_tot_bagil_sapma": -0.02},
              akma_tani={"oran_max": 1.0}, akma_kipi="ara",
              defter={"artik_bagil": 1e-14})
    kw.update(deg)
    return kw


def test_saglikli_kosu_GECERLI():
    g = sayisal_gecerlilik(**_kw())
    assert g["gecerli"] and all(g["kontroller"].values())


@pytest.mark.parametrize("bozuk, anahtar", [
    ({"t": 0.02}, "tamamlandi"),
    ({"enerji": {"e_tot_bagil_sapma": -0.10}}, "enerji"),
    ({"akma_tani": {"oran_max": 1.5}}, "kurucu_sinir"),
    ({"defter": {"artik_bagil": 1e-2}}, "momentum_defteri"),
])
def test_her_kontrol_KENDI_basina_dusurebiliyor(bozuk, anahtar):
    g = sayisal_gecerlilik(**_kw(**bozuk))
    assert not g["gecerli"]
    assert [k for k, v in g["kontroller"].items() if not v] == [anahtar]


def test_NaN_sonlu_kontrolunu_dusuruyor():
    st = _st()
    st["v"][3, 1] = np.nan
    g = sayisal_gecerlilik(**_kw(st=st))
    assert g["kontroller"]["sonlu"] is False


def test_son_kipinde_kurucu_sinir_DURUSTCE_false():
    """A72: `son` kipinde kuvvet anında aşım tasarım gereği var."""
    g = sayisal_gecerlilik(**_kw(akma_tani={"oran_max": 1966.0},
                                 akma_kipi="son"))
    assert g["kontroller"]["kurucu_sinir"] is False
    assert g["degerler"]["q_bolu_Y_max"] == 1966.0


def test_esikler_KAYITTA():
    g = sayisal_gecerlilik(**_kw())
    assert g["esikler"]["enerji"] == ENERJI_BAYRAK_ESIGI
    assert g["esikler"]["akma"] == AKMA_TAVANI


def test_kutle_agirlikli_yuzdelik():
    d = np.array([1.0, 2.0, 3.0, 4.0])
    w = np.array([1.0, 1.0, 1.0, 97.0])
    assert kutle_agirlikli_yuzdelik(d, w, 50.0) == 4.0     # agir parcacik
    assert kutle_agirlikli_yuzdelik(d, np.ones(4), 50.0) == 2.0


def test_fizik_tanilari_KAPI_icermiyor_ve_egriyi_tasiyor():
    f = fizik_tanilari(rho_zirve=np.array([2000.0, 2600.0]),
                       alpha0_hedef=np.array([1.3, 1.3]),
                       m_hedef=np.array([1.0, 3.0]),
                       defter={"beta_hedef": 1.2, "M_ejekta": 5.0},
                       enerji={"bas": {"e_tot": 10.0},
                               "son": {"e_kin": 4.0, "e_int": 5.8}},
                       impuls_egrisi=[[0.01, 0.5], [0.02, 0.9]])
    assert "gecerli" not in f
    assert f["zirve_sikisma_max_yuzde"] == pytest.approx(100 * (2600 * 1.3 / 2700 - 1))
    assert f["impuls_egrisi"][-1] == [0.02, 0.9]
    assert f["enerji_bolusumu"]["kinetik_kesri"] == pytest.approx(0.4)


def test_ileri_model_iki_kaydi_AYRI_yaziyor():
    from dartrift.inference import forward as F

    k = inspect.getsource(F.ileri_kosu_merdiven)
    assert "gecerlilik=json.dumps(gecerlilik)" in k
    assert "fizik_tani=json.dumps(fizik_tani)" in k
    assert "impuls.append" in k
    assert F.IMPULS_ORNEK == 50
