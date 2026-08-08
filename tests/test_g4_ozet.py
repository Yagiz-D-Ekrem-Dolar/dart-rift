"""Ölçüm çıktısı → G4 anahtarları çevirisi (FAZ 4.7).

Bu mantık `measure_longrun`'daki plato mantığıyla **aynı riski**
taşıyordu: bir betiğin içinde gömülü ve sınanamaz. Dışarı alındı.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.g4_gate import degerlendir
from dartrift.validation.g4_ozet import faz44_ozet, faz45_ozet


def _kol(N, beta, cap=2.6, durum="tamam"):
    return {"durum": durum, "N": N, "beta_son": beta,
            "mermi_parcacik_cap": cap, "tasarruf": 6.9}


def _ham(**kw):
    varsayilan = {
        "A2_r_ince_carpani": 8.0, "A3_kutle_sapmasi": 2.25e-05,
        "sonuclar": {
            "s7_lam2_Aprime": _kol(11164, 3.10),
            "s7_lam2_tek_h": _kol(11164, 2.60),
            "s5_lam2_Aprime": _kol(28000, 3.18),
            "s5_lam2_tek_h": _kol(28000, 2.70),
        },
    }
    varsayilan.update(kw)
    return varsayilan


def test_A1_EN_KOTU_kolu_aliyor() -> None:
    """Kapı en zayıf halkadan geçer — en iyi kol değil, en kötüsü."""
    h = _ham()
    h["sonuclar"]["s7_lam2_Aprime"]["mermi_parcacik_cap"] = 1.4
    assert faz44_ozet(h)["A1_mermi_parcacik_cap"] == pytest.approx(1.4)


def test_A2_A3_tepe_duzeyden_tasiniyor() -> None:
    o = faz44_ozet(_ham())
    assert o["A2_r_ince_carpani"] == pytest.approx(8.0)
    assert o["A3_kutle_sapmasi"] == pytest.approx(2.25e-05)


def test_B1_GORELI_fark_ve_EN_INCE_iki_kol() -> None:
    """`β` mertebesi kurulumla değişir; fark **göreli** olmalı."""
    o = faz44_ozet(_ham())
    assert o["B1_beta_farki"] == pytest.approx(abs(3.18 - 3.10) / 3.18)
    assert o["B1_kollar"] == ["s7_lam2_Aprime", "s5_lam2_Aprime"]


def test_B1_tek_kol_varsa_KOSULMAMIS() -> None:
    """Bir tek çözünürlükle yakınsama gösterilemez."""
    h = _ham(sonuclar={"s7_lam2_Aprime": _kol(11164, 3.10)})
    assert "B1_beta_farki" not in faz44_ozet(h)


def test_B3_Aprime_daha_yakinsa_1() -> None:
    """A′ (3,10) referansa (3,18) tek `h`'den (2,60) daha yakın → geçer."""
    assert faz44_ozet(_ham())["B3_Aprime_daha_yakin"] == 1.0


def test_B3_tersine_donebiliyor() -> None:
    """Pozitif kontrol: ölçüt gerçekten iki yönlü mü?"""
    h = _ham()
    h["sonuclar"]["s7_lam2_Aprime"]["beta_son"] = 2.00   # referanstan UZAK
    h["sonuclar"]["s7_lam2_tek_h"]["beta_son"] = 3.17    # referansa YAKIN
    assert faz44_ozet(h)["B3_Aprime_daha_yakin"] == 0.0


def test_PATLAYAN_kol_atlaniyor() -> None:
    """`durum != tamam` olan kol özete girmemeli."""
    h = _ham()
    h["sonuclar"]["s5_lam2_Aprime"] = {"durum": "patladi", "adim": 12}
    o = faz44_ozet(h)
    assert "B1_beta_farki" not in o          # geriye tek A' kolu kaldi
    assert o["A1_mermi_parcacik_cap"] == pytest.approx(2.6)


def test_NAN_beta_atlaniyor() -> None:
    h = _ham()
    h["sonuclar"]["s5_lam2_Aprime"]["beta_son"] = float("nan")
    assert "B1_beta_farki" not in faz44_ozet(h)


def test_bos_girdi_BOS_ozet() -> None:
    assert faz44_ozet({}) == {}
    assert faz44_ozet({"sonuclar": {}}) == {}


def test_faz45_ozet_bayragi_cevirıyor() -> None:
    assert faz45_ozet({"beta_bound_settled": True})["B2_durulmus"] == 1.0
    assert faz45_ozet({"beta_bound_settled": False})["B2_durulmus"] == 0.0
    assert "B2_durulmus" not in faz45_ozet({})


def test_faz45_egim_NAN_ise_yazilmiyor() -> None:
    assert "B4_enerji_egim" not in faz45_ozet(
        {"energy_drift_loglog_slope": float("nan")})
    assert faz45_ozet({"energy_drift_loglog_slope": 0.92})[
        "B4_enerji_egim"] == pytest.approx(0.92)


