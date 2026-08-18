"""`a17_momentum_anatomisi` — yönlülük ayrımı ve süre yargısı kilidi.

Betiğin işi tek bir `β` sayısının karıştırdığı üç soruyu ayırmak. O
ayrımın kendisi test edilmeli, çünkü A17'de yanlış çıkarım tam burada
yapıldı: eş yönlü çınlama ile yönlü koni ayrılmadığı için `β`'nın sabit
kalması *"ejekta yok"* diye okundu.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from a17_momentum_anatomisi import anatomi  # noqa: E402


def _yaz(tmp: Path, x, v, m, R, t) -> Path:
    y = tmp / "durum.npz"
    np.savez(y, x=np.asarray(x, np.float64), v=np.asarray(v, np.float64),
             m=np.asarray(m, np.float64), R=np.float64(R), t=np.float64(t))
    return y


def _kure(n: int, R: float):
    """Fibonacci küresi — eş dağılımlı yön vektörleri."""
    i = np.arange(n) + 0.5
    phi = np.arccos(1.0 - 2.0 * i / n)
    tht = np.pi * (1.0 + 5.0**0.5) * i
    return R * np.stack([np.cos(tht) * np.sin(phi),
                         np.sin(tht) * np.sin(phi), np.cos(phi)], axis=1)


def test_es_yonlu_genlesme_yonluluk_sifir(tmp_path: Path) -> None:
    """Çınlama: radyal momentum büyük, eksenel net ~0."""
    n, R = 400, 80.0
    x = _kure(n, 0.6 * R)
    v = 3.0 * x / np.linalg.norm(x, axis=1)[:, None]  # tam radyal disa
    a = anatomi(_yaz(tmp_path, x, v, np.full(n, 1.0e5), R, 50.0))

    assert a["p_radyal_disa"] > 0.0
    assert a["yonluluk"] < 1e-2, a["yonluluk"]


def test_yonlu_koni_yonluluk_bire_yakin(tmp_path: Path) -> None:
    """Koni: tüm madde tek eksende -> yönlülük ~1."""
    n, R = 200, 80.0
    rng = np.random.default_rng(7)
    # +z yarim-uzayda dar bir koni, hepsi +z dogrultusunda hizli
    ct = rng.uniform(0.98, 1.0, n)
    st = np.sqrt(1.0 - ct**2)
    ph = rng.uniform(0.0, 2 * np.pi, n)
    x = 0.7 * R * np.stack([st * np.cos(ph), st * np.sin(ph), ct], axis=1)
    v = np.zeros((n, 3))
    v[:, 2] = 5.0
    a = anatomi(_yaz(tmp_path, x, v, np.full(n, 1.0e5), R, 50.0))

    assert a["yonluluk"] > 0.95, a["yonluluk"]


def test_sure_yargisi_varis_suresini_kullanir(tmp_path: Path) -> None:
    """`2R` varış süresi koşulan `t`'den büyükse süre YETERSIZ demeli."""
    n, R = 300, 80.0
    x = _kure(n, 0.5 * R)                     # r = 40 m
    v = 0.2 * x / np.linalg.norm(x, axis=1)[:, None]   # v_r = 0,2 m/s
    # 2R - 40 = 120 m,  120 / 0,2 = 600 s
    a = anatomi(_yaz(tmp_path, x, v, np.full(n, 1.0e5), R, 100.0))

    assert a["ic_disa"]["varis_2R_s"] == pytest.approx(600.0, rel=1e-6)
    assert a["ic_disa"]["sure_yeterli_mi"] is False

    b = anatomi(_yaz(tmp_path, x, v, np.full(n, 1.0e5), R, 700.0))
    assert b["ic_disa"]["sure_yeterli_mi"] is True


def test_isaret_donusu_salinimi_yakalar(tmp_path: Path) -> None:
    """Bantlar arası eksenel işaret dönüşü sayılmalı."""
    R = 80.0
    # iki grup: yavas +z, hizli -z  -> iki bantta zit isaret
    x = np.array([[0.0, 0.0, 40.0], [0.0, 0.0, -40.0]])
    v = np.array([[0.0, 0.0, 0.05], [0.0, 0.0, -5.0]])
    a = anatomi(_yaz(tmp_path, x, v, np.array([1e5, 1e5]), R, 50.0))

    # her ikisi de DISARI gidiyor (v_r > 0) ama eksenel isaretleri zit
    assert a["n_disa"] == 2
    assert a["isaret_donusu"] >= 1


