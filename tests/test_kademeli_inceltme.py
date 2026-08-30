"""Kademeli inceltme — arayüz basamağı merdivene yayılıyor mu (A25).

Tek basamaklı inceltmede `λ = 20` şu arayüzü üretiyor: ince parçacık
`46,6 kg`, hemen dışındaki `372 834 kg` — **oran `8 000`** — ve
şoklanan `73` tonun tamamının momentumu tek bir kaba parçacığı şok
hızına çıkarmaya `107` kat yetmiyor.

Burada kilitlenen: merdivenin **sırası** (yanlış sıra sessizce daha
kötü bir sahne üretirdi) ve mermi `h`'sinin **en ince** seviyeye
bağlanması.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from arayuz_orani import kademe_onerisi, oranlar  # noqa: E402

from dartrift.setup.refine import refine_scene_kademeli  # noqa: E402


class _Sahte:
    """Kafes kurulumunu koşmadan **doğrulama** yollarını sınamak için."""

    spacing = 7.0
    impact_point = np.array([0.0, 0.0, 82.0])
    target_radius = 82.0
    impact_direction = np.array([0.0, 0.0, -1.0])
    surface_normal = np.array([0.0, 0.0, 1.0])
    x = np.zeros((1, 3))
    m = np.ones(1)
    alpha0 = np.ones(1)
    Y0 = np.ones(1)
    is_boulder = np.zeros(1, bool)
    is_impactor = np.zeros(1, bool)


def test_TEK_kademe_reddediliyor() -> None:
    with pytest.raises(ValueError, match="en az iki kademe"):
        refine_scene_kademeli(_Sahte(), None, [(3.0, 20.0)])


def test_YARICAP_sirasi_zorunlu() -> None:
    """Dıştan içe **azalmalı**; ters sıra sessizce geçmemeli."""
    with pytest.raises(ValueError, match="DISTAN ICE azalmali"):
        refine_scene_kademeli(_Sahte(), None, [(3.0, 2.0), (12.0, 20.0)])


def test_LAM_sirasi_zorunlu() -> None:
    """İç bölge **daha ince** olmalı — `lam` dıştan içe artmalı."""
    with pytest.raises(ValueError, match="DISTAN ICE artmali"):
        refine_scene_kademeli(_Sahte(), None, [(12.0, 20.0), (3.0, 2.0)])


def test_esit_lam_de_reddediliyor() -> None:
    with pytest.raises(ValueError, match="DISTAN ICE artmali"):
        refine_scene_kademeli(_Sahte(), None, [(12.0, 5.0), (3.0, 5.0)])


# --------------------------------------------- merdivenin ARITMETIGI

def _kutleler(spacing: float, lamlar) -> np.ndarray:
    """Verilen `lam` merdiveninin parçacık kütleleri (`m ~ s³`)."""
    rho = 2700.0 / 1.7564
    return np.array([0.707 * (spacing / lam) ** 3 * rho for lam in lamlar])


def test_TEK_BASAMAK_olculen_orani_yeniden_uretiyor() -> None:
    """`λ = 20` ve kaba `λ = 1`: `8 000`."""
    o = oranlar(_kutleler(7.0, [20.0, 1.0]))
    assert o["en_dik"] == pytest.approx(8000.0, rel=1e-6)
    assert o["yargi"] == "TEHLIKELI"


def test_MERDIVEN_basamagi_OLAGAN_a_indiriyor() -> None:
    """`20 -> 10 -> 5 -> 2,5 -> 1,25 -> 1`: her basamak `8×`."""
    o = oranlar(_kutleler(7.0, [20.0, 10.0, 5.0, 2.5, 1.25, 1.0]))
    assert o["en_dik"] <= 8.0 + 1e-9
    assert o["yargi"] == "OLAGAN"
    assert len(o["oranlar"]) == 5


def test_kademe_onerisi_MERDIVEN_uzunlugunu_veriyor() -> None:
    """`8 000` -> `4` ara seviye; merdiven `20,10,5,2.5,1.25` = `4` ara."""
    assert kademe_onerisi(8000.0) == 4
    ara = [10.0, 5.0, 2.5, 1.25]
    assert len(ara) == kademe_onerisi(8000.0)


def test_EKSIK_merdiven_hala_tehlikeli() -> None:
    """Üç seviyeli yol bir ara seviye ekliyor — gerekenin dörtte biri."""
    o = oranlar(_kutleler(7.0, [20.0, 8.0, 1.0]))
    assert o["yargi"] == "TEHLIKELI"
    assert o["en_dik"] > 100.0


# ---------------------------------------------- kosucuya BAGLANMA

def test_faz48_kademeler_bayragi_var_ve_TEK_ASAMA_zorunlu() -> None:
    """İki aşamalı yolda aktarım merdiveni kabalaştırır (A24/A25).

    Bayrağı sessizce kabul edip aktarımda öğütmek, bu deponun tam
    olarak kaçındığı hata sınıfı: kullanıcı çareyi uyguladığını
    **sanır**.
    """
    import inspect
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz48_iki_asama as f
    k = inspect.getsource(f.main)
    assert '"--kademeler"' in k
    assert "yalnizca --tek-asama ile" in k
    assert "refine_scene_kademeli(kaba, mesh, kad)" in k


def test_kademe_sinavi_MERDIVEN_kurabiliyor() -> None:
    import inspect
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import kademe_sinavi as ks
    k = inspect.getsource(ks.main)
    assert "refine_scene_kademeli(kaba, mesh, kad)" in k
    # cephe yargisi EN IC yaricapa gore olmali, r1'e degil
    assert 'a.kademeler[-1].split(":")[0]' in k


# ------------------------------------------------ OZ-BENZER merdiven

def test_ozbenzer_s_bolu_r_SABIT_tutuyor() -> None:
    """Elle yazılan merdiven dıştan içe bozuluyordu (`0,058 -> 0,233`)."""
    from dartrift.setup.refine import ozbenzer_kademeler
    k = ozbenzer_kademeler(3.5, 3.0, 0.175, 24.0)
    oranlar_sr = [(3.5 / lam) / r for r, lam in k]
    assert max(oranlar_sr) - min(oranlar_sr) < 1e-9
    assert oranlar_sr[0] == pytest.approx(0.175 / 3.0, rel=1e-9)


def test_ozbenzer_DISTAN_ICE_donuyor() -> None:
    """`refine_scene_kademeli` dıştan içe bekliyor; sıra yanlışsa atar."""
    from dartrift.setup.refine import ozbenzer_kademeler
    k = ozbenzer_kademeler(3.5, 3.0, 0.175, 24.0)
    r = [r for r, _ in k]
    lam = [lam for _, lam in k]
    assert r == sorted(r, reverse=True)      # azalan
    assert lam == sorted(lam)                # artan


def test_ozbenzer_r_disi_KAPSIYOR_ve_gerekirse_asiyor() -> None:
    """`r_dış`'a **ulaşmalı**; tabana bağlanmak için **aşabilir**.

    Sözleşme bilerek *"tam eşit"* değil: merdiven `s_dış`'ta bitip
    tabana atlarsa orada `15,6×` artık sıçrama kalıyordu. Kapatmak
    için birkaç kademe daha gerekebilir ve o kademeler `r_dış`'ın
    ötesine düşer.
    """
    from dartrift.setup.refine import ozbenzer_kademeler
    k = ozbenzer_kademeler(3.5, 3.0, 0.175, 24.0)
    assert max(r for r, _ in k) >= 24.0
    # ama gereksiz yere buyumemeli: son kademe tabanin yarisini yeni gecmis
    s_dis = 3.5 / k[0][1]
    assert s_dis < 3.5 and s_dis >= 3.5 / 2.0 * (1 - 1e-9)


def test_OKTAV_maliyeti_r_den_BAGIMSIZ() -> None:
    """`N = 20,7 (r/s)³` — her oktav aynı maliyette.

    Bu, kraterin yarıçapına ulaşmanın **geometrik** olarak ucuz
    olmasının sebebi ve `ozbenzer_kademeler`'in belgelediği yasa.
    """
    def n_oktav(r: float, s: float) -> float:
        V = (14.0 / 3.0) * np.pi * r ** 3          # r -> 2r, yarim kure
        return V / (0.707 * s ** 3)
    # ayni r/s, farkli r -> ayni N
    assert n_oktav(3.0, 3.0 / 8.6) == pytest.approx(n_oktav(24.0, 24.0 / 8.6),
                                                    rel=1e-9)
    # ve katsayi 20,7
    assert n_oktav(1.0, 1.0) == pytest.approx(20.7, rel=0.01)


def test_ozbenzer_bozuk_girdi_REDDEDIYOR() -> None:
    from dartrift.setup.refine import ozbenzer_kademeler
    with pytest.raises(ValueError, match="r_ic < r_dis"):
        ozbenzer_kademeler(3.5, 24.0, 0.175, 3.0)
    with pytest.raises(ValueError, match="s_ic pozitif"):
        ozbenzer_kademeler(3.5, 3.0, 0.0, 24.0)
    with pytest.raises(ValueError, match="kat > 1"):
        ozbenzer_kademeler(3.5, 3.0, 0.175, 24.0, kat=1.0)


def test_izgara_arama_KABA_KUVVETLE_ayni() -> None:
    """Hız için yazıldı; **sonucu değiştirmemeli**.

    `refine_scene_ucseviye` de bu yola geçti, yani iki aşamalı bütün
    koşular buna bağlı. Rastgele bulutta birebir eşitlik aranıyor.
    """
    from dartrift.setup.refine import _en_yakin_indeks
    rng = np.random.default_rng(7)
    h = rng.uniform(-30, 30, (2000, 3))
    q = rng.uniform(-25, 25, (600, 3))
    izgara = _en_yakin_indeks(h, q, 7.0)
    kaba = np.array([np.argmin(np.linalg.norm(h - p, axis=1)) for p in q])
    assert (izgara == kaba).all()


def test_izgara_arama_UZAK_sorguda_yaricapi_BUYUTUYOR() -> None:
    """Hücre içinde komşu yoksa sessizce yanlış komşu **dönmemeli**."""
    from dartrift.setup.refine import _en_yakin_indeks
    h = np.array([[0.0, 0.0, 0.0]])
    q = np.array([[50.0, 0.0, 0.0]])          # hucrenin cok otesinde
    assert _en_yakin_indeks(h, q, 1.0)[0] == 0


def test_izgara_arama_BOS_hedefi_REDDEDIYOR() -> None:
    from dartrift.setup.refine import _en_yakin_indeks
    with pytest.raises(ValueError, match="hedef_x bos"):
        _en_yakin_indeks(np.zeros((0, 3)), np.zeros((1, 3)), 1.0)


def test_ozbenzer_TABANA_kadar_kapaniyor() -> None:
    """Merdiven `s_dış`'ta bitip tabana atlarsa **artık sıçrama** kalır.

    Ölçüldü (`2026-08-29`): `r_dış = 24` ile merdiven `s = 1,4`'te
    bitiyor ve tabana (`3,5`) `2,5×` aralık = `15,6×` kütle
    sıçraması kalıyordu. Araç `9×` diye raporladı çünkü blok/matris
    farkı araya giriyor — yani kusur **gizlenmişti**.
    """
    from dartrift.setup.refine import ozbenzer_kademeler
    spacing = 3.5
    k = ozbenzer_kademeler(spacing, 3.0, 0.175, 24.0)
    s_dis = spacing / k[0][1]                    # en DIS kademe
    assert s_dis >= spacing / 2.0 * (1 - 1e-9), s_dis
    assert (spacing / s_dis) ** 3 <= 8.0 + 1e-9  # tabana son sicrama


def test_ozbenzer_ic_basamaklar_hepsi_SEKIZ() -> None:
    from dartrift.setup.refine import ozbenzer_kademeler
    spacing = 3.5
    k = ozbenzer_kademeler(spacing, 3.0, 0.175, 24.0)
    s = [spacing / lam for _, lam in k]           # distan ice, azalan
    oran = [(s[i] / s[i + 1]) ** 3 for i in range(len(s) - 1)]
    assert all(abs(o - 8.0) < 1e-6 for o in oran), oran


def test_ozbenzer_KABUK_KALINLIGI_hepsi_yeterli() -> None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from arayuz_orani import kabuk_kalinligi

    from dartrift.setup.refine import ozbenzer_kademeler
    kk = kabuk_kalinligi(ozbenzer_kademeler(3.5, 3.0, 0.175, 24.0), 3.5)
    assert all(d["yeterli"] for d in kk)


# ------------------------------- KADEME AYRISTIRICI: metre, lam DEGIL

def test_ayristirici_TABANDAN_bagimsiz_ayni_araligi_veriyor() -> None:
    """Kusurun özü: `λ` tabana bağlıydı, iki betiğin tabanı farklıydı.

    `kademe_sinavi.py` `spacing = 3,5`, `faz48_iki_asama.py`
    varsayılan `7,0`. Aynı `"3:20"` dizgisi birinde `s = 0,175`,
    ötekinde `s = 0,350` demekti — ve **hiçbir şey hata vermedi**.
    TRUBA `J4` merdiveni `N = 131 057` yerine `17 201` parçacıkla
    kurdu, koşu iki kat kaba gitti (`β = 1,216`).
    """
    from dartrift.setup.refine import kademe_ayristir
    for taban in (3.5, 7.0, 14.0):
        k = kademe_ayristir(["48:2.8", "3:0.175"], taban)
        s = [taban / lam for _, lam in k]
        assert s == pytest.approx([2.8, 0.175]), (taban, s)


def test_ayristirici_TABANDAN_BUYUK_araligi_REDDEDIYOR() -> None:
    """Tabandan kaba bir 'inceltme' sessizce sahneyi bozardı."""
    from dartrift.setup.refine import kademe_ayristir
    with pytest.raises(ValueError, match="BUYUK olamaz"):
        kademe_ayristir(["3:9.0"], 7.0)


def test_ayristirici_bozuk_bicimi_REDDEDIYOR() -> None:
    from dartrift.setup.refine import kademe_ayristir
    with pytest.raises(ValueError, match="'r:s' biciminde"):
        kademe_ayristir(["3"], 7.0)
    with pytest.raises(ValueError, match="pozitif"):
        kademe_ayristir(["0:0.175"], 7.0)


def test_her_iki_betik_de_AYRISTIRICIYI_kullaniyor() -> None:
    """Biri elle ayrıştırmaya dönerse kusur geri gelir."""
    import inspect
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz48_iki_asama as f
    import kademe_sinavi as ks
    assert "kademe_ayristir(a.kademeler, a.spacing)" in inspect.getsource(f.main)
    assert "kademe_ayristir(a.kademeler, kaba.spacing)" in \
        inspect.getsource(ks.main)
