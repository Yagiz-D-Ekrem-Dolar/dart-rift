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

# TRUBA is 1451309 (D-2, n_side=128) GERCEK olculen biriktirme kolu.
DEP = [{"r_deposit": d, "r_measured": r, "kinetic_fraction": k}
       for d, r, k in
       [(0.025, 0.22389, 0.13175), (0.030, 0.22585, 0.13606),
        (0.040, 0.23053, 0.14684), (0.050, 0.23499, 0.15688),
        (0.060, 0.23755, 0.16755), (0.080, 0.24023, 0.18908)]]

# Ayni kosunun piston kolu.
PIS = [{"r_piston": R, "r_measured": rs, "kinetic_fraction": kp,
        "well_sampled": True}
       for R, rs, kp in [(0.0250, 0.23247, 0.17313), (0.0350, 0.23559, 0.18814),
                         (0.0500, 0.24354, 0.20930), (0.0700, 0.25088, 0.21813)]]


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


def test_gercek_olcum_TASINABILIR_DEGIL() -> None:
    """D-2'nin gerçek sonucu (KAYIT-030): **taşınabilir değil**, iki sebeple.

    1. Dört pistonun **ikisi** biriktirme aralığının **dışında** kaldı;
       `np.interp` onları uç değere **kelepçeler** ve `1,60` / `1,14` gibi
       **uydurma** oranlar üretirdi. Aralık dışında oran artık `NaN`.
    2. Şok yarıçapı eşleşirken **kinetik enerji kesri %14,5–18,0 ayrışıyor** —
       tek parametreli kalibrasyon iki gözlenebiliri **aynı anda eşlemiyor**.
    """
    c = calibrate(PIS, DEP)
    assert c["n_in_bracket"] == 2
    assert c["enough_points"] is False
    # Aralik disi noktalar KELEPCELENMIS oran uretmemeli.
    disarida = [s for s in c["rows"] if not s["in_bracket"]]
    assert len(disarida) == 2
    assert all(np.isnan(s["ratio"]) for s in disarida)
    # Ikinci gozlenebilir esleimiyor.
    assert c["second_observable_available"] is True
    assert c["second_observable_matches"] is False
    assert c["kinetic_mismatch_max"] == pytest.approx(0.180, abs=0.01)
    assert c["transferable"] is False


def test_az_orneklenmis_piston_TASINABILIR_dedirtemez() -> None:
    """Eşleme kusursuz olsa bile az örneklenmişse `transferable` **False**."""
    iyi = [{"r_piston": R, "r_measured": rs, "kinetic_fraction": kf,
            "well_sampled": True}
           for R, rs, kf in [(0.030, 0.2270, 0.1400), (0.045, 0.2310, 0.1480),
                             (0.060, 0.2360, 0.1600)]]
    az = [dict(p, well_sampled=False) for p in iyi]
    assert calibrate(iyi, DEP)["transferable"] is True
    assert calibrate(az, DEP)["transferable"] is False


def test_iki_nokta_SABITLIK_iddiasi_tasiyamaz() -> None:
    """İki noktayla "yayılım" tek bir farktır — sabitlik kanıtı değil."""
    iki = [{"r_piston": 0.030, "r_measured": 0.2270, "kinetic_fraction": 0.1400,
            "well_sampled": True},
           {"r_piston": 0.060, "r_measured": 0.2360, "kinetic_fraction": 0.1600,
            "well_sampled": True}]
    c = calibrate(iki, DEP)
    assert c["n_in_bracket"] == 2
    assert c["enough_points"] is False
    assert c["transferable"] is False


def test_ayirt_etmeyen_kollar_TASINABILIR_dedirtemez() -> None:
    """BOŞLUK KONTROLÜ: piston `R` ile değişmiyorsa eşleme anlamsızdır."""
    duz = [{"r_piston": R, "r_measured": 0.2300, "kinetic_fraction": 0.1450,
            "well_sampled": True} for R in (0.030, 0.045, 0.060)]
    c = calibrate(duz, DEP)
    assert c["piston_discriminates"] is False
    assert c["transferable"] is False


def test_aralik_disi_EKSTRAPOLASYON_isaretleniyor() -> None:
    disarida = [{"r_piston": 0.030, "r_measured": 0.2000,
                 "kinetic_fraction": 0.1400, "well_sampled": True},
                {"r_piston": 0.060, "r_measured": 0.2370,
                 "kinetic_fraction": 0.1600, "well_sampled": True}]
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
