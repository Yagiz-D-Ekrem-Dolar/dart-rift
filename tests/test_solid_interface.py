"""ADR-0041 §5 boşluk 3 ölçümü — IC ve yargı mantığı (GPU gerekmez)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.solid_interface import (BASALT_SOLID, CEPHE_ESIKLERI,
                                                 KUTU, RHO0, _malzeme,
                                                 build_two_zone_solid_ic,
                                                 cephe_yaricapi, judge)


def _uc_kol(n=16, lam=2, r_ic=0.15, per_particle_h=True):
    h = 2.0 / n
    return (build_two_zone_solid_ic(n, 1, r_ic, h),
            build_two_zone_solid_ic(n, lam, r_ic, h,
                                    per_particle_h=per_particle_h),
            build_two_zone_solid_ic(n * lam, 1, r_ic, h / lam))


def test_enerji_uc_kolda_AYNI() -> None:
    """Farklı enerji = farklı problem. `1e-3` değil, `1e-12` isteniyor."""
    e = [k["energy_injected"] for k in _uc_kol()]
    assert (max(e) - min(e)) / max(e) < 1e-12, e


def test_kutle_sapmasi_KUCUK_ama_SIFIR_DEGIL() -> None:
    """Küre sınırı iki kafesle mükemmel döşenmez — susulmaz, ölçülür."""
    m = [k["total_mass"] for k in _uc_kol()]
    sapma = (max(m) - min(m)) / max(m)
    assert 0.0 < sapma < 0.005, sapma


def test_lam1_TEK_populasyon() -> None:
    """Boşluk kontrolü: `lam=1` iki bölgeli değildir, `h` tekdüzedir."""
    k = build_two_zone_solid_ic(16, 1, 0.15, 0.125)
    assert k["h_min"] == k["h_max"] == 0.125
    assert len(k["m"]) == 16 ** 3
    assert np.all(k["m"] == k["m"][0])


def test_A_prime_ince_bolgeye_KUCUK_h_veriyor() -> None:
    """A′'nın tanımı: ince bölge `h/λ` alır."""
    k = build_two_zone_solid_ic(16, 2, 0.15, 0.125, per_particle_h=True)
    assert k["h_min"] == pytest.approx(0.0625)
    assert k["h_max"] == pytest.approx(0.125)
    assert k["per_particle_h"] is True


def test_kontrol_kolu_TEK_h_kullaniyor() -> None:
    """`per_particle_h=False` A′'yı kapatır — katkıyı yalıtan kontrol kolu."""
    k = build_two_zone_solid_ic(16, 2, 0.15, 0.125, per_particle_h=False)
    assert k["h_min"] == k["h_max"] == pytest.approx(0.125)
    # Ama kutle DAGILIMI hala iki bolgeli -- yalnizca h degisti.
    assert len(np.unique(k["m"])) == 2


def test_kutle_yerel_hucre_hacminden() -> None:
    """ADR-0030'un değişmezi: `m = ρ₀·dx³`, bölgeye göre."""
    k = build_two_zone_solid_ic(16, 2, 0.15, 0.125)
    kutleler = np.unique(k["m"])
    assert kutleler[1] / kutleler[0] == pytest.approx(8.0, rel=1e-12)
    assert kutleler[1] == pytest.approx(RHO0 * (KUTU / 16) ** 3, rel=1e-12)


def test_gecersiz_girdiler_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError):
        build_two_zone_solid_ic(16, 0, 0.15, 0.125)
    with pytest.raises(ValueError):
        build_two_zone_solid_ic(16, 2, 0.6, 0.125)
    with pytest.raises(ValueError):
        build_two_zone_solid_ic(16, 2, 0.001, 0.125)   # ince bölge boş


def test_cephe_hicbiri_HAREKET_ETMIYORSA_patliyor() -> None:
    """Sessizce `0.0` dönmek, "cephe yok"u "cephe merkezde" diye raporlardı."""
    x = np.array([[0.1, 0.0, 0.0], [0.2, 0.0, 0.0]])
    with pytest.raises(RuntimeError):
        cephe_yaricapi(x, np.zeros_like(x), 0.02)


