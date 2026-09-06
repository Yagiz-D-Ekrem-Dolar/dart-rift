"""hiz_tanisi: M(>v) dagilimi bilinen kurulusta dogru mu."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_yol = Path(__file__).resolve().parents[1] / "scripts" / "hiz_tanisi.py"
_spec = importlib.util.spec_from_file_location("hiz_tanisi", _yol)
ht = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ht)


def _sahne(hizlar, *, R=10.0, m_p=1.0, mermi=None):
    """Her parcacik R'nin hemen disinda, +x yonunde `v_r` ile."""
    n = len(hizlar)
    x = np.zeros((n, 3))
    x[:, 0] = R * 1.01
    v = np.zeros((n, 3))
    v[:, 0] = hizlar
    return {
        "x": x,
        "v": v,
        "m": np.full(n, m_p),
        "R": np.array(R),
        "v_esc": np.array(0.082),
        "t": np.array(0.2),
        "mermi_kesri": np.zeros(n) if mermi is None else np.asarray(mermi),
    }


def test_esik_ustu_kutle_dogru():
    h = ht.hiz_yapisi(_sahne([0.05, 0.5, 5.0, 50.0, 500.0]))
    d = {x["v_esik"]: x for x in h["dis_dagilim"]}
    assert d[0.0]["n"] == 5
    assert d[0.082]["n"] == 4          # 0,05 elenir
    assert d[1.0]["n"] == 3
    assert d[10.0]["n"] == 2
    assert d[100.0]["n"] == 1
    assert d[1000.0]["n"] == 0
    assert d[1.0]["M"] == pytest.approx(3.0)


def test_mermi_disarida_birakilir():
    # ikisi mermi (mermi_kesri=1), ucu hedef
    h = ht.hiz_yapisi(_sahne([1.0] * 5, mermi=[1.0, 1.0, 0.0, 0.0, 0.0]))
    assert h["N_hedef"] == 3
    d = {x["v_esik"]: x for x in h["dis_dagilim"]}
    assert d[0.082]["n"] == 3


def test_icerdeki_akis_ayri_sayilir():
    s = _sahne([100.0, 100.0])
    s["x"][0, 0] = 1.0                 # birini iceri al
    h = ht.hiz_yapisi(s)
    dis = {x["v_esik"]: x for x in h["dis_dagilim"]}
    ic = {x["v_esik"]: x for x in h["ic_dagilim"]}
    assert dis[10.0]["n"] == 1
    assert ic[10.0]["n"] == 1


def test_ustel_yasa_egimi_geri_gelir():
    # M(>v) = C v^-1.5 kuracak sekilde kutle ata
    v = np.array([0.082, 0.5, 1.0, 10.0, 100.0, 1000.0])
    kum = 1.0e6 * v ** -1.5            # istenen kumulatif
    kutle = np.diff(np.append(kum, 0.0)) * -1.0
    hizlar, agirlik = [], []
    for vi, mi in zip(v, kutle):
        hizlar.append(vi * 1.0001)     # esigin hemen ustunde
        agirlik.append(mi)
    s = _sahne(hizlar)
    s["m"] = np.array(agirlik)
    h = ht.hiz_yargi = ht.hiz_yapisi(s)
    e = ht.egim(h["dis_dagilim"], 0.08, 1000.0)
    assert e == pytest.approx(-1.5, abs=0.05)


def test_kacan_seviye_kutleye_gore_ayrisir():
    s = _sahne([1.0] * 6)
    s["m"] = np.array([5.83, 5.83, 5.83, 372.8, 372.8, 46.6])
    h = ht.hiz_yapisi(s)
    sev = {round(x["m_p"], 3): x["n"] for x in h["kacan_seviye"]}
    assert sev == {5.83: 3, 372.8: 2, 46.6: 1}


def test_bos_kacan_cokmez():
    h = ht.hiz_yapisi(_sahne([0.001, 0.002]))
    assert h["kacan_hiz"] is None
    assert h["kacan_seviye"] == []


# --- ezilme mi sok mu ---------------------------------------------------

def _durum(rho, alpha0, *, m=1.0, mermi=None):
    n = len(rho)
    return {
        "rho": np.asarray(rho, dtype=float),
        "alpha0": np.asarray(alpha0, dtype=float),
        "m": np.full(n, m, dtype=float),
        "mermi_kesri": np.zeros(n) if mermi is None else np.asarray(mermi, float),
    }


def test_salt_gozenek_kapanmasi_sok_sayilmaz():
    """rho < rho0_kati iken sikisma YALNIZ gozenek kapanmasidir."""
    # a0 = 1,7564, rho = 2233 -> sikisma %45,3, bandin ICINDE
    e = ht.ezilme_mi_sok_mu(_durum([2233.0], [1.7564]))
    assert e["sikisma_max"] == pytest.approx(45.28, abs=0.1)
    assert e["n_kati_sikisan"] == 0            # rho < 2700
    assert e["en_sikisan"]["rho_bolu_rho0_kati"] < 1.0
    assert e["en_sikisan"]["gozenek_tavani"] == pytest.approx(75.64, abs=0.01)
    assert e["en_sikisan"]["tavanin_altinda"] is True


def test_kati_sikismasi_ayirt_edilir():
    e = ht.ezilme_mi_sok_mu(_durum([2233.0, 3000.0], [1.7564, 1.7564]))
    assert e["n_kati_sikisan"] == 1
    assert e["rho_max"] == pytest.approx(3000.0)
    assert e["en_sikisan"]["rho_bolu_rho0_kati"] > 1.0


