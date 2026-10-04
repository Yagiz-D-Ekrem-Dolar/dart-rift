"""ADR-0053 — önsel denetimi: ölçülen `β(Y₀)` eğrisinden kilitli yargı."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference import onsel_denetimi as OD


def _uy(tg: float = 1.0) -> OD.Uydurma:
    d = OD.OLCULEN_Y0_BETA[tg]
    Y = sorted(d)
    return OD.guc_yasasi_uydur(Y, [d[y] for y in Y])


def test_olculen_cifti_kayitta_ve_uretim_tgecisi_var():
    assert set(OD.OLCULEN_Y0_BETA) == {0.2, 1.0}      # 1,0 s = uretim (PROTOKOL-UG)
    for tg, d in OD.OLCULEN_Y0_BETA.items():
        assert set(d) == {1.0, 10.0, 50.0}, tg
        beta = [d[y] for y in sorted(d)]
        assert beta == sorted(beta, reverse=True)      # Y0 artarken beta DUSER


def test_guc_yasasi_uydurmasi_olculen_noktalara_oturuyor():
    uy = _uy()
    assert uy.p < 0.0 and uy.n == 3
    assert uy.Y_alt == 1.0 and uy.Y_ust == 50.0
    # Uc nokta ve kavis var: guc yasasi %5,3'e kadar oturuyor -- MUKEMMEL DEGIL,
    # ve bu yuzden PROTOKOL-DO olcumle dogrulatiyor (dusuk p, buyuk kaldirac).
    assert uy.artik_en_buyuk == pytest.approx(0.0525, abs=0.002)
    for y, b in OD.OLCULEN_Y0_BETA[1.0].items():
        assert OD.beta_tahmin(uy, y) == pytest.approx(b, rel=0.06)


def test_tam_tersinirlik():
    uy = _uy()
    for y in (0.5, 7.0, 123.0, 9e3):
        assert OD.y0_coz(uy, float(OD.beta_tahmin(uy, y))) == pytest.approx(y, rel=1e-9)


def test_duyarlilik_carpani_beta_nin_Y0_a_duyarsizligini_sayiya_ceviriyor():
    uy = _uy()
    # DY2'nin paydasi 0,447; b = 2,748 -> bagil 0,163
    c = OD.duyarlilik_carpani(uy, 0.447 / 2.748)
    assert c > 5.0                 # 1 sigma ~ bir dekaddan fazla Y0 belirsizligi
    assert OD.duyarlilik_carpani(OD.Uydurma(C=3.0, p=0.0, Y_alt=1.0, Y_ust=2.0,
                                            n=2, artik_en_buyuk=0.0),
                                 0.1) == float("inf")
    with pytest.raises(ValueError):
        OD.duyarlilik_carpani(uy, 0.0)


def test_uretim_onseli_1e3_1e7_gozlemi_ICERMIYOR():
    """ADR-0053'ün bulgusu: `DART_UZAYI_S3`'ün alt kenarı gözlemin **üstünde**.

    Bu sınav **DO koşularından önceki** durumu kayda geçirir. DO iki nokta
    eklediğinde uydurma değişir; yargı dönerse bu sınav düşer ve değişiklik
    **bilerek** yazılır (sessiz geçmez).
    """
    from dartrift.inference.design import DART_UZAYI_S3
    j = DART_UZAYI_S3.names.index("Y0")
    lo, hi = DART_UZAYI_S3.lo[j], DART_UZAYI_S3.hi[j]
    assert (lo, hi) == (1.0e3, 1.0e7)
    d = OD.onsel_denetle(_uy(), beta_gozlem=3.12, sigma_toplam=0.447,
                         onsel_lo=lo, onsel_hi=hi)
    assert d["genel"] == "ONSEL GOZLEMI ICERMIYOR"
    assert d["Y0_gozlem"] == pytest.approx(644.0, abs=5.0)
    assert d["dekad_alt_kenara"] < 0.0            # alt kenarin ALTINDA
    assert d["disdegerleme"] and d["cok_uzak"]    # 50 Pa'dan 1,11 dekad uzak


@pytest.mark.parametrize("lo,hi,genel", [
    (1.0e3, 1.0e7, "ONSEL GOZLEMI ICERMIYOR"),     # uretim onseli (ADR-0053)
    (3.0e2, 1.0e7, "GOZLEM ONSEL KENARINDA"),      # 644 Pa, kenara 0,33 dekad
    (1.0e5, 1.0e7, "ONSEL GOZLEMI ICERMIYOR"),     # tamami gozlemin ustunde
    (1.0e-2, 1.0e2, "ONSEL GOZLEMI ICERMIYOR"),    # tamami altinda
    (1.0e-1, 1.0e5, "ONSEL GOZLEMI ICERIYOR")])
def test_uc_yargi(lo, hi, genel):
    d = OD.onsel_denetle(_uy(), beta_gozlem=3.12, sigma_toplam=0.447,
                         onsel_lo=lo, onsel_hi=hi)
    assert d["genel"] == genel


def test_kenar_esigi_tam_sinirda_KENARDA_sayiyor():
    uy = _uy()
    y = OD.y0_coz(uy, 3.12)
    lo = y / 10 ** OD.ESIK_KENAR_DEKAD                  # tam esikte
    d = OD.onsel_denetle(uy, beta_gozlem=3.12, sigma_toplam=0.447,
                         onsel_lo=lo, onsel_hi=lo * 1e6)
    assert d["dekad_alt_kenara"] == pytest.approx(OD.ESIK_KENAR_DEKAD)
    assert d["genel"] == "GOZLEM ONSEL KENARINDA"       # <= kapsayici


def test_iki_tgecis_ayni_isareti_veriyor():
    """Yargı `t_geçiş` seçimine dayanmıyor: ikisi de kenarı işaret ediyor."""
    for tg in (0.2, 1.0):
        d = OD.onsel_denetle(_uy(tg), beta_gozlem=3.12, sigma_toplam=0.447,
                             onsel_lo=1.0e3, onsel_hi=1.0e7)
        assert d["genel"] != "ONSEL GOZLEMI ICERIYOR", tg
        assert d["beta_onsel_ust_kenarda"] < 3.12 - 0.34, tg   # ust kenar gozlemin ALTINDA


def test_gecersiz_girdiler():
    with pytest.raises(ValueError):
        OD.guc_yasasi_uydur([1.0], [3.0])
    with pytest.raises(ValueError):
        OD.guc_yasasi_uydur([1.0, 10.0], [3.0, 0.5])         # beta < 1
    with pytest.raises(ValueError):
        OD.guc_yasasi_uydur([0.0, 10.0], [3.0, 2.0])         # Y0 = 0
    uy = _uy()
    with pytest.raises(ValueError):
        OD.y0_coz(uy, 1.0)
    with pytest.raises(ValueError):
        OD.onsel_denetle(uy, beta_gozlem=3.12, sigma_toplam=0.4,
                         onsel_lo=1e7, onsel_hi=1e3)
    with pytest.raises(ValueError):
        OD.beta_tahmin(uy, [-1.0])


def test_cakilma_kuralina_baglanti_KODDA():
    """`recovery.C2` çakılmış ekseni saymıyor; bu modül aynı tuzağı önden yakalar.

    Yapısal sınav: `recovery` gerçekten `post.pinned` kullanıyor olmalı — yoksa
    kenara çakılan bir `Y₀` ekseni "en bilgilendirici" gibi görünür ve bu
    modülün uyarısının karşılığı kalmaz.
    """
    import inspect

    import dartrift.inference.recovery as R
    kaynak = inspect.getsource(R)
    assert ".pinned(" in kaynak and "oran_gecerli" in kaynak
    assert "C2" in OD.__doc__ and "kenara" in OD.__doc__.lower()


# ----------------------------------------- duyarlilik tablosu (ADR-0053 §3)
def _uretim_tablosu():
    sM = float(np.hypot(0.3 / 1.6, 0.15))        # L17 gozlem + gerceklem (KAYIT-070)
    return OD.duyarlilik_tablosu(OD.uretim_gozlemlileri(
        sigma_beta_toplam=0.447, beta_gozlem=3.12, sigma_M_bagil=sM))


def test_seriler_hepsi_Y0_da_TEKDUZE():
    """Dört gözlemlinin hepsi `Y₀`'da tekdüze — güç yasası anlamlı."""
    for ad, seri in OD.OLCULEN_Y0_SERILERI.items():
        d = [seri[y] for y in sorted(seri)]
        assert d == sorted(d, reverse=True), ad       # Y0 artarken hepsi DUSER
        assert sorted(seri) == [1.0, 10.0, 50.0], ad


