"""Yakınsama denetiminin **kendisi** sınanıyor.

Bu betiğin işi bir yöntem eksiğini kapatmak: `G4-B1` yakınsamayı tek
düğmede (`λ₂`) ölçüp *"model yakınsadı"* diye okumuştu, `λ₁` hiç
taranmamıştı. Denetim aracı yanlışsa aynı hata **daha güvenli
görünerek** tekrarlanır — o yüzden aracın yargı mantığı burada
kilitleniyor.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from yakinsama_denetimi import (  # noqa: E402
    DUGMELER,
    Dugme,
    bagil_fark,
    mertebe,
    plan_uret,
    topla,
    yargi,
    yeterli_ayar,
)

# ------------------------------------------------------------ kapsam

def test_her_dugmenin_TABANI_uretim_degeri() -> None:
    """Taban üretimden kaymışsa denetim başka bir modeli sınar."""
    beklenen = {"lam1": 19.0, "lam2": 2.0, "spacing": 7.0,
                "r_ince1": 3.0, "r_ince2": 25.0, "cfl": 0.25,
                "n_mermi": 800.0}
    for d in DUGMELER:
        if d.ad in beklenen:
            assert d.taban == beklenen[d.ad], d.ad


def test_plan_TEK_taban_uretiyor() -> None:
    """`n` düğme için `n` özdeş taban koşusu israf olurdu."""
    kollar = plan_uret()
    tabanlar = [k for k in kollar if k.taban_mi]
    assert len(tabanlar) == 1
    assert len(kollar) == 1 + sum(len(d.basamaklar) for d in DUGMELER)


def test_plan_kollari_TEK_DEGISKENLI() -> None:
    """Bir kolda yalnızca bir düğme değişmeli."""
    for k in plan_uret():
        if k.taban_mi:
            continue
        bayraklar = [x for x in k.argumanlar if x.startswith("--")]
        assert bayraklar.count("--t-end") == 1
        assert len(bayraklar) == 2, k.argumanlar


# ------------------------------------------------------------ mertebe

def test_mertebe_ikinci_dereceyi_buluyor() -> None:
    """`Δ ~ h²`: yarıya inen `h` farkı `4` kat küçültür -> `p = 2`."""
    assert mertebe(4.0, 1.0, 2.0) == pytest.approx(2.0)
    assert mertebe(8.0, 1.0, 2.0) == pytest.approx(3.0)
    assert mertebe(2.0, 1.0, 2.0) == pytest.approx(1.0)


def test_mertebe_YAKINSAMAYAN_ekseni_negatif_veriyor() -> None:
    """Fark büyüyorsa mertebe negatif olmalı -- sessizce geçmemeli."""
    assert mertebe(1.0, 2.0, 2.0) < 0.0


def test_mertebe_makine_sifiri_ve_bozuk_oran() -> None:
    assert mertebe(1.0, 0.0, 2.0) == math.inf
    assert math.isnan(mertebe(0.0, 0.0, 2.0))
    assert mertebe(0.0, 1.0, 2.0) == 0.0
    with pytest.raises(ValueError, match="oran > 1"):
        mertebe(1.0, 1.0, 1.0)


def test_ters_dugmede_oran_TERS_hesaplaniyor() -> None:
    """`cfl` ve `spacing` küçülünce incelir; oran `kaba/ince`."""
    cfl = next(d for d in DUGMELER if d.ad == "cfl")
    assert cfl.oran(0.25, 0.125) == pytest.approx(2.0)
    lam1 = next(d for d in DUGMELER if d.ad == "lam1")
    assert lam1.oran(19.0, 38.0) == pytest.approx(2.0)


# ------------------------------------------------------------- yargi

def test_bagil_fark_ve_yargi() -> None:
    assert bagil_fark(2.0, 2.2) == pytest.approx(0.1)
    assert bagil_fark(0.0, 0.3) == pytest.approx(0.3)   # taban sifir
    assert yargi(0.05, 0.10) == "gecti"
    assert yargi(0.16, 0.10) == "DUSTU"
    assert yargi(float("nan"), 0.10) == "olculemedi"


def test_esikte_DUSUYOR_esitlik_gecmez() -> None:
    """`<` ile `<=` arasindaki fark bir kapiyi geciriyor olabilir."""
    assert yargi(0.10, 0.10) == "DUSTU"


# ------------------------------------------------------- yeterli ayar

def test_yeterli_ayar_yakinsamis_ekseni_KABA_birakiyor() -> None:
    d = Dugme("x", "--x", 2.0, (4.0, 8.0), "")
    # 4'e inceltince fark cok kucuk -> taban zaten yeterli
    assert yeterli_ayar({4.0: 1e-4, 8.0: 1e-5}, d, 0.10) == 2.0


def test_yeterli_ayar_YAKINSAMAYAN_eksende_nan() -> None:
    d = Dugme("x", "--x", 2.0, (4.0, 8.0), "")
    assert math.isnan(yeterli_ayar({4.0: 0.16, 8.0: 0.30}, d, 0.10))


def test_yeterli_ayar_ARADA_dogru_basamagi_seciyor() -> None:
    d = Dugme("x", "--x", 2.0, (4.0, 8.0), "")
    # 4'e gecerken buyuk fark, 8'e gecerken kucuk -> 4 yeterli
    assert yeterli_ayar({4.0: 0.30, 8.0: 0.01}, d, 0.10) == 4.0


# ------------------------------------------------------------- topla

def _yaz(dizin: Path, ad: str, beta: float) -> None:
    (dizin / f"{ad}.json").write_text(json.dumps(
        {"beta": beta, "n_ejekta": 28, "A1": 2.04, "N_asama2": 10410,
         "duvar_s": 60.0, "t_sim": 0.2}), encoding="utf-8")


def test_topla_KOSULMAYAN_dugmeyi_DENETLENMEDI_diye_isaretliyor(
        tmp_path: Path) -> None:
    """Asıl hata buydu: taranmamış düğme sessizce yok sayılıyordu."""
    _yaz(tmp_path, "taban_0", 1.4112)
    _yaz(tmp_path, "lam2_4", 1.4113)
    r = topla(tmp_path)
    d = {s["dugme"]: s for s in r["satirlar"]}
    assert d["lam2"]["durum"] == "denetlendi"
    assert d["lam2"]["yargi"] == "gecti"
    assert d["lam1"]["durum"] == "denetlenmedi"
    assert d["spacing"]["durum"] == "denetlenmedi"
    assert r["eksik_kollar"]


def test_topla_ESIK_DISI_ekseni_DUSTU_veriyor(tmp_path: Path) -> None:
    _yaz(tmp_path, "taban_0", 1.411216)
    _yaz(tmp_path, "lam1_38", 1.185066)      # olculen gercek deger
    r = topla(tmp_path)
    d = {s["dugme"]: s for s in r["satirlar"]}
    assert d["lam1"]["yargi"] == "DUSTU"
    assert d["lam1"]["bagil_fark"] == pytest.approx(0.1603, abs=1e-3)


def test_topla_TABAN_yoksa_duruyor(tmp_path: Path) -> None:
    _yaz(tmp_path, "lam1_38", 1.2)
    with pytest.raises(SystemExit, match="taban"):
        topla(tmp_path)
