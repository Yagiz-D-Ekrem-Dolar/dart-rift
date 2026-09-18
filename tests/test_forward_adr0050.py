"""ADR-0050 — ileri modelin yeni seçenekleri: geç evre, dondurma, elipsoit.

Varsayılanlar **değişmemeli**: verilmeyen her seçenek eski davranışı ve eski
koşu kimliğini (`_fizik_ozeti`) bit-aynı bırakır.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from dartrift.inference.forward import (
    _fizik_ozeti,
    gozlenebilirleri_cikar,
    ileri_kosu_merdiven,
)

SAHNE = dict(radius=82.0, bulk_density=1800.0, root_seed=1, model_class="M0")
ELIPS = dict(shape="ellipsoid", semi_axes=[88.5, 87.0, 58.0], radius=None,
             bulk_density=1800.0, root_seed=1, model_class="M0")


def _kos(**kw):
    return ileri_kosu_merdiven(
        np.array([[1.15, 1.0e3, 0.275]]), material=None, device="cpu",
        t_end=1.0e-3, kademeler=("6:1.0",), spacing=2.0, **kw)


def test_imza_yeni_secenekler_ve_VARSAYILANLAR():
    p = inspect.signature(ileri_kosu_merdiven).parameters
    assert p["gec_evre"].default is None
    assert p["dondurma"].default is None
    assert p["yari_eksenler"].default is None
    assert p["impuls_zaman"].default == "dogrusal"
    assert p["beta_km"].default is False
    assert inspect.signature(gozlenebilirleri_cikar).parameters[
        "yari_eksenler"].default is None


def test_KAYNAK_cozucunun_gecis_ve_dondurma_yollarini_cagiriyor():
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "gec_evreye_gec(" in k
    assert "uzak_kacanlari_dondur(" in k
    assert "beta_iki_yontem(" in k
    assert "yari_eksenler=_yari" in k


def test_t_gecis_ARALIK_DISI_sahne_kurulmadan_REDDEDILIYOR():
    with pytest.raises(ValueError, match="t_gecis"):
        _kos(sahne_taban=SAHNE, gec_evre={"t_gecis": 2.0e-3, "A": 1e5})
    with pytest.raises(ValueError, match="t_gecis"):
        _kos(sahne_taban=SAHNE, gec_evre={"t_gecis": 0.0, "A": 1e5})


def test_dondurma_her_adim_SIFIR_REDDEDILIYOR():
    with pytest.raises(ValueError, match="her_adim"):
        _kos(sahne_taban=SAHNE, dondurma={"k_uzak": 3.0, "her_adim": 0})


def test_impuls_zaman_GECERSIZ_REDDEDILIYOR():
    with pytest.raises(ValueError, match="impuls_zaman"):
        _kos(sahne_taban=SAHNE, impuls_zaman="karekok")


def test_yari_eksenler_KURE_sahnede_REDDEDILIYOR():
    """Sessiz tutarsızlık olmasın: küre sahnesinde elipsoit ölçütü hata."""
    with pytest.raises(ValueError, match="elipsoit sahnede"):
        _kos(sahne_taban=SAHNE, yari_eksenler=(88.5, 87.0, 58.0))


def test_ozet_YENI_secenekler_VERILMEYINCE_DEGISMIYOR():
    taban = _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1)
    assert _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1,
                        gec_evre=None, dondurma=None,
                        yari_eksenler=None) == taban


@pytest.mark.parametrize("ek", [
    {"gec_evre": {"t_gecis": 0.2, "A": 1.0e5}},
    {"dondurma": {"k_uzak": 3.0, "her_adim": 200}},
    {"yari_eksenler": (88.5, 87.0, 58.0)},
])
def test_ozet_YENI_secenekler_VERILINCE_DEGISIYOR(ek):
    taban = _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1)
    assert _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1, **ek) != taban


def test_ozet_gec_evre_A_DEGERI_kimlige_giriyor():
    a = _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1,
                     gec_evre={"t_gecis": 0.2, "A": 1.0e5})
    b = _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1,
                     gec_evre={"t_gecis": 0.2, "A": 2.7e4})
    assert a != b


def test_ELIPSOIT_sahnede_yari_eksenler_TURETILIYOR():
    """`yari_eksenler` verilmese de sahne elipsoitse ölçüt elipsoit olmalı;
    aksi halde uzun eksen ucundaki çınlama ejekta sayılırdı."""
    k = inspect.getsource(ileri_kosu_merdiven)
    assert 'get("shape") == "ellipsoid"' in k
    assert '_st_["semi_axes"]' in k


def test_adim_bildir_VARSAYILAN_kapali_ve_NEGATIF_reddediliyor():
    """Uzun koşuda ilerleme yazılmazsa takılan koşu bitmiş koşudan
    ayırt edilemez; varsayılan yine de kapalı (çıktı bit-aynı kalsın)."""
    assert inspect.signature(ileri_kosu_merdiven).parameters[
        "adim_bildir"].default == 0
    with pytest.raises(ValueError, match="adim_bildir"):
        _kos(sahne_taban=SAHNE, adim_bildir=-1)
    assert "adim_bildir and adim %" in inspect.getsource(ileri_kosu_merdiven)


def test_gerinim_yumusama_VARSAYILAN_kapali_ozete_giriyor_ve_dogrulaniyor():
    p = inspect.signature(ileri_kosu_merdiven).parameters
    assert p["gerinim_yumusama"].default is None
    taban = _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1)
    assert _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1,
                        gerinim_yumusama=None) == taban
    assert _fizik_ozeti(SAHNE, None, ("6:1.0",), 2.0, 0.1,
                        gerinim_yumusama={"eps_c": 1.0}) != taban
    with pytest.raises(ValueError, match="hedef"):
        _kos(sahne_taban=SAHNE, gerinim_yumusama={"hedef": "bloklar"})
    with pytest.raises(ValueError, match="eps_c"):
        _kos(sahne_taban=SAHNE, gerinim_yumusama={"eps_c": 0.0})