def test_M_ejekta_Y0_u_beta_dan_COK_daha_iyi_sikistiriyor():
    """ADR-0053'ün ana ölçümü: `M_ejekta`'nın üssü `β`'nınkinden ~4 kat dik."""
    t = _uretim_tablosu()
    r = {s["ad"]: s for s in t["satirlar"]}
    assert r["beta"]["p"] == pytest.approx(-0.0760, abs=0.001)
    assert r["M_ejekta"]["p"] == pytest.approx(-0.3206, abs=0.001)
    assert abs(r["M_ejekta"]["p"] / r["beta"]["p"]) > 4.0
    # 1 sigma -> Y0 carpani: beta bir dekaddan fazla, M_ejekta ucte bir dekad
    assert r["beta"]["carpan_1sigma"] == pytest.approx(12.4, abs=0.2)
    assert r["M_ejekta"]["carpan_1sigma"] == pytest.approx(1.96, abs=0.05)
    assert t["en_iyi_gozlenen"] == "M_ejekta"
    assert t["beta_ya_gore_kazanc"] > 6.0
    assert t["genel"] == "Y0'I TANIMLAYAN GOZLEMLI VAR"


def test_t50_t90_GOZLENMIYOR_tanimlayici_secilemez():
    """`t50`/`t90` daha duyarlı ama DART için ölçülmüş karşılıkları **yok**."""
    t = _uretim_tablosu()
    r = {s["ad"]: s for s in t["satirlar"]}
    assert not r["t50"]["gozlenen"] and not r["t90"]["gozlenen"]
    # siralama en sikistirandan baslar: t90 en ustte ama SECILMEDI
    assert t["satirlar"][0]["ad"] == "t90"
    assert t["en_iyi_gozlenen"] == "M_ejekta"