def test_korunum_ve_kontrol_yuzeyi_sayimlari(tmp_path: Path) -> None:
    """`r > R` ve `r > 2R` sayımları ayrı olmalı."""
    R = 80.0
    x = np.array([[0.0, 0.0, 40.0],     # icte
                  [0.0, 0.0, 120.0],    # R < r < 2R
                  [0.0, 0.0, 200.0]])   # r > 2R
    v = np.zeros((3, 3))
    v[:, 2] = 1.0
    a = anatomi(_yaz(tmp_path, x, v, np.full(3, 1e5), R, 10.0))

    assert a["n_r_ustu_R"] == 2
    assert a["n_r_ustu_2R"] == 1
    # p_toplam = 3 * 1e5 * 1 = 3e5
    assert a["p_toplam_buyukluk"] == pytest.approx(3.0e5, rel=1e-12)


def test_ayristirma_alan_yoksa_ACIKCA_soyluyor(tmp_path: Path) -> None:
    """Eski dosyada `mermi_kesri` yok — sessizce sıfır varsayılmamalı."""
    n, R = 100, 80.0
    x = _kure(n, 0.5 * R)
    v = np.zeros((n, 3))
    v[:, 2] = 1.0
    a = anatomi(_yaz(tmp_path, x, v, np.full(n, 1e5), R, 10.0))
    assert a["ayristirma"]["var"] is False
    assert "mermi_kesri" in a["ayristirma"]["neden"]


def _yaz_kesirli(tmp: Path, x, v, m, f, R, t) -> Path:
    y = tmp / "durum_kesirli.npz"
    np.savez(y, x=np.asarray(x, np.float64), v=np.asarray(v, np.float64),
             m=np.asarray(m, np.float64),
             mermi_kesri=np.asarray(f, np.float64),
             R=np.float64(R), t=np.float64(t))
    return y


def test_ayristirma_mermi_ve_hedefi_kutle_payina_gore_boluyor(
        tmp_path: Path) -> None:
    """Karışım parçacığının momentumu tek tarafa yazılmamalı."""
    R = 80.0
    # Ucu de 2R disinda; kesirler 1 / 0 / 0,25
    x = np.array([[0.0, 0.0, 200.0], [0.0, 0.0, 210.0], [0.0, 0.0, 220.0]])
    v = np.zeros((3, 3))
    v[:, 2] = -10.0
    m = np.array([100.0, 100.0, 400.0])
    f = np.array([1.0, 0.0, 0.25])
    a = anatomi(_yaz_kesirli(tmp_path, x, v, m, f, R, 50.0))
    ay = a["ayristirma"]
    assert ay["var"] is True
    # mermi kutlesi = 100 + 0,25*400 = 200 ; hedef = 100 + 300 = 400
    assert ay["mermi_kutlesi_kacan"] == pytest.approx(200.0, rel=1e-12)
    assert ay["hedef_kutlesi_kacan"] == pytest.approx(400.0, rel=1e-12)
    assert ay["p_eksen_mermi"] == pytest.approx(-2000.0, rel=1e-12)
    assert ay["p_eksen_hedef"] == pytest.approx(-4000.0, rel=1e-12)
    assert ay["hedef_payi"] == pytest.approx(2.0 / 3.0, rel=1e-12)


def test_ayristirma_yalniz_mermi_kacinca_hedef_payi_sifir(
        tmp_path: Path) -> None:
    """A17'nin durumu: kaçanların tamamı mermi ⇒ hedef payı `0`."""
    R = 80.0
    x = np.array([[0.0, 0.0, 200.0], [0.0, 0.0, 40.0]])
    v = np.zeros((2, 3))
    v[:, 2] = -10.0
    a = anatomi(_yaz_kesirli(tmp_path, x, v, np.array([100.0, 1e6]),
                             np.array([1.0, 0.0]), R, 50.0))
    ay = a["ayristirma"]
    assert ay["hedef_payi"] == pytest.approx(0.0)
    assert ay["hedef_kutlesi_kacan"] == pytest.approx(0.0)
