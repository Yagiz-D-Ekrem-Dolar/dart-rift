"""KAYIT-073 — `β`'nın üç çarpanı ve toplam kuralı."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables import ejekta_ayrismasi as EA

P_MERMI = 579.4 * 6144.9


def test_olculen_ayrisma_kayitta():
    assert sorted(EA.OLCULEN_AYRISMA) == [1.0, 10.0, 50.0]
    M = [EA.OLCULEN_AYRISMA[y][0] for y in sorted(EA.OLCULEN_AYRISMA)]
    v = [EA.OLCULEN_AYRISMA[y][1] for y in sorted(EA.OLCULEN_AYRISMA)]
    k = [EA.OLCULEN_AYRISMA[y][2] for y in sorted(EA.OLCULEN_AYRISMA)]
    assert M == sorted(M, reverse=True)       # dayanim artinca daha AZ kaciyor
    assert v == sorted(v)                      # ama kacan daha HIZLI
    assert k == sorted(k)                      # ve daha TOPLU


def test_toplam_kurali_TUTUYOR_ve_goturme_var():
    """Üç üs toplanıp `β`'nın üssünü veriyor — `%1,3` içinde."""
    r = EA.ayrisma_ussleri()
    assert r["usler"]["M_kacan"] == pytest.approx(-0.3221, abs=0.001)
    assert r["usler"]["v_ort"] == pytest.approx(+0.1866, abs=0.001)
    assert r["usler"]["kos_ort"] == pytest.approx(+0.0585, abs=0.001)
    assert r["toplam"] == pytest.approx(-0.0769, abs=0.001)
    assert r["b_ussu"] == pytest.approx(-0.0760, abs=0.001)
    assert r["bagil_fark"] == pytest.approx(0.013, abs=0.003)
    assert r["toplam_kurali"] == "TUTUYOR"
    # Kaydin ana iddiasi: goturme
    assert r["M_kazanci"] == pytest.approx(4.2, abs=0.1)
    assert "GOTURME VAR" in r["goturme"]


def test_oncarpan_sabit_ve_kayitta():
    """`M·v·kos/(p·b)` üç koşuda `0,8347 ± 0,0052`."""
    oranlar = [M * v * k / (P_MERMI * b)
               for M, v, k, b in EA.OLCULEN_AYRISMA.values()]
    assert np.mean(oranlar) == pytest.approx(EA.ONCARPAN_K, abs=0.001)
    assert np.std(oranlar) == pytest.approx(EA.ONCARPAN_K_SD, abs=0.001)
    # Y0 boyunca yalnız %1,4 degisiyor -> oncarpan SABIT sayilabilir
    assert max(oranlar) / min(oranlar) - 1.0 < 0.02


def _sentetik(n=600, hiz=0.5, yayilim=0.3, tohum=3):
    """Eksen çevresinde toplu, bilinen bir ejekta bulutu."""
    rng = np.random.default_rng(tohum)
    yon = rng.normal(size=(n, 3))
    yon[:, 2] = abs(yon[:, 2]) / max(yayilim, 1e-9)      # +z'de topla
    yon /= np.linalg.norm(yon, axis=1, keepdims=True)
    v = yon * hiz
    return v, np.full(n, 1.0e4)


def test_bilesenler_sentetik_bulutta_dogru():
    v, m = _sentetik(hiz=0.5)
    r = EA.ejekta_bilesenleri(v, m, ehat=np.array([0.0, 0.0, -1.0]),
                              v_esc=0.1, p_mermi=P_MERMI)
    assert r["n_kacan"] == len(m)
    assert r["M_kacan"] == pytest.approx(m.sum())
    assert r["v_ort"] == pytest.approx(0.5)              # hepsi ayni hizda
    assert 0.0 < r["kos_ort"] <= 1.0
    assert r["carpim"] == pytest.approx(r["M_kacan"] * r["v_ort"] * r["kos_ort"])
    assert r["b_tahmin"] == pytest.approx(
        EA.ONCARPAN_K * r["carpim"] / P_MERMI)


