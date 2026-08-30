"""Merdivenli ileri model + şok kapısı (ADR-0049).

`ileri_kosu` ve `ileri_kosu_ikiasama` şokun hiç oluşmadığı ya da
aktarımda silindiği rejimlerde koşuyordu (A22 – A25). Ensemble'ın
anlamlı olabilmesi için ileri modelin **merdivenli** sürümü gerekli.

Ve ADR-0049: şok kurulmayan nokta `nan` döner, vekil onu **görmez**.
Sessizce zayıf bir noktayı veri saymaktansa eksik saymak doğru.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from dartrift.observables.sok import (
    GECME_KESRI,
    hugoniot_bandi,
    sikisma_max,
    sok_gecti,
)

# ------------------------------------------------------- SOK KAPISI

def test_band_DART_hizinda_literatur_mertebesinde() -> None:
    alt, ust = hugoniot_bandi(6144.9)
    assert alt == pytest.approx(45.6, abs=0.2)
    assert ust == pytest.approx(74.3, abs=0.2)


def test_sikisma_alpha0_ile_KESIN() -> None:
    a0 = np.array([1.7564, 1.05])
    rho = np.array([2700.0 / 1.7564 * 1.5, 2700.0 / 1.05 * 1.2])
    assert sikisma_max(rho, a0) == pytest.approx(50.0, abs=1e-3)


def test_kapi_OLCULEN_degerleri_dogru_ayiriyor() -> None:
    """Eşik, A23'ün iki ölçümünün **arasında** ve ikisine de uzak.

    | `λ₂` | sıkışma | beklenen |
    |---|---|---|
    | `8` | `%1,68` | **düşer** |
    | `20` | `%22,0` | **geçer** |
    | merdiven | `%45,18` | geçer |
    """
    a0 = np.array([1.7564])
    taban = 2700.0 / 1.7564
    for sik, bek in ((0.0168, False), (0.2200, True), (0.4518, True)):
        assert sok_gecti(np.array([taban * (1 + sik)]), a0) is bek, sik


def test_kapi_esigi_iki_olcumun_ARASINDA() -> None:
    alt, _ = hugoniot_bandi()
    esik = GECME_KESRI * alt
    assert 1.68 < esik < 22.0, esik


def test_kapi_bozuk_girdiyi_REDDEDIYOR() -> None:
    with pytest.raises(ValueError, match="ayni olmali"):
        sikisma_max(np.ones(3), np.ones(2))
    with pytest.raises(ValueError, match="alpha0 pozitif"):
        sikisma_max(np.ones(2), np.zeros(2))


# ------------------------------------------------- ILERI MODEL YAPISI

def test_ileri_merdiven_VAR_ve_kademeleri_aliyor() -> None:
    from dartrift.inference.forward import ileri_kosu_merdiven
    s = inspect.signature(ileri_kosu_merdiven)
    for ad in ("kademeler", "spacing", "t_end", "sok_yargisi"):
        assert ad in s.parameters, ad
    assert s.parameters["sok_yargisi"].default is True


def test_ileri_merdiven_SESSIZ_KISALMAYI_reddediyor() -> None:
    """A20: adım sınırına takılan koşu tam koşmuş gibi kaydedilirse
    vekil **yanlış veriyle** eğitilir ve bunu anlayamaz."""
    from dartrift.inference.forward import ileri_kosu_merdiven
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "ADIM SINIRINA TAKILDI" in k
    assert "raise RuntimeError" in k


def test_ileri_merdiven_SOK_KAPISINI_uyguluyor() -> None:
    from dartrift.inference.forward import ileri_kosu_merdiven
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "sok_gecti" in k
    assert "ADR-0049" in k


def test_ileri_merdiven_AKTARIM_kullanmiyor() -> None:
    """Tek aşamalı: `ρ` hiçbir yerde sıfırlanmıyor (A24)."""
    from dartrift.inference.forward import ileri_kosu_merdiven
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "asama2" not in k and "two_stage" not in k
    assert "refine_scene_kademeli" in k


# ------------------------------------------------- ENSEMBLE SURUCUSU

def test_ensemble_surucusu_MERDIVENI_kullaniyor() -> None:
    """Sürücü eski (şoksuz) ileri modele düşerse ensemble yine boş çıkar."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert "ileri_kosu_merdiven(" in k
    assert "kademeler=MERDIVEN" in k
    assert m.MERDIVEN == ("48:2.8", "24:1.4", "12:0.7", "6:0.35", "3:0.175")


def test_ensemble_surucusu_SOK_KAPISI_varsayilan_ACIK() -> None:
    """Kapıyı kapatmak tanı içindir; varsayılan olmamalı (ADR-0049)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert '"--sok-kapisi-kapali", action="store_true"' in k
    assert "sok_yargisi=not a.sok_kapisi_kapali" in k


def test_ensemble_surucusu_EnsembleDurum_alanlarini_dogru_okuyor() -> None:
    """Yanlış alan adı `AttributeError` ile koşunun **sonunda** patlar —
    yani bütün GPU işi bittikten sonra. Burada erken yakalanıyor."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m

    from dartrift.inference.ensemble import EnsembleDurum
    alanlar = set(EnsembleDurum.__dataclass_fields__)
    k = inspect.getsource(m.main)
    for ad in ("tamamlanan", "toplam", "dusen", "atlanan", "bozuk_satir"):
        assert ad in alanlar, ad
        assert f"durum.{ad}" in k, ad
