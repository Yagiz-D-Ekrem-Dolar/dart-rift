"""Her koşu **kendi** şok yargısını taşıyor mu (ADR-0049 §4).

Bu depo **dört kez** bir şeyin etkisiz olduğunu, o şeyin etki
edeceği fiziğin hiç oluşmadığı bir koşuda ölçtü. Yargı sonuç
dosyasının **içinde** olursa *"etkisiz"* diyen bir satırın yanında
"şok var mıydı" sorusu da yanıtlı durur.

A22 ayrıca yalnızca `t_end`'e bakmıştı ve şok `t₁` civarında tepe
yapıp söndüğü için *"model şok üretmiyor"* sonucuna varmıştı; bu
yüzden **iki** yargı da kilitleniyor.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import faz48_iki_asama as f  # noqa: E402
from sok_sinavi import RHO_MATRIS  # noqa: E402


def test_yargi_HEDEFI_suzuyor_mermiyi_saymiyor() -> None:
    """Mermi çok sıkışmış olsa bile yargı **hedefe** bakmalı."""
    rho = np.array([RHO_MATRIS, RHO_MATRIS * 1.6])   # 2. parcacik mermi
    hedef = np.array([True, False])
    r = f._sok_yargisi(rho, np.zeros(2), np.ones(2),
                       np.full(2, 1.7564), hedef)
    assert r["sikisma_max_yuzde"] == pytest.approx(0.0, abs=1e-9)
    assert r["yargi"] == "SOK_YOK"


def test_yargi_SOKLANMIS_hedefi_goruyor() -> None:
    rho = np.array([RHO_MATRIS * 1.5, RHO_MATRIS])
    r = f._sok_yargisi(rho, np.zeros(2), np.ones(2), np.full(2, 1.7564),
                       np.array([True, True]))
    assert r["yargi"] == "SOK_VAR"
    assert r["sikisma_max_yuzde"] == pytest.approx(50.0, abs=1e-3)


def test_yargi_alanlari_SONUC_dosyasina_uygun() -> None:
    """JSON'a yazılacağı için hepsi seri hale gelebilmeli."""
    import json
    r = f._sok_yargisi(np.array([RHO_MATRIS]), np.zeros(1), np.ones(1),
                       np.array([1.7564]), np.array([True]))
    assert set(r) == {"sikisma_max_yuzde", "sikisma_medyan_yuzde",
                      "hugoniot_bandi_yuzde", "bandin_kacta_biri",
                      "n_yuzde5_ustu", "n_bant_icinde", "yargi"}
    json.dumps(r)          # atmamali


def test_IKI_ASAMALI_sonuc_t1_VE_tend_yargisini_tasiyor() -> None:
    """Yalnızca `t_end`'e bakmak A22'nin hatasıydı."""
    k = inspect.getsource(f.main)
    assert '"sok": _sok_yargisi(st_son["rho"]' in k
    assert '"sok_t1": _sok_yargisi(st1["rho"]' in k


def test_TEK_ASAMALI_sonuc_da_yargi_tasiyor() -> None:
    k = inspect.getsource(f.main)
    assert '"sok": _sok_yargisi(st_tek["rho"]' in k


def test_SOK_YOK_ekrana_UYARI_basiyor() -> None:
    """Sessiz geçmek, dört kez düşülen tuzağın kendisi."""
    k = inspect.getsource(f.main)
    assert "sok t1'de VARDI, t_end'de YOK" in k
    assert "hedefe ait hicbir seyin " in k and "ADR-0049" in k