def test_cephe_EN_DIS_hareketliyi_buluyor() -> None:
    x = np.array([[0.1, 0.0, 0.0], [0.3, 0.0, 0.0], [0.4, 0.0, 0.0]])
    v = np.array([[100.0, 0, 0], [10.0, 0, 0], [0.1, 0, 0]])
    # max|v| = 100; kesir 0.02 -> esik 2.0 -> ilk ikisi gecer, ucuncusu hayir
    assert cephe_yaricapi(x, v, 0.02) == pytest.approx(0.3)
    # kesir 0.0005 -> esik 0.05 -> ucu de gecer
    assert cephe_yaricapi(x, v, 0.0005) == pytest.approx(0.4)


def test_cephe_gecersiz_kesir_REDDEDILIYOR() -> None:
    x = np.array([[0.1, 0.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0]])
    for k in (0.0, 1.0, -0.1, 2.0):
        with pytest.raises(ValueError):
            cephe_yaricapi(x, v, k)


def test_cephe_YIGIN_yogunlugu_tuzagi_KAYITLI() -> None:
    """Gözeneklilik açıkken `ρ` başlangıçta `ρ₀/α₀`'dır, `ρ₀` değil.

    Bu tuzak gerçekten ölçüldü: `2700/1,5 = 1800`. Yoğunluk eşiği
    (`1,05·ρ₀ = 2835`) başlangıcın **%58 üstündeydi** ve hiç tetiklenmedi.
    Belge kodda kalsın diye burada sabitleniyor.
    """
    assert RHO0 / 1.5 == pytest.approx(1800.0)
    assert len(CEPHE_ESIKLERI) >= 3, "tek esige bagli kalinmamali"


def _kol(r, m=1.0, e=1.0):
    return {"r_measured": r, "total_mass": m, "energy_injected": e,
            "N": 1, "h_min": 1.0, "h_max": 1.0, "n_injected": 1,
            "rho_max": 1.0, "n_steps": 1}


def test_yargi_parantez_ICINDE_zararsiz() -> None:
    y = judge(_kol(0.20), _kol(0.25), _kol(0.30), 2, 0.15, 1.0)
    assert y["yargi"] == "arayuz_zararsiz"
    assert y["tasma_rel"] == 0.0


def test_yargi_parantez_DISINDA_bedelli() -> None:
    y = judge(_kol(0.20), _kol(0.40), _kol(0.30), 2, 0.15, 1.0)
    assert y["yargi"] == "arayuz_bedelli"
    assert y["tasma_rel"] > 0.0