def test_UCTAN_UCA_ozet_kapiya_baglanıyor() -> None:
    """Özet → kapı: anahtarlar gerçekten eşleşiyor mu?

    İki modül ayrı yazıldı; adlar ayrışsaydı kapı her şeyi `koşulmadı`
    sanardı ve bu **sessizce** doğru görünürdü (kapı zaten geçmiyor).
    Bu test o sessiz ayrışmayı yakalar.
    """
    o44 = faz44_ozet(_ham())
    o45 = faz45_ozet({"beta_bound_settled": True,
                      "energy_drift_loglog_slope": 0.92})
    r = degerlendir(o44, o45, {"c1_kapsama": 1.0, "c2_en_dar": 0.142,
                               "c3_gecti": True, "kuru": False})
    assert r.kosulmayanlar == [], r.kosulmayanlar
    assert r.gecti is True


def test_UCTAN_UCA_A1_dususu_kapiya_ULASIYOR() -> None:
    """Özetteki bir düşüş kapıda gerçekten görünüyor mu?"""
    h = _ham()
    h["sonuclar"]["s7_lam2_Aprime"]["mermi_parcacik_cap"] = 1.2
    r = degerlendir(faz44_ozet(h),
                    faz45_ozet({"beta_bound_settled": True,
                                "energy_drift_loglog_slope": 0.92}),
                    {"c1_kapsama": 1.0, "c2_en_dar": 0.142,
                     "c3_gecti": True, "kuru": False})
    assert "A1" in r.dusenler
    assert r.gecti is False


def test_B3_SOZLUK_SIRASINDAN_bagimsiz() -> None:
    """B3 **en kaba** kurulumu seçmeli, sözlük sırasındaki ilkini değil.

    Bulunan kusur: kod `eslesen[0]` alıyordu. Python 3.7+'da sözlük
    sırası ekleme sırasıdır ve koşucu kolları kaba→ince eklediği için
    **şu an** doğru sonuç çıkıyordu — ama koşucunun döngü sırası
    değiştiği anda sessizce yanlış kola bakardı.

    Bu test sırayı **tersine çevirip** aynı yanıtı bekliyor.
    """
    duz = _ham()
    ters = _ham(sonuclar={k: duz["sonuclar"][k]
                          for k in reversed(list(duz["sonuclar"]))})
    a, b = faz44_ozet(duz), faz44_ozet(ters)
    assert a["B3_Aprime_daha_yakin"] == b["B3_Aprime_daha_yakin"]
    assert a["B3_ayrinti"]["kurulum"] == b["B3_ayrinti"]["kurulum"] == "s7_lam2"


def test_B3_EN_KABA_kurulumu_seciyor() -> None:
    """Doğrudan: seçilen kurulum en küçük `N`'li olan mı?"""
    o = faz44_ozet(_ham())
    assert o["B3_ayrinti"]["kurulum"] == "s7_lam2"      # N=11164 < 28000
    assert o["B3_ayrinti"]["referans_beta"] == pytest.approx(3.18)


def test_ciktilar_JSON_serilestirilebilir() -> None:
    """12 saatlik bir koşunun **sonunda** JSON patlarsa her şey kaybolur.

    `json.dumps` numpy tiplerini kabul etmez (`np.float64` kabul eder ama
    `np.bool_` ve `np.int64` **etmez**). Bütün özet çıktıları burada
    yuvarlanıyor.
    """
    import json

    o44 = faz44_ozet(_ham())
    o45 = faz45_ozet({"beta_bound_settled": True,
                      "energy_drift_loglog_slope": 0.92})
    for ad, o in (("faz44", o44), ("faz45", o45)):
        json.dumps(o), ad
    # Ve B3_ayrinti gercekten DOLU olmali -- bos bir sozluk sinamaz.
    assert o44["B3_ayrinti"], "B3_ayrinti bos, test bos bir dogruyu siniyor"
    json.dumps(o44["B3_ayrinti"])


def test_durulma_tanisi_JSON_serilestirilebilir() -> None:
    from dartrift.validation.settling_time import settling_time
    import json

    t = np.linspace(0.0, 1.0, 60)
    for b in (0.5 + 1e-5 * np.sin(30.0 * t), 0.5 + 0.4 * t):
        json.dumps(settling_time(t, b, adim=np.arange(60)))


def test_kapi_raporu_JSON_ve_markdown_uretiyor() -> None:
    import json

    r = degerlendir(faz44_ozet(_ham()),
                    faz45_ozet({"beta_bound_settled": True,
                                "energy_drift_loglog_slope": 0.92}),
                    {"c1_kapsama": 1.0, "c2_en_dar": 0.21,
                     "c3_gecti": True, "kuru": False})
    m = r.markdown()
    assert "G4 kapı raporu" in m and len(m) > 500
    json.dumps({"gecti": r.gecti, "dusen": r.dusenler,
                "kosulmayan": r.kosulmayanlar})
