"""`faz48_iki_asama._mat` — hasar kolu ve **config ile çelişki**.

A17'nin kök neden adayı bir kod çelişkisiydi: `configs/p3_dimorphos.yaml`
`damage.enabled: true` derken FAZ 4'ün bütün koşularının malzemesi
(`faz44_dart_yakinsama._malzeme`) hasarı kapalı tutuyordu.

Bu dosya iki şeyi sabitliyor:

1. `--hasarli` kolu gerçekten **yalnızca** hasarı açıyor; başka hiçbir
   modülü sessizce değiştirmiyor (bir tanı kolunun tek değişkenli
   olması bu depoda daha önce bozulmuştu — `--gozeneksiz` sahneyi de
   katı kurmak zorundaydı, rapor A14).
2. Çelişkinin kendisi **kayıtlı**. Biri iki taraftan birini
   düzeltirse bu test düşer ve raporun güncellenmesi gerektiğini
   söyler.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from faz44_dart_yakinsama import _malzeme  # noqa: E402
from faz48_iki_asama import _mat  # noqa: E402


def test_varsayilan_kol_hasari_KAPALI_tutuyor() -> None:
    """FAZ 4'ün bütün ölçümlerinin koştuğu hâl — kayda geçiyor."""
    assert _mat().damage.enabled is False
    assert _malzeme().damage.enabled is False


def test_hasarli_kol_YALNIZCA_hasari_aciyor() -> None:
    k, h = _mat(), _mat(hasarli=True)
    assert h.damage.enabled is True
    # tek degisken: geri kalan her sey birebir ayni kalmali
    assert h.strength == k.strength
    assert h.porosity == k.porosity
    assert h.gravity == k.gravity
    assert h.eos == k.eos
    assert h.density_method == k.density_method
    # hasar parametreleri varsayilanlardan gelir (configs/p3_dimorphos.yaml
    # ile ayni degerler); bayrak onlari uydurmuyor
    assert h.damage.k_weibull == k.damage.k_weibull
    assert h.damage.m_weibull == k.damage.m_weibull


def test_hasar_kolu_diger_kollarla_BIRLESEBILIYOR() -> None:
    h = _mat(gozeneksiz=True, yercekimli=True, hasarli=True)
    assert h.damage.enabled is True
    assert h.gravity.enabled is True
    assert h.porosity.enabled is False


def test_config_ile_KOD_celisiyor_ve_bu_YAZILI() -> None:
    """Çelişki kapanırsa rapor da güncellenmeli; test onu hatırlatır."""
    cfg = (REPO / "configs" / "p3_dimorphos.yaml").read_text(encoding="utf-8")
    i = cfg.index("damage:")
    assert "enabled: true" in cfg[i:i + 200], "config artik hasari acmiyor"
    assert _malzeme().damage.enabled is False, (
        "kod hasari artik ACIYOR -- celiski kapandi, "
        "docs/FAZ4-SIKINTI-RAPORU.md A17 guncellenmelidir")
    rapor = (REPO / "docs" / "FAZ4-SIKINTI-RAPORU.md").read_text(
        encoding="utf-8")
    assert "ADR-0027" in rapor


def test_boulder_Y0_kolu_ayri_ve_matristen_BAGIMSIZ() -> None:
    """`--Y0` matrisi, `--boulder-Y0` bloğu ezmeli; ikisi karışmamalı.

    KAYIT-050: `_sahne_Y0` yalnızca `matrix_Y0`'ı eziyordu ve
    `boulder_Y0` (hedefin kütlece `%36,3`'ü) FAZ 4 boyunca `1e7 Pa`'da
    sabit kaldı. Bu test o boşluğun geri gelmesini engelliyor.
    """
    from faz48_iki_asama import _sahne_Y0
    kw = {"radius": 82.0}
    assert _sahne_Y0(kw, None) == kw
    assert _sahne_Y0(kw, 5.0)["matrix_Y0"] == 5.0
    assert "boulder_Y0" not in _sahne_Y0(kw, 5.0)
    d = _sahne_Y0(kw, None, 3.0)
    assert d["boulder_Y0"] == 3.0 and "matrix_Y0" not in d
    d = _sahne_Y0(kw, 5.0, 3.0)
    assert (d["matrix_Y0"], d["boulder_Y0"]) == (5.0, 3.0)
    # cagiranin sozlugu DEGISMEMELI
    assert kw == {"radius": 82.0}


def test_boulder_Y0_pozitif_olmali() -> None:
    import pytest
    from faz48_iki_asama import _sahne_Y0
    with pytest.raises(ValueError, match="boulder_Y0 pozitif"):
        _sahne_Y0({}, None, 0.0)
    with pytest.raises(ValueError, match="Y0 pozitif"):
        _sahne_Y0({}, -1.0)