def test_yargi_kollar_ayirt_EDILEMEZSE_belirsiz() -> None:
    """Parantez sıfır genişlikteyse ölçüt boştur."""
    y = judge(_kol(0.30), _kol(0.30), _kol(0.3001), 2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"
    assert y["kollar_ayirt_edilebilir"] is False


def test_yargi_enerji_FARKLIYSA_belirsiz() -> None:
    y = judge(_kol(0.20, e=1.0), _kol(0.25, e=1.1), _kol(0.30, e=1.0),
              2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"
    assert y["enerji_esit"] is False


def test_yargi_kutle_BUYUKSE_belirsiz() -> None:
    y = judge(_kol(0.20, m=1.0), _kol(0.25, m=2.0), _kol(0.30, m=1.0),
              2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"
    assert y["kutle_ihmal_edilebilir"] is False


def test_malzeme_bayraklari_GERCEKTEN_geciyor() -> None:
    """Ayrıştırma kolları gerçekten farklı malzeme kuruyor mu?"""
    assert BASALT_SOLID.strength.enabled
    assert BASALT_SOLID.porosity.enabled
    assert BASALT_SOLID.damage.enabled
    m = _malzeme(True, False, False)
    assert m.strength.enabled and not m.porosity.enabled and not m.damage.enabled


def _kol_esikli(r_dict, m=1.0, e=1.0):
    k = _kol(r_dict["0.02"], m, e)
    k["r_esikler"] = r_dict
    return k


def test_yargi_ESIGE_BAGIMLI_dali_calisiyor() -> None:
    """Yargı eşikten eşiğe değişiyorsa bu bir ölçüm değil, bir **tercihtir**.

    Sonuç `esige_bagimli` dönmeli — sessizce eşiklerden birini seçip
    "zararsız" demek, ölçümü tercihle değiştirmek olurdu.
    """
    a = _kol_esikli({"0.01": 0.20, "0.02": 0.20, "0.05": 0.20})
    c = _kol_esikli({"0.01": 0.30, "0.02": 0.30, "0.05": 0.30})
    # 0.01'de parantez ICINDE, 0.05'te DISINDA -> celiskili
    b = _kol_esikli({"0.01": 0.25, "0.02": 0.25, "0.05": 0.50})
    y = judge(a, b, c, 2, 0.15, 1.0)
    assert y["yargi"] == "esige_bagimli", y["esik_yargilari"]
    assert set(y["esik_yargilari"].values()) == {True, False}


def test_yargi_UC_ESIKTE_de_ayni_ise_yargi_DURUYOR() -> None:
    a = _kol_esikli({"0.01": 0.20, "0.02": 0.20, "0.05": 0.20})
    b = _kol_esikli({"0.01": 0.25, "0.02": 0.25, "0.05": 0.25})
    c = _kol_esikli({"0.01": 0.30, "0.02": 0.30, "0.05": 0.30})
    y = judge(a, b, c, 2, 0.15, 1.0)
    assert y["yargi"] == "arayuz_zararsiz"
    assert set(y["esik_yargilari"].values()) == {True}


def test_esik_bagimliligi_ON_KOSUL_dusunce_ARANMIYOR() -> None:
    """Ön koşul düştüyse yargı zaten `belirsiz` — eşik tartışması anlamsız."""
    a = _kol_esikli({"0.01": 0.30, "0.02": 0.30, "0.05": 0.30})
    b = _kol_esikli({"0.01": 0.25, "0.02": 0.25, "0.05": 0.90})
    c = _kol_esikli({"0.01": 0.3001, "0.02": 0.3001, "0.05": 0.3001})
    y = judge(a, b, c, 2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"


def test_enjeksiyon_bolgesi_MUTLAK_verilince_uc_kolda_AYNI() -> None:
    """Aynı enerji **aynı bölgeye** girmeli — ince kolu patlatan hata.

    İlk sürümde `h_inject = 3·dx_k` idi; ince kolun `dx`'i yarı olduğu için
    aynı enerji `8` kat küçük hacme giriyordu (özgül `1,33e5 → 1,06e6 J/kg`)
    ve koşu patladı (`262144/262144` parçacıkta `rho` sonlu değil).
    """
    h_inj = 3.0 / 16
    a = build_two_zone_solid_ic(16, 1, 0.15, 0.125, h_inject=h_inj)
    b = build_two_zone_solid_ic(16, 2, 0.15, 0.125, h_inject=h_inj)
    c = build_two_zone_solid_ic(32, 1, 0.15, 0.0625, h_inject=h_inj)
    km = [k["injected_mass"] for k in (a, b, c)]
    assert (max(km) - min(km)) / max(km) < 0.05, km
    assert a["h_inject"] == b["h_inject"] == c["h_inject"] == h_inj


def test_enjeksiyon_bolgesi_dx_e_baglanirsa_AYRISIYOR() -> None:
    """Eski davranışın gerçekten hatalı olduğunu **gösteren** test.

    Bir düzeltmenin gerekli olduğunu iddia etmek yetmez; düzeltilen şeyin
    gerçekten bozuk olduğu ölçülür.
    """
    a = build_two_zone_solid_ic(16, 1, 0.15, 0.125)      # h_inject yok -> 3*dx
    c = build_two_zone_solid_ic(32, 1, 0.15, 0.0625)
    assert c["h_inject"] == pytest.approx(a["h_inject"] / 2)
    oran = a["injected_mass"] / c["injected_mass"]
    assert oran > 4.0, f"ayrisma beklenenden kucuk: {oran}"


def test_yargi_enjeksiyon_BOLGESI_farkliysa_belirsiz() -> None:
    """`enerji_esit` bu hatayı yakalayamaz — ayrı bir ön koşul gerekiyordu."""
    def _k(r, km):
        d = _kol(r)
        d["injected_mass"] = km
        return d
    y = judge(_k(0.20, 75.0), _k(0.25, 9.4), _k(0.30, 75.0), 2, 0.15, 1.0)
    assert y["enerji_esit"] is True          # enerji AYNI
    assert y["enjeksiyon_bolgesi_ayni"] is False
    assert y["yargi"] == "belirsiz"


def test_yargi_eski_kayitlarla_GERIYE_UYUMLU() -> None:
    """`injected_mass` yoksa ön koşul atlanır, `nan` raporlanır."""
    y = judge(_kol(0.20), _kol(0.25), _kol(0.30), 2, 0.15, 1.0)
    assert y["enjeksiyon_bolgesi_ayni"] is True
    assert np.isnan(y["enjeksiyon_kutle_sapmasi"])
    assert y["yargi"] == "arayuz_zararsiz"


def test_cephe_DOYGUNLUK_korumasi() -> None:
    """Cephe kutu kenarına vardıysa bu bir cephe **değil**, doygunluktur.

    Job 1460697'de gözenekli kaba kol `r = 0,838970` verdi — kutu köşe
    mesafesi (`√3/2 = 0,866`). Sessizce geçtiği için parantez `%278,95`
    genişledi ve iki bölgeli kol "içine" düştü: yargı **`arayuz_zararsiz`**
    çıktı. Bu doğru değil; ölçüm geçersizdi.
    """
    x = np.array([[0.83, 0.0, 0.0], [0.1, 0.0, 0.0]])
    v = np.array([[10.0, 0, 0], [10.0, 0, 0]])
    with pytest.raises(RuntimeError, match="DOYGUN"):
        cephe_yaricapi(x, v, 0.01, v_ref=100.0)


def test_cephe_v_ref_KOLA_BAGLI_DEGIL() -> None:
    """`v_ref` verilince eşik `max|v|`'den bağımsızdır — kollar eşitlenir.

    İki "kol": aynı hız alanı, ama birinde tek bir parçacık çok hızlı.
    `max|v|` tabanıyla eşikler farklı çıkar; `v_ref` ile aynı.
    """
    x = np.array([[0.1, 0, 0], [0.2, 0, 0], [0.3, 0, 0]])
    yavas = np.array([[50.0, 0, 0], [20.0, 0, 0], [1.0, 0, 0]])
    hizli = np.array([[500.0, 0, 0], [20.0, 0, 0], [1.0, 0, 0]])
    # max|v| tabani: esikler 0.5 ve 5.0 -> FARKLI sonuc
    assert cephe_yaricapi(x, yavas, 0.01) == pytest.approx(0.3)
    assert cephe_yaricapi(x, hizli, 0.01) == pytest.approx(0.2)
    # v_ref tabani: esik ikisinde de 5.0 -> AYNI sonuc
    assert (cephe_yaricapi(x, yavas, 0.01, v_ref=500.0)
            == cephe_yaricapi(x, hizli, 0.01, v_ref=500.0) == pytest.approx(0.2))


def test_cephe_esik_gecilemezse_PATLIYOR() -> None:
    """Hiçbir parçacık eşiği geçmiyorsa `0.0` dönmek yanlış olurdu."""
    x = np.array([[0.1, 0.0, 0.0]])
    v = np.array([[0.001, 0.0, 0.0]])
    with pytest.raises(RuntimeError, match="cephe yok"):
        cephe_yaricapi(x, v, 0.5, v_ref=500.0)


def test_esik_ayrinti_AYIRT_ETME_GUCUNU_raporluyor() -> None:
    """Parantez, ölçülen taşmadan geniş değilse ölçütün orada **gücü yoktur**.

    Gerçek ölçümde (job 1460698, `mukavemet`) `0,05` eşiğinde parantez
    `%2,31`, taşma ise `%2,17` — yani ölçüt kendi çözünürlüğü kadar bir
    farkı "dışarıda" ilan ediyor. Yargı **ayarlanmıyor**; gücü yanına
    yazılıyor ki yorumlanabilsin.
    """
    def _k(rd):
        d = _kol(rd["0.02"])
        d["r_esikler"] = rd
        return d
    a = _k({"0.01": 0.280, "0.02": 0.255, "0.05": 0.21396})
    b = _k({"0.01": 0.273, "0.02": 0.247, "0.05": 0.20931})
    c = _k({"0.01": 0.262, "0.02": 0.244, "0.05": 0.21825})
    y = judge(a, b, c, 2, 0.15, 1.0)
    d5 = y["esik_ayrinti"]["0.05"]
    assert d5["parantez_genisligi_rel"] == pytest.approx(0.0200, abs=1e-3)
    assert d5["tasma_rel"] == pytest.approx(0.0217, abs=1e-3)
    # Tasma parantezle AYNI mertebede -> olcut orada ayirt edemiyor
    assert 0.5 < d5["tasma_parantez_orani"] < 2.0
    # Ve siralama TERS donmus: dusuk esikte kaba > ince, yuksekte degil
    assert y["esik_ayrinti"]["0.01"]["kaba_incenin_ustunde"] is True
    assert d5["kaba_incenin_ustunde"] is False


def test_iletilen_momentum_DISARI_bileseni_sayiyor() -> None:
    """İçeri dönen hız net toplamı **yapay olarak küçültürdü**."""
    from dartrift.validation.solid_interface import iletilen_radyal_momentum

    x = np.array([[0.4, 0, 0], [-0.4, 0, 0]])
    m = np.array([1.0, 1.0])
    disari = np.array([[10.0, 0, 0], [-10.0, 0, 0]])       # ikisi de disari
    karisik = np.array([[10.0, 0, 0], [10.0, 0, 0]])       # biri iceri
    assert iletilen_radyal_momentum(x, disari, m, 0.3) == pytest.approx(20.0)
    assert iletilen_radyal_momentum(x, karisik, m, 0.3) == pytest.approx(10.0)


def test_iletilen_momentum_SONDA_DISINI_aliyor() -> None:
    from dartrift.validation.solid_interface import iletilen_radyal_momentum

    x = np.array([[0.1, 0, 0], [0.4, 0, 0]])
    v = np.array([[10.0, 0, 0], [10.0, 0, 0]])
    m = np.array([1.0, 1.0])
    assert iletilen_radyal_momentum(x, v, m, 0.3) == pytest.approx(10.0)
    with pytest.raises(RuntimeError):
        iletilen_radyal_momentum(x, v, m, 0.9)


def test_iletilen_momentum_DOYGUNLASMIYOR() -> None:
    """Cephe yarıçapının aksine bir tavanı yok — ölçütün varlık nedeni.

    Bozulma kutuyu doldursa bile momentum **büyümeye devam eder**;
    cephe yarıçapı ise köşe mesafesinde takılır.
    """
    from dartrift.validation.solid_interface import iletilen_radyal_momentum

    x = np.array([[0.4, 0, 0], [0.45, 0, 0]])
    m = np.array([1.0, 1.0])
    zayif = iletilen_radyal_momentum(x, np.full((2, 3), 0.0) + [1.0, 0, 0], m, 0.3)
    guclu = iletilen_radyal_momentum(x, np.full((2, 3), 0.0) + [50.0, 0, 0], m, 0.3)
    assert guclu == pytest.approx(50.0 * zayif)


def _kol_p(p, m=1.0, e=1.0, km=75.0):
    return {"p_iletilen": p, "total_mass": m, "energy_injected": e,
            "injected_mass": km}


def test_momentum_yargisi_parantez_ICINDE() -> None:
    from dartrift.validation.solid_interface import judge_momentum

    y = judge_momentum(_kol_p(100.0), _kol_p(110.0), _kol_p(120.0),
                       2, 0.15, 1.0)
    assert y["yargi"] == "arayuz_zararsiz"
    assert y["tasma_rel"] == 0.0


def test_momentum_yargisi_parantez_DISINDA() -> None:
    from dartrift.validation.solid_interface import judge_momentum

    y = judge_momentum(_kol_p(100.0), _kol_p(200.0), _kol_p(120.0),
                       2, 0.15, 1.0)
    assert y["yargi"] == "arayuz_bedelli"
    assert y["tasma_rel"] > 0.5


def test_momentum_yargisi_ON_KOSULLARI_koruyor() -> None:
    from dartrift.validation.solid_interface import judge_momentum

    # enjeksiyon bolgesi farkli -> belirsiz
    y = judge_momentum(_kol_p(100.0, km=75.0), _kol_p(110.0, km=9.0),
                       _kol_p(120.0, km=75.0), 2, 0.15, 1.0)
    assert y["yargi"] == "belirsiz"
    # kollar ayirt edilemiyor -> belirsiz
    y2 = judge_momentum(_kol_p(100.0), _kol_p(100.0), _kol_p(100.05),
                        2, 0.15, 1.0)
    assert y2["yargi"] == "belirsiz"