def test_sekil_terimi_eklenince_M_ejekta_hala_beta_dan_iyi():
    """Üst sınır denemesi: `M_ejekta`'ya küre/elipsoit farkı (`%56`) de eklenirse."""
    sM = float(np.sqrt((0.3 / 1.6) ** 2 + 0.15 ** 2 + 0.56 ** 2))
    t = OD.duyarlilik_tablosu(OD.uretim_gozlemlileri(
        sigma_beta_toplam=0.447, beta_gozlem=3.12, sigma_M_bagil=sM))
    r = {s["ad"]: s for s in t["satirlar"]}
    assert r["M_ejekta"]["carpan_1sigma"] == pytest.approx(4.45, abs=0.1)
    assert r["M_ejekta"]["carpan_1sigma"] < r["beta"]["carpan_1sigma"] / 2.5
    # bu sertlikte esik asilir: tek basina "tanimlayici" sayilmaz
    assert t["genel"] == "Y0 GOZLEMLILERLE TANIMLANAMAZ"


def test_tablo_gecersiz_girdiler():
    with pytest.raises(ValueError):
        OD.Gozlemli("x", {1.0: 2.0, 10.0: 1.0}, 0.0, True)
    with pytest.raises(ValueError):
        OD.Gozlemli("x", {1.0: 2.0}, 0.1, True)
    with pytest.raises(ValueError):          # hic gozlenen yok
        OD.duyarlilik_tablosu([OD.Gozlemli("t50", OD.OLCULEN_Y0_SERILERI["t50"],
                                           0.2, False)])


# ------------------------------- ADR-0053 §2c: karar C1'den BAGIMSIZ
#: Gozlenen `β` icin butun adaylar (ADR-0053 §2c tablosu).
BETA_ADAYLARI = (3.748, 3.600, 3.320, 3.223, 3.125, 3.120, 3.019, 2.816)
ONERILEN = (1.0e0, 1.0e5)


def test_onerilen_onsel_BUTUN_beta_adaylarini_iceriyor():
    """Önsel kararı C1'e bağlı değil: sekiz adayın hepsi `[1e0, 1e5]` içinde."""
    uy = _uy()
    ys = [OD.y0_coz(uy, b) for b in BETA_ADAYLARI]
    assert all(ONERILEN[0] <= y <= ONERILEN[1] for y in ys), ys
    for b in BETA_ADAYLARI:
        d = OD.onsel_denetle(uy, beta_gozlem=b, sigma_toplam=0.447,
                             onsel_lo=ONERILEN[0], onsel_hi=ONERILEN[1])
        assert d["genel"] == "ONSEL GOZLEMI ICERIYOR", (b, d["Y0_gozlem"])
    # en yakin kenara en az bir dekad bosluk
    kenar = min(np.log10(min(ys) / ONERILEN[0]), np.log10(ONERILEN[1] / max(ys)))
    assert kenar > 1.0


def test_ESKI_onsel_yalniz_yeniden_sekillenme_dalinda_kurtuluyor():
    """Eski `[1e3, 1e7]`'yi ancak L16 düzeltmesi (en az yerleşmiş aday) kurtarıyor."""
    uy = _uy()
    icinde = {b for b in BETA_ADAYLARI if 1.0e3 <= OD.y0_coz(uy, b) <= 1.0e7}
    assert icinde == {3.019, 2.816}          # yalniz yeniden sekillenme adaylari
    # kilitli hedef (3,12) ve yayinlanan (3,6) ikisi de DISINDA
    for b in (3.120, 3.600):
        assert OD.onsel_denetle(uy, beta_gozlem=b, sigma_toplam=0.447,
                                onsel_lo=1.0e3, onsel_hi=1.0e7
                                )["genel"] == "ONSEL GOZLEMI ICERMIYOR"


def test_C1_in_Y0_uzerindeki_kaldiraci_bir_dekaddan_BUYUK():
    """`3,12` ile yayınlanan `3,6` arasındaki seçim `Y₀`'yı `1,17` dekad kaydırıyor."""
    uy = _uy()
    kayma = np.log10(OD.y0_coz(uy, 3.120) / OD.y0_coz(uy, 3.600))
    assert kayma == pytest.approx(1.17, abs=0.02)
    # yani C1 kozmetik degil: beta'daki %15 fark Y0'da 15 kat
    assert OD.y0_coz(uy, 3.120) / OD.y0_coz(uy, 3.600) > 10.0
