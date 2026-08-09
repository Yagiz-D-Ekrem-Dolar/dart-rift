"""`sure_denetimi` — `~3` saatlik bir GPU koşusunu koruyan kapı.

Sınanan asıl şey: **bilinmeyen `yeterli` sayılmıyor.** Denetim
yapılamadığında sonuç `denetlenemedi`; `kisa_kosu` `False` **değil**,
`None`.
"""
from __future__ import annotations

import pytest

from dartrift.validation.kosu_suresi import DURUM, sure_denetimi

#: FAZ 4.5 benzeri çıktı: 8000 adımda 0,2 s → `dt = 2,5e-5 s`.
_F45 = {"t_sim_end": 0.2, "steps_done": 8000,
        "beta_bound_settling_time_s": 0.15,
        "beta_bound_settling_diag": {"sabit": False, "durulmus": True}}


# ------------------------------------------------------- normal iki hal

def test_kisa_kosu_yakalaniyor_ve_gereken_adim_soyleniyor():
    d = sure_denetimi(_F45, steps=3000)          # 0,075 s < 0,15 s
    assert d["durum"] == "kisa" and d["kisa_kosu"] is True
    assert d["onerilen_steps"] == 6000           # ceil(0,15 / 2,5e-5)
    assert "durulmadan bitiyor" in d["neden"]


def test_yeterli_kosu_geciyor():
    d = sure_denetimi(_F45, steps=7000)          # 0,175 s >= 0,15 s
    assert d["durum"] == "yeterli" and d["kisa_kosu"] is False


def test_onerilen_adim_GERCEKTEN_yetiyor():
    """Önerilen sayı sınırda kalıp yine `kisa` demezse öneri işe yaramaz."""
    d = sure_denetimi(_F45, steps=3000)
    assert sure_denetimi(_F45, steps=d["onerilen_steps"])["durum"] == "yeterli"


@pytest.mark.parametrize("steps,bekle", [(5999, "kisa"), (6000, "yeterli"),
                                         (6001, "yeterli")])
def test_esik_kenari(steps, bekle):
    assert sure_denetimi(_F45, steps=steps)["durum"] == bekle


# ------------------------- BILINMEYEN `yeterli` SAYILMIYOR (asil sinav)

@pytest.mark.parametrize("faz45,parca", [
    (None, "verilmedi"),
    ({}, "verilmedi"),
    ({"t_sim_end": 0.2, "steps_done": 8000,
      "beta_bound_settling_diag": {"sabit": True}}, "SABİT"),
    ({"t_sim_end": 0.2, "steps_done": 8000,
      "beta_bound_settling_time_s": float("nan")}, "durulmadı"),
    ({"t_sim_end": 0.2, "steps_done": 8000}, "durulmadı"),
    ({"beta_bound_settling_time_s": 0.15}, "t_sim_end"),
    ({"beta_bound_settling_time_s": 0.15, "t_sim_end": 0.2}, "steps_done"),
])
def test_denetlenemeyen_haller_YETERLI_demiyor(faz45, parca):
    d = sure_denetimi(faz45, steps=3000)
    assert d["durum"] == "denetlenemedi"
    assert d["kisa_kosu"] is None            # <-- False DEGIL
    assert parca in d["neden"], d["neden"]


def test_sifir_adim_orani_yakalaniyor():
    d = sure_denetimi({"t_sim_end": 0.0, "steps_done": 8000,
                       "beta_bound_settling_time_s": 0.15}, steps=3000)
    assert d["durum"] == "denetlenemedi"


def test_durum_her_zaman_bilinen_kumede():
    for f in (None, _F45, {"t_sim_end": 0.2, "steps_done": 8000}):
        assert sure_denetimi(f, steps=3000)["durum"] in DURUM


def test_gecersiz_steps():
    with pytest.raises(ValueError, match="pozitif"):
        sure_denetimi(_F45, steps=0)


# ----------------------------------------------- oran TAHMIN EDILMIYOR

def test_adim_zaman_orani_FAZ45ten_okunuyor():
    """Farklı `dt`'li bir sahne farklı karar vermeli — sabit varsayılmıyor."""
    yavas = dict(_F45, t_sim_end=0.4)        # dt iki kat buyuk
    assert sure_denetimi(_F45, steps=4000)["durum"] == "kisa"
    assert sure_denetimi(yavas, steps=4000)["durum"] == "yeterli"
    assert sure_denetimi(yavas, steps=4000)["dt_ort_s"] == pytest.approx(5.0e-5)