def test_daha_toplu_bulut_daha_buyuk_kosinus():
    ehat = np.array([0.0, 0.0, -1.0])
    k = []
    for yayilim in (1.0, 0.3, 0.05):
        v, m = _sentetik(yayilim=yayilim)
        k.append(EA.ejekta_bilesenleri(v, m, ehat=ehat, v_esc=0.1)["kos_ort"])
    assert k == sorted(k)                                # topluluk arttikca kos artar
    assert k[-1] > 0.9           # kucuk |z| cekenler kuyrugu birakiyor


def test_kacis_esigi_altinda_kalan_sayilmaz():
    v, m = _sentetik(hiz=0.5)
    r = EA.ejekta_bilesenleri(v, m, ehat=np.array([0.0, 0.0, -1.0]), v_esc=0.1)
    with pytest.raises(ValueError, match="kacan parcacik"):
        EA.ejekta_bilesenleri(v, m, ehat=np.array([0.0, 0.0, -1.0]), v_esc=0.9)
    assert r["M_kacan"] > 0.0


def test_mermi_kesri_disarida_birakiliyor():
    v, m = _sentetik(hiz=0.5)
    mk = np.zeros(len(m))
    mk[:100] = 1.0
    ehat = np.array([0.0, 0.0, -1.0])
    tam = EA.ejekta_bilesenleri(v, m, ehat=ehat, v_esc=0.1)
    hedef = EA.ejekta_bilesenleri(v, m, ehat=ehat, v_esc=0.1, mermi_kesri=mk)
    assert hedef["n_kacan"] == tam["n_kacan"] - 100
    assert hedef["M_kacan"] < tam["M_kacan"]


def test_gecersiz_girdiler():
    v, m = _sentetik()
    ehat = np.array([0.0, 0.0, -1.0])
    with pytest.raises(ValueError):
        EA.ejekta_bilesenleri(v[:, :2], m, ehat=ehat, v_esc=0.1)
    with pytest.raises(ValueError):
        EA.ejekta_bilesenleri(v, m, ehat=np.zeros(3), v_esc=0.1)
    with pytest.raises(ValueError):
        EA.ejekta_bilesenleri(v, m, ehat=ehat, v_esc=0.0)
    with pytest.raises(ValueError):
        EA.ejekta_bilesenleri(v, m, ehat=ehat, v_esc=0.1, p_mermi=0.0)
    with pytest.raises(ValueError):
        EA.ayrisma_ussleri({1.0: (1.0, 1.0, 1.0, 1.0)})
    with pytest.raises(ValueError):
        EA.ayrisma_ussleri({1.0: (1.0, 1.0, 1.0, 1.0), 2.0: (1.0, -1.0, 1.0, 1.0)})
    with pytest.raises(ValueError):
        EA.ayrisma_ussleri({0.0: (1.0, 1.0, 1.0, 1.0), 2.0: (1.0, 1.0, 1.0, 1.0)})


def test_toplam_kurali_TUTMUYOR_dalini_de_veriyor():
    """Uydurma bir seride kural düşerse rapor bunu söyler."""
    bozuk = {1.0: (1.0e7, 1.0, 0.5, 3.0), 10.0: (0.5e7, 1.0, 0.5, 3.0)}
    r = EA.ayrisma_ussleri(bozuk)
    assert r["toplam_kurali"] == "TUTMUYOR"


def test_ileri_kosu_ayrismayi_TANI_olarak_yaziyor():
    """Havuz başlamadan önce bağlandı: her koşu üç çarpanı kaydedecek.

    Yapısal sınav — warp CPU yerelde engelli (A113), bu yüzden gerçek koşu
    yerine bağlantının kodda olduğu sınanıyor. İlk gerçek koşusu PROTOKOL-DO.
    """
    import inspect

    from dartrift.inference import forward as FW
    kaynak = inspect.getsource(FW)
    assert 'fizik_tani["ejekta_ayrismasi"]' in kaynak
    assert "from ..observables.ejekta_ayrismasi import ejekta_bilesenleri" in kaynak
    # Tani basarisiz olursa kosu DUSMEMELI: hata kayda girer
    i = kaynak.index('fizik_tani["ejekta_ayrismasi"] = ejekta_bilesenleri')
    kuyruk = kaynak[i:i + 700]
    assert "except Exception" in kuyruk and '{"hata"' in kuyruk
    # KAPI olmadigi yazili
    assert "KAPI DEGIL" in kaynak[i - 400:i]