def test_gozenek_tavani_asilirsa_isaretlenir():
    """a0 = 1,05 (blok) ile %45 sikisma gozenekle ACIKLANAMAZ."""
    rho = 2700.0 * 1.45 / 1.05          # sikisma %45, a0 = 1,05
    e = ht.ezilme_mi_sok_mu(_durum([rho], [1.05]))
    assert e["sikisma_max"] == pytest.approx(45.0, abs=0.1)
    assert e["en_sikisan"]["gozenek_tavani"] == pytest.approx(5.0, abs=0.01)
    assert e["en_sikisan"]["tavanin_altinda"] is False
    assert e["n_kati_sikisan"] == 1     # rho = 3728 > 2700


def test_ezilme_durumu_sayimi():
    a0 = 1.7564
    bakir = 2700.0 / a0                 # hic ezilmemis
    e = ht.ezilme_mi_sok_mu(_durum([bakir, 2200.0, 2700.0], [a0, a0, a0]))
    assert e["n_bakir"] == 1
    assert e["n_kismen_ezilmis"] == 1
    assert e["n_tam_ezilmis"] == 1


def test_mermi_ezilmede_de_disarida():
    e = ht.ezilme_mi_sok_mu(
        _durum([2233.0, 9000.0], [1.7564, 1.7564], mermi=[0.0, 1.0])
    )
    assert e["rho_max"] == pytest.approx(2233.0)   # mermi sayilmadi
    assert e["n_kati_sikisan"] == 0


def test_gozeneksiz_kolda_sayisal_artik_sok_sanilmaz():
    """`alpha0 = 1` iken baslangic yogunlugu ZATEN rho0_kati.

    Olculen: gozeneksiz kolda `rho_max = 2700,1` idi ve paysiz sinav
    `16 762` parcacigi "kati sikismis" saydi. Hepsi sayisal artik.
    """
    e = ht.ezilme_mi_sok_mu(_durum([2700.1, 2700.05, 2699.9], [1.0, 1.0, 1.0]))
    assert e["n_kati_sikisan"] == 0
    # gercek sikisma hala gorunur
    e2 = ht.ezilme_mi_sok_mu(_durum([2700.1, 3500.0], [1.0, 1.0]))
    assert e2["n_kati_sikisan"] == 1


# --- A61: kumelenme denetimi --------------------------------------------

def _kume(konumlar, *, m_p=5.826, a0=1.7564):
    n = len(konumlar)
    return {
        "x": np.asarray(konumlar, dtype=float),
        "m": np.full(n, m_p),
        "rho": np.full(n, 2900.0),      # hepsi "kati sikismis" gorunsun
        "alpha0": np.full(n, a0),
        "mermi_kesri": np.zeros(n),
    }


def test_kumelenme_olculen_kusuru_yakaliyor():
    """A61'in gerçek sayıları: `0,2013 m` komşu, `0,35 m` aralık."""
    # nominal aralik: (m / (2700/1,7564))^(1/3) = 0,1494... -> kendi
    # olcegimizi kuralim: m_p'yi araliga gore sec
    aralik = 0.35
    rho_y = 2700.0 / 1.7564
    m_p = rho_y * aralik ** 3
    x = np.array([[i * 0.2013, 0.0, 0.0] for i in range(8)])
    e = ht.ezilme_mi_sok_mu(_kume(x, m_p=m_p))
    assert e["kumelenme_olculdu"] is True
    assert e["nominal_aralik"] == pytest.approx(aralik, rel=1e-9)
    assert e["komsu_orani"] == pytest.approx(0.2013 / aralik, rel=1e-6)
    assert e["kumelenmis"] is True
    assert e["sahte_yogunluk_kati"] == pytest.approx(5.26, abs=0.05)


def test_duzgun_paketleme_kumelenmis_sayilmaz():
    aralik = 0.35
    m_p = (2700.0 / 1.7564) * aralik ** 3
    x = np.array([[i * aralik * 0.95, 0.0, 0.0] for i in range(8)])
    e = ht.ezilme_mi_sok_mu(_kume(x, m_p=m_p))
    assert e["kumelenmis"] is False
    assert e["komsu_orani"] == pytest.approx(0.95, rel=1e-6)


def test_esik_tam_sinirda():
    assert ht.KUMELENME_ESIGI == 0.75
    aralik = 0.35
    m_p = (2700.0 / 1.7564) * aralik ** 3
    for oran, beklenen in ((0.74, True), (0.76, False)):
        x = np.array([[i * aralik * oran, 0.0, 0.0] for i in range(6)])
        e = ht.ezilme_mi_sok_mu(_kume(x, m_p=m_p))
        assert e["kumelenmis"] is beklenen, f"oran {oran}"


def test_tek_parcacikta_olculmez():
    e = ht.ezilme_mi_sok_mu(_kume([[0.0, 0.0, 0.0]]))
    assert e["kumelenme_olculdu"] is False


def test_kati_sikisma_yoksa_kumelenme_de_olculmez():
    """`rho < rho0_kati` iken seçim boş → ölçüm yapılmaz."""
    s = _kume([[0.0, 0, 0], [0.3, 0, 0]])
    s["rho"] = np.full(2, 2200.0)
    e = ht.ezilme_mi_sok_mu(s)
    assert e["n_kati_sikisan"] == 0
    assert e["kumelenme_olculdu"] is False


def test_rapor_kumelenmeyi_yaziyor():
    aralik = 0.35
    m_p = (2700.0 / 1.7564) * aralik ** 3
    x = np.array([[i * 0.2013, 0.0, 0.0] for i in range(8)])
    e = ht.ezilme_mi_sok_mu(_kume(x, m_p=m_p))
    metin = ht.ezilme_raporu("sinav", e)
    assert "kumelenme" in metin
    assert "KUMELENMIS" in metin
    assert "SAHTE" in metin
