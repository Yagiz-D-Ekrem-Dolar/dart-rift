"""D-1 tarama **analizinin** denetimi — GPU gerekmez.

Koşu GPU ister ama asıl mantık **iki rejimin ayrılmasıdır** ve o saf bir
fonksiyona (`analyse_scan`) çıkarıldı. Burada ölçülmüş gerçek veriyle
sınanıyor: eşiği yanlış koymak sonucu **nasıl** değiştirirdi?
"""
from __future__ import annotations

import pytest

from dartrift.validation.deposit_radius import analyse_scan

# TRUBA is 1451137, n_side = 64 — GERCEK olculen veri.
OLCULEN = [
    {"rel_err": 0.07112, "deposit_over_shock": 0.1200, "n_injected": 32},
    {"rel_err": 0.09611, "deposit_over_shock": 0.1601, "n_injected": 56},
    {"rel_err": 0.04028, "deposit_over_shock": 0.2001, "n_injected": 136},
    {"rel_err": 0.04435, "deposit_over_shock": 0.2401, "n_injected": 208},
    {"rel_err": 0.04464, "deposit_over_shock": 0.3201, "n_injected": 552},
    {"rel_err": 0.03255, "deposit_over_shock": 0.4802, "n_injected": 1904},
]


def test_iki_rejim_ayriliyor() -> None:
    a = analyse_scan(OLCULEN)
    assert a["n_well_sampled"] == 4
    assert a["min_injected_particles"] == 32
    assert a["injection_well_sampled"] is False        # 32 < 100
    assert a["enough_well_sampled_points"] is True


def test_gevsek_esik_iki_rejimi_KARISTIRIR() -> None:
    """İlk eşiğim (`20`) neden yetersizdi — **ölçülen** veriyle gösteriliyor.

    `20` ile altı noktanın **hepsi** "iyi" sayılır ve az örneklenen iki nokta
    uydurmayı 2,4 kat bozar.
    """
    gevsek = analyse_scan(OLCULEN, well_sampled_min=20)
    siki = analyse_scan(OLCULEN, well_sampled_min=100)
    assert gevsek["n_well_sampled"] == 6
    assert siki["n_well_sampled"] == 4
    assert abs(gevsek["error_exponent"]) > 2.0 * abs(siki["error_exponent"])
    # Ve yayilim: gevsek esik hatanin ne kadar DUZ oldugunu gizler.
    assert gevsek["well_sampled_spread"] > 3.0 * siki["well_sampled_spread"]


def test_iyi_rejimde_hata_DUZ() -> None:
    """Asıl bulgu: iyi rejimde yarıçap 2,4 kat değişiyor, hata 1,21 puan."""
    a = analyse_scan(OLCULEN)
    lo, hi = a["well_sampled_err_range"]
    assert lo == pytest.approx(0.03255)
    assert hi == pytest.approx(0.04464)
    assert a["well_sampled_spread"] == pytest.approx(0.01209, abs=1e-5)


def test_us_isareti_negatif() -> None:
    """`p < 0`: yarıçap küçüldükçe hata büyüyor (naif beklentinin tersi)."""
    a = analyse_scan(OLCULEN)
    assert a["error_exponent"] < 0.0
    assert a["error_exponent_contaminated"] < a["error_exponent"]


def test_ayirt_etme_bosluk_kontrolu() -> None:
    a = analyse_scan(OLCULEN)
    assert a["scan_discriminates"] is True
    # BOSLUK KONTROLU: DUZ bir tarama ayirt ETMEMELI.
    duz = [{"rel_err": 0.04, "deposit_over_shock": o, "n_injected": 500}
           for o in (0.2, 0.3, 0.4)]
    assert analyse_scan(duz)["scan_discriminates"] is False


def test_gecersiz_girdi_reddediliyor() -> None:
    with pytest.raises(ValueError, match="en az 3"):
        analyse_scan(OLCULEN[:2])
    kotu = [dict(r) for r in OLCULEN]
    kotu[0]["deposit_over_shock"] = 0.0
    with pytest.raises(ValueError, match="pozitif"):
        analyse_scan(kotu)


def test_kinetik_kesir_eski_ciktilarla_uyumlu() -> None:
    """Alan yoksa **sessizce atlanır** ama `kinetic_available` bunu söyler.

    Eski koşu çıktıları (bu alan eklenmeden önce üretilmiş) hâlâ
    yorumlanabilmeli — ama "ölçülmedi" ile "sıfır" karıştırılmamalı.
    """
    assert analyse_scan(OLCULEN)["kinetic_available"] is False


def test_kinetik_kesir_sok_yaricapindan_DAHA_DUYARLI() -> None:
    """ADR-0041 §5 boşluk 2: β'nın Sedov karşılığı daha duyarlı mı?

    ADR-0011'in ölçtüğü değerlerle (n = 32…112: 0,224 / 0,191 / 0,182 /
    0,200 / 0,189 / 0,187) sınanıyor. Nokta patlaması değeri **0,28**;
    sonlu enjeksiyon **~0,19** — yani `%32` fark, şok yarıçapının `%4`'üne
    karşı.
    """
    rows = [dict(r) for r in OLCULEN]
    for r, k in zip(rows, [0.224, 0.210, 0.200, 0.195, 0.189, 0.182], strict=False):
        r["kinetic_fraction"] = k
    a = analyse_scan(rows)
    assert a["kinetic_available"] is True
    lo, hi = a["kinetic_well_sampled_range"]
    assert lo == pytest.approx(0.182)
    assert hi == pytest.approx(0.200)
    # Kinetik kesrin GORELI yayilimi, sok yaricapi hatasinin yayilimindan
    # daha buyuk olmali — yoksa bu ikinci gozlenebilir bir sey EKLEMIYOR.
    assert a["kinetic_spread_rel"] > 0.05
