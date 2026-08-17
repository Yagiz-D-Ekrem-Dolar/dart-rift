"""`h_policy`'nin DART salınımı yargısı — ADR-0042 yükümlülüğünün kilidi.

Yargı **kapsama** üzerine kurulu: küp taramasının fiilen kapsadığı
`N_komşu` aralığı dışında yargı kurulmaz (KAYIT-029 dersi). Bu testler
o mantığın gevşemesini engelliyor.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.h_policy import (
    KUP_SALINIMI, KUP_TARAMA_KAPSAMI, dart_salinim_ozeti,
    judge_dart_salinimi, neighbour_count)


def _orn(degerler) -> dict:
    return {"n_komsu": np.asarray(degerler, dtype=np.float64)}


def test_ozet_zaman_ve_uzay_salinimini_ayirir() -> None:
    """Uzaysal yayılım sabitken zaman salınımı yakalanmalı."""
    # Iki ornek: ortancalari 100 ve 400, her birinde dar yayilim.
    o = dart_salinim_ozeti([_orn(np.full(200, 100.0)),
                            _orn(np.full(200, 400.0))])
    assert o["salinim_zamanda"] == pytest.approx(4.0, rel=1e-9)
    assert o["n_ornek"] == 2
    assert o["n_deger"] == 400


def test_ozet_gecersiz_degerleri_atar() -> None:
    d = np.concatenate([np.full(100, 300.0), [np.nan, np.inf, 0.0, -5.0]])
    o = dart_salinim_ozeti([_orn(d)])
    assert o["n_deger"] == 100
    assert o["N_komsu_p01"] == pytest.approx(300.0)


def test_ozet_az_ornekte_hata_verir() -> None:
    with pytest.raises(ValueError, match="32"):
        dart_salinim_ozeti([_orn(np.full(10, 300.0))])
    with pytest.raises(ValueError, match="ornek yok"):
        dart_salinim_ozeti([])


def test_kapsam_icinde_kanit_gecerli() -> None:
    """Küp aralığının içinde kalan salınım ADR'yi açmaz."""
    d = np.concatenate([np.full(500, 100.0), np.full(500, 600.0)])
    y = judge_dart_salinimi(dart_salinim_ozeti([_orn(d)]))
    assert y["kanit_kapsiyor"] is True
    assert y["karar"] == "kanit_gecerli"


def test_kapsam_disinda_adr_yeniden_acilir() -> None:
    """Üst uçtan taşan salınım ADR'yi açmalı."""
    d = np.concatenate([np.full(500, 100.0), np.full(500, 5000.0)])
    y = judge_dart_salinimi(dart_salinim_ozeti([_orn(d)]))
    assert y["kanit_kapsiyor"] is False
    assert y["karar"] == "adr_yeniden_acilmali"


def test_alt_uctan_tasma_da_acar() -> None:
    """Çok SEYREK bölge de kapsam dışıdır — tek yön değil."""
    d = np.concatenate([np.full(500, 5.0), np.full(500, 300.0)])
    y = judge_dart_salinimi(dart_salinim_ozeti([_orn(d)]))
    assert y["kanit_kapsiyor"] is False
    assert y["karar"] == "adr_yeniden_acilmali"


def test_oran_buyuk_ama_kapsam_ici_ise_kanit_gecerli_kalir() -> None:
    """Kararı belirleyen ORAN değil KAPSAMA — ayrım korunmalı.

    `2,06×`'ı aşan ama `56,1–650,5` içinde kalan bir salınımda karar
    `kanit_gecerli` olmalı; oran ayrıca raporlanır.
    """
    d = np.concatenate([np.full(500, 60.0), np.full(500, 640.0)])
    y = judge_dart_salinimi(dart_salinim_ozeti([_orn(d)]))
    assert y["dart_salinim_orani"] > y["kup_salinim_orani"]
    assert y["oran_kup_uzerinde_mi"] is True
    assert y["kanit_kapsiyor"] is True
    assert y["karar"] == "kanit_gecerli"


def test_yorum_alani_tasiniyor() -> None:
    """*"Belirgin biçimde"*'nin yorum olduğu çıktıda kalmalı."""
    y = judge_dart_salinimi(dart_salinim_ozeti([_orn(np.full(100, 300.0))]))
    assert "tanimsiz" in y["yorum"]
    assert "kapsama" in y["yorum"]


def test_sabitler_kayit_035_ile_tutarli() -> None:
    """Küp sayıları kayıttan geliyor; sessizce değişmesin."""
    assert KUP_SALINIMI == (268.2, 551.5)
    assert KUP_TARAMA_KAPSAMI == (56.1, 650.5)
    # Kapsam, salinimi ICERMEK zorunda -- yoksa kaydin kendisi tutarsiz.
    assert KUP_TARAMA_KAPSAMI[0] < KUP_SALINIMI[0]
    assert KUP_TARAMA_KAPSAMI[1] > KUP_SALINIMI[1]


def test_parcacik_basina_h_ile_komsu_sayisi_olcekten_bagimsiz() -> None:
    """A′ tasarım niyeti: `h ∝ s`, `m ∝ s³ρ` ⇒ `N_komşu` sabit.

    Bu, DART ölçümünde ince/kaba bölgelerin ayrı raporlanmasının
    gerekçesi. Niyet cebirsel; testi de cebirsel olmalı.
    """
    rho = 2700.0
    for s in (0.5, 1.0, 7.0):
        h = 2.0 * s
        m = rho * s**3
        nk = float(neighbour_count(rho, h, m))
        assert nk == pytest.approx(
            (4.0 / 3.0) * np.pi * (2.0 * 2.0) ** 3, rel=1e-12)
