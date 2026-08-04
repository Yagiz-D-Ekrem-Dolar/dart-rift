"""D-2 kalibrasyon aracının denetimi (GPU gerekmez).

Piston başlangıç koşulu ve eşleme mantığı CPU'da tam sınanabilir; koşunun
kendisi GPU ister. Asıl risk, KAYIT-029'un tekrarıdır: **az örneklenmiş**
bir noktadan yargı kurmak.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.deposit_calibration import build_piston_ic, calibrate
from dartrift.validation.sedov import E_INJECT

DEP = [{"r_deposit": d, "r_measured": r} for d, r in
       [(0.025, 0.22389), (0.030, 0.22585), (0.040, 0.23053),
        (0.050, 0.23499), (0.060, 0.23755), (0.080, 0.24023)]]


def test_piston_enerjisi_biriktirmeyle_AYNI() -> None:
    """İki kol **aynı enerjiyi** taşımazsa kıyas anlamsızdır."""
    for rp in (0.025, 0.050, 0.070):
        ic = build_piston_ic(128, rp)
        assert ic["energy_matches"] is True
        assert ic["kinetic_energy"] == pytest.approx(E_INJECT, rel=1e-12)


def test_piston_hizi_yalnizca_ICERIDE() -> None:
    """Piston dışında hız **tam sıfır** olmalı; sızarsa enerji dağılır."""
    ic = build_piston_ic(64, 0.06)
    r = np.linalg.norm(ic["x"], axis=1)
    dis = r >= 0.06
    assert np.all(ic["v"][dis] == 0.0)
    # Ve icerisi GERCEKTEN hareketli olmali (bos test olmasin).
    assert np.max(np.linalg.norm(ic["v"][~dis], axis=1)) > 0.0


def test_hiz_homolog() -> None:
    """`v = c·x` — yön radyal, büyüklük `r` ile doğrusal."""
    ic = build_piston_ic(64, 0.06)
    r = np.linalg.norm(ic["x"], axis=1)
    icr = r < 0.06
    v = np.linalg.norm(ic["v"][icr], axis=1)
    c = v / r[icr]
    assert float(np.ptp(c)) < 1.0e-12 * float(np.mean(c))


def test_ornekleme_bayragi_KAYIT029_dersini_uyguluyor() -> None:
    """`n < 100` "iyi örneklenmiş" **sayılmamalı** — KAYIT-029'un dersi."""
    az = build_piston_ic(64, 0.030)          # olculdu: 32 parcacik
    cok = build_piston_ic(128, 0.025)        # olculdu: 136 parcacik
    assert az["n_piston"] < 100 and az["piston_well_sampled"] is False
    assert cok["n_piston"] >= 100 and cok["piston_well_sampled"] is True


def test_az_orneklenmis_piston_TASINABILIR_dedirtemez() -> None:
    """Eşleme mükemmel olsa bile az örneklenmişse `transferable` **False**."""
    iyi = [{"r_piston": 0.030, "r_measured": 0.2270, "well_sampled": True},
           {"r_piston": 0.060, "r_measured": 0.2370, "well_sampled": True}]
    az = [dict(p, well_sampled=False) for p in iyi]
    assert calibrate(iyi, DEP)["transferable"] is True
    assert calibrate(az, DEP)["transferable"] is False


def test_ayirt_etmeyen_kollar_TASINABILIR_dedirtemez() -> None:
    """BOŞLUK KONTROLÜ: piston `R` ile değişmiyorsa eşleme anlamsızdır."""
    duz = [{"r_piston": 0.030, "r_measured": 0.2300, "well_sampled": True},
           {"r_piston": 0.060, "r_measured": 0.2300, "well_sampled": True}]
    c = calibrate(duz, DEP)
    assert c["piston_discriminates"] is False
    assert c["transferable"] is False


def test_aralik_disi_EKSTRAPOLASYON_isaretleniyor() -> None:
    disarida = [{"r_piston": 0.030, "r_measured": 0.2000, "well_sampled": True},
                {"r_piston": 0.060, "r_measured": 0.2370, "well_sampled": True}]
    c = calibrate(disarida, DEP)
    assert c["rows"][0]["in_bracket"] is False
    assert c["rows"][1]["in_bracket"] is True
    assert c["n_in_bracket"] == 1
    assert c["transferable"] is False        # 2'den az nokta aralikta


def test_gecersiz_girdi_reddediliyor() -> None:
    with pytest.raises(ValueError, match="r_piston"):
        build_piston_ic(64, 0.7)
    with pytest.raises(ValueError, match="çok küçük"):
        build_piston_ic(64, 0.005)
    with pytest.raises(ValueError, match="en az 2 piston"):
        calibrate([{"r_piston": 0.03, "r_measured": 0.23}], DEP)
