"""FAZ 5 ensemble maliyeti — A′'dan sonra yeniden hesap (FAZ 4 → 5 geçişi)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.ensemble_cost import (OLCULEN, adim_maliyeti_s,
                                               ensemble_gpu_gunu,
                                               fizibilite_sinirlari,
                                               kosu_maliyeti_s)


def test_adim_maliyeti_OLCULEN_noktada_tutuyor() -> None:
    """Boşluk kontrolü: ölçümün yapıldığı `N`'de ölçülen süreyi vermeli.

    FIZIBILITE §2b: `N = 65 840` → `570 ms`.
    """
    beklenen = 0.570
    assert adim_maliyeti_s(OLCULEN["olcum_N"]) == pytest.approx(beklenen,
                                                               rel=0.02)


def test_adim_maliyeti_PARCACIKLA_dogrusal() -> None:
    assert adim_maliyeti_s(20000) == pytest.approx(2.0 * adim_maliyeti_s(10000))


def test_kosu_maliyeti_ADIM_SAYISIYLA_dogrusal() -> None:
    a = kosu_maliyeti_s(1.0, 10000, 1e-4)
    b = kosu_maliyeti_s(2.0, 10000, 1e-4)
    assert b == pytest.approx(2.0 * a, rel=1e-9)


def test_dt_KUCULURSE_maliyet_ARTIYOR() -> None:
    """A′'nın `dt` cezası hesaba **girmeli** — atlanırsa A′ ucuz görünür."""
    buyuk = kosu_maliyeti_s(1.0, 10000, 1e-4)
    kucuk = kosu_maliyeti_s(1.0, 10000, 5e-5)
    assert kucuk == pytest.approx(2.0 * buyuk, rel=1e-9)


def test_A_prime_TEKDUZE_INCEDEN_ucuz() -> None:
    """A′'nın varlık nedeni; oran `6,87×` (parçacık tasarrufu) olmalı."""
    d = ensemble_gpu_gunu(1.0, 300)
    assert d["A-prime"] < d["tekduze-ince"]
    beklenen = OLCULEN["N_tumu_ince"] / OLCULEN["N_aprime"]
    assert d["_kazanc_tumu_inceye_gore"] == pytest.approx(beklenen, rel=1e-6)


def test_A_prime_TEKDUZE_KABADAN_pahali_ve_NEDENI_dt() -> None:
    """A′ kaba sahneden **pahalı** — ve bu gizlenmemeli.

    Neden: parçacık sayısı biraz artıyor **ve** `dt` yarıya iniyor.
    Kaba sahne yine de kullanılamaz (mermi çözülmemiş, ADR-0026), ama
    A′'nın kabaya göre bedeli **açıkça** görünmeli.
    """
    d = ensemble_gpu_gunu(1.0, 300)
    assert d["A-prime"] > d["tekduze-kaba"]
    # Bedelin buyuk kismi dt'den: N orani kucuk, dt orani 2.
    n_orani = OLCULEN["N_aprime"] / OLCULEN["N_tumu_kaba"]
    assert d["A-prime"] / d["tekduze-kaba"] == pytest.approx(
        n_orani * OLCULEN["lam"], rel=1e-6)


def test_ensemble_KOSU_SAYISIYLA_dogrusal() -> None:
    a = ensemble_gpu_gunu(1.0, 100)["A-prime"]
    b = ensemble_gpu_gunu(1.0, 300)["A-prime"]
    assert b == pytest.approx(3.0 * a, rel=1e-9)


def test_fizibilite_siniri_ENSEMBLE_ile_TUTARLI() -> None:
    """İki fonksiyon aynı modeli kullanıyor; ayrışırlarsa biri yanlış."""
    butce = 30.0
    sinir = fizibilite_sinirlari(butce, 300)
    for ad in ("tekduze-kaba", "A-prime", "tekduze-ince"):
        geri = ensemble_gpu_gunu(sinir[ad], 300)[ad]
        assert geri == pytest.approx(butce, rel=1e-3), ad


def test_A_prime_30_GUNLUK_butceye_SIGIYOR_ince_SIGMIYOR() -> None:
    """Kararın kendisi: A′ ensemble'ı fizibil kılan şey mi?

    FIZIBILITE `~30 GPU-günü`nü fizibil sayıyordu. `1 s` simüle için:
    A′ `9,73` gün, tekdüze ince `66,85` gün.
    """
    d = ensemble_gpu_gunu(1.0, 300)
    assert d["A-prime"] < 30.0 < d["tekduze-ince"]


def test_gecersiz_girdiler_REDDEDILIYOR() -> None:
    for f, arg in ((adim_maliyeti_s, 0), (adim_maliyeti_s, -5)):
        with pytest.raises(ValueError):
            f(arg)
    with pytest.raises(ValueError):
        kosu_maliyeti_s(0.0, 100, 1e-4)
    with pytest.raises(ValueError):
        kosu_maliyeti_s(1.0, 100, 0.0)
    with pytest.raises(ValueError):
        ensemble_gpu_gunu(1.0, 0)
    with pytest.raises(ValueError):
        fizibilite_sinirlari(0.0)


def test_FIZIBILITE_ile_dogrudan_kiyas_UYARISI_var() -> None:
    """İki mutlak sayı aynı şeyi ölçmüyor; modül bunu **söylemeli**."""
    from pathlib import Path

    m = (Path(__file__).resolve().parents[1] / "src" / "dartrift" /
         "validation" / "ensemble_cost.py").read_text(encoding="utf-8")
    assert "doğrudan kıyaslanamaz" in m
    assert "2 000 000" in m and "11 000" in m
    assert "ORAN" in m
