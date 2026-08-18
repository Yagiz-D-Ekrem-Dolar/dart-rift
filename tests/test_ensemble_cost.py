"""FAZ 5 ensemble maliyeti — A′'dan sonra yeniden hesap (FAZ 4 → 5 geçişi)."""
from __future__ import annotations

import pytest

from dartrift.validation.ensemble_cost import (
    OLCULEN,
    adim_maliyeti_s,
    ensemble_gpu_gunu,
    fizibilite_sinirlari,
    kosu_maliyeti_s,
)


def test_adim_maliyeti_OLCULEN_noktada_tutuyor() -> None:
    """Boşluk kontrolü: ölçümün yapıldığı `N`'de ölçülen süreyi vermeli.

    FIZIBILITE §2b: `N = 65 840` → `570 ms`.
    """
    beklenen = 0.570
    assert adim_maliyeti_s(OLCULEN["olcum_N"]) == pytest.approx(beklenen,
                                                               rel=0.02)


def test_adim_maliyeti_PARCACIKLA_dogrusal() -> None:
    assert adim_maliyeti_s(20000) == pytest.approx(2.0 * adim_maliyeti_s(10000))


def test_kosu_maliyeti_ADIM_SAYISIYLA_dogrusal() -> None:
    a = kosu_maliyeti_s(1.0, 10000, 1e-4)
    b = kosu_maliyeti_s(2.0, 10000, 1e-4)
    assert b == pytest.approx(2.0 * a, rel=1e-9)


def test_dt_KUCULURSE_maliyet_ARTIYOR() -> None:
    """A′'nın `dt` cezası hesaba **girmeli** — atlanırsa A′ ucuz görünür."""
    buyuk = kosu_maliyeti_s(1.0, 10000, 1e-4)
    kucuk = kosu_maliyeti_s(1.0, 10000, 5e-5)
    assert kucuk == pytest.approx(2.0 * buyuk, rel=1e-9)


def test_A_prime_TEKDUZE_INCEDEN_ucuz() -> None:
    """A′'nın varlık nedeni; oran `6,87×` (parçacık tasarrufu) olmalı."""
    d = ensemble_gpu_gunu(1.0, 300)
    assert d["A-prime"] < d["tekduze-ince"]
    beklenen = OLCULEN["N_tumu_ince"] / OLCULEN["N_aprime"]
    assert d["_kazanc_tumu_inceye_gore"] == pytest.approx(beklenen, rel=1e-6)


def test_A_prime_TEKDUZE_KABADAN_pahali_ve_NEDENI_dt() -> None:
    """A′ kaba sahneden **pahalı** — ve bu gizlenmemeli.

    Neden: parçacık sayısı biraz artıyor **ve** `dt` yarıya iniyor.
    Kaba sahne yine de kullanılamaz (mermi çözülmemiş, ADR-0026), ama
    A′'nın kabaya göre bedeli **açıkça** görünmeli.
    """
    d = ensemble_gpu_gunu(1.0, 300)
    assert d["A-prime"] > d["tekduze-kaba"]
    # Bedelin buyuk kismi dt'den: N orani kucuk, dt orani 2.
    n_orani = OLCULEN["N_aprime"] / OLCULEN["N_tumu_kaba"]
    assert d["A-prime"] / d["tekduze-kaba"] == pytest.approx(
        n_orani * OLCULEN["lam"], rel=1e-6)


def test_ensemble_KOSU_SAYISIYLA_dogrusal() -> None:
    a = ensemble_gpu_gunu(1.0, 100)["A-prime"]
    b = ensemble_gpu_gunu(1.0, 300)["A-prime"]
    assert b == pytest.approx(3.0 * a, rel=1e-9)


def test_fizibilite_siniri_ENSEMBLE_ile_TUTARLI() -> None:
    """İki fonksiyon aynı modeli kullanıyor; ayrışırlarsa biri yanlış."""
    butce = 30.0
    sinir = fizibilite_sinirlari(butce, 300)
    for ad in ("tekduze-kaba", "A-prime", "tekduze-ince"):
        geri = ensemble_gpu_gunu(sinir[ad], 300)[ad]
        assert geri == pytest.approx(butce, rel=1e-3), ad


def test_A_prime_30_GUNLUK_butceye_SIGIYOR_ince_SIGMIYOR() -> None:
    """Kararın kendisi: A′ ensemble'ı fizibil kılan şey mi?

    FIZIBILITE `~30 GPU-günü`nü fizibil sayıyordu. `1 s` simüle için:
    A′ `9,73` gün, tekdüze ince `66,85` gün.
    """
    d = ensemble_gpu_gunu(1.0, 300)
    assert d["A-prime"] < 30.0 < d["tekduze-ince"]


def test_gecersiz_girdiler_REDDEDILIYOR() -> None:
    for f, arg in ((adim_maliyeti_s, 0), (adim_maliyeti_s, -5)):
        with pytest.raises(ValueError):
            f(arg)
    with pytest.raises(ValueError):
        kosu_maliyeti_s(0.0, 100, 1e-4)
    with pytest.raises(ValueError):
        kosu_maliyeti_s(1.0, 100, 0.0)
    with pytest.raises(ValueError):
        ensemble_gpu_gunu(1.0, 0)
    with pytest.raises(ValueError):
        fizibilite_sinirlari(0.0)


def test_FIZIBILITE_ile_dogrudan_kiyas_UYARISI_var() -> None:
    """İki mutlak sayı aynı şeyi ölçmüyor; modül bunu **söylemeli**."""
    from pathlib import Path

    m = (Path(__file__).resolve().parents[1] / "src" / "dartrift" /
         "validation" / "ensemble_cost.py").read_text(encoding="utf-8")
    assert "doğrudan kıyaslanamaz" in m
    assert "2 000 000" in m and "11 000" in m
    assert "ORAN" in m


def test_mermiyi_cozmek_icin_GEREKEN_lam() -> None:
    """`A1 = D/s_ince` ve `s_ince = s_kaba/λ` ⇒ `λ = A1·s_kaba/D`."""
    from dartrift.validation.ensemble_cost import MERMI_CAPI_M, mermiyi_cozmek_icin_lam

    lam = mermiyi_cozmek_icin_lam(2.0, 7.0)
    assert lam == pytest.approx(2.0 * 7.0 / MERMI_CAPI_M)
    assert 18.0 < lam < 19.0, lam
    # Bosluk 3 lam=2'de kapandi; gereken lam ONDAN cok buyuk.
    assert lam > 9.0 * 2.0


def test_geometrik_sabit_OLCULEN_degeri_veriyor() -> None:
    """`c` uydurulmadı: `λ=2, r_iç=25` ölçümünden türetildi (`n_ince = 933`)."""
    from dartrift.validation.ensemble_cost import INCE_GEOMETRI_C, cozunurluk_bedeli

    assert INCE_GEOMETRI_C * (25.0 / 3.5) ** 3 == pytest.approx(933.0)
    d = cozunurluk_bedeli(2.0, 25.0)
    assert d["n_ince"] == pytest.approx(933, abs=1)
    assert d["N"] == pytest.approx(11164, abs=2)


def test_A1_lam_ile_DOGRU_hesaplaniyor() -> None:
    """Ölçülen: `λ=2` → `A1 = 0,215` (`COZULMEMIS`)."""
    from dartrift.validation.ensemble_cost import cozunurluk_bedeli

    assert cozunurluk_bedeli(2.0, 25.0)["A1"] == pytest.approx(0.2146, abs=1e-3)
    assert cozunurluk_bedeli(18.6, 3.0)["A1"] == pytest.approx(2.0, rel=1e-2)


def test_r_ince_kucultmek_PARCACIK_yukunu_KALDIRIYOR() -> None:
    """`n_ince ∝ r_iç³` — küçük bölge parçacık bedelini yok ediyor."""
    from dartrift.validation.ensemble_cost import cozunurluk_bedeli

    buyuk = cozunurluk_bedeli(18.6, 25.0)
    kucuk = cozunurluk_bedeli(18.6, 3.0)
    assert buyuk["ensemble_gpu_gunu"] / kucuk["ensemble_gpu_gunu"] > 50.0
    assert kucuk["parcacik_carpani"] < 1.2, kucuk["parcacik_carpani"]


def test_KALAN_bedel_TAMAMEN_dt_cezasi() -> None:
    """Küçük bölgede toplam çarpan ≈ `dt` çarpanı. **Bulgunun özü.**

    Tek global adımlı bir şemada bu **küçültülemez**; çözüm bireysel /
    blok zaman adımı (bu kod tabanında **yok**).
    """
    from dartrift.validation.ensemble_cost import cozunurluk_bedeli

    d = cozunurluk_bedeli(18.6, 3.0)
    assert d["toplam_carpan_lam2ye_gore"] == pytest.approx(
        d["parcacik_carpani"] * d["dt_carpani"], rel=1e-6)
    # dt cezasi baskin: toplam carpanin en az %85'i
    assert d["dt_carpani"] / d["toplam_carpan_lam2ye_gore"] > 0.85


def test_cozulmus_mermi_30_GUNLUK_butceye_SIGMIYOR() -> None:
    """Bulgunun kararı: A′ mevcut hâliyle ikisini birlikte veremiyor.

    `λ=2`: bütçeye sığar ama mermi **çözülmemiş** (`A1 = 0,21`).
    `λ=19`: mermi çözülür ama bütçe **3 kat** aşılır.
    """
    from dartrift.validation.ensemble_cost import cozunurluk_bedeli, mermiyi_cozmek_icin_lam

    ucuz = cozunurluk_bedeli(2.0, 25.0)
    # `lam` PRATIKTE tam sayi secilir ve gerekenin USTUNE yuvarlanir.
    #
    # Kayan nokta notu: `mermiyi_cozmek_icin_lam()` tam degeri (18,6418)
    # geri konulunca `A1 = 1.9999999999999998` cikiyor -- gidis-donusun
    # son biti. Kusur degil, ama esigin TAM ustunde bir olcum kayan
    # noktayla ters yone dusebilir. Pratikte lam = 19 secilir.
    cozulmus = cozunurluk_bedeli(19.0, 3.0)
    assert mermiyi_cozmek_icin_lam() < 19.0
    assert ucuz["ensemble_gpu_gunu"] < 30.0 and ucuz["A1"] < 2.0
    assert cozulmus["A1"] >= 2.0 and cozulmus["ensemble_gpu_gunu"] > 3.0 * 30.0


def test_cozunurluk_bedeli_gecersiz_girdi() -> None:
    from dartrift.validation.ensemble_cost import cozunurluk_bedeli, mermiyi_cozmek_icin_lam

    for lam, r in ((0.0, 3.0), (-1.0, 3.0), (2.0, 0.0), (2.0, -1.0)):
        with pytest.raises(ValueError):
            cozunurluk_bedeli(lam, r)
    with pytest.raises(ValueError):
        mermiyi_cozmek_icin_lam(0.0)


def test_IKI_ASAMALI_secenek_bedeli_ihmal_edilebilir() -> None:
    """ADR-0043'ün çekirdeği: mermiyi çözmek `%1`'e mal oluyor, `10×`'a değil.

    Bağlanma fazı `~1,2e-4 s` (mermi kendi çapını geçme süresi), ensemble
    ise `~1 s` — dört mertebe fark. Pahalı çözünürlük **sürekli**
    taşınmak zorunda değil.
    """
    from dartrift.validation.ensemble_cost import cozunurluk_bedeli

    tek_ucuz = cozunurluk_bedeli(2.0, 25.0, t_simule_s=1.0)["ensemble_gpu_gunu"]
    tek_pahali = cozunurluk_bedeli(19.0, 3.0, t_simule_s=1.0)["ensemble_gpu_gunu"]
    asama1 = cozunurluk_bedeli(19.0, 3.0, t_simule_s=1e-3)["ensemble_gpu_gunu"]
    iki_asama = asama1 + tek_ucuz

    # Tek asama pahali secenek butcenin 3 katindan fazla.
    assert tek_pahali > 3.0 * 30.0
    # Iki asama ucuz secenekten %2'den az pahali.
    assert iki_asama / tek_ucuz < 1.02, iki_asama / tek_ucuz
    # Ve butceye SIGIYOR.
    assert iki_asama < 30.0


def test_baglanma_suresi_kosu_suresinden_COK_kisa() -> None:
    """`t₁ / t_kosu ~ 1e-4` — iki aşamayı mümkün kılan oran."""
    from dartrift.validation.ensemble_cost import MERMI_CAPI_M

    v_carpma = 6144.9          # SAHNE varsayilani
    t_gecis = MERMI_CAPI_M / v_carpma
    assert t_gecis == pytest.approx(1.222e-4, rel=1e-2)
    assert t_gecis / 1.0 < 1e-3


def test_t1_duyarliligi_MONOTON_ve_kucuk() -> None:
    """`t₁` on kat büyürse toplam bedel yine `%10`'un altında artar."""
    from dartrift.validation.ensemble_cost import cozunurluk_bedeli

    taban = cozunurluk_bedeli(2.0, 25.0, t_simule_s=1.0)["ensemble_gpu_gunu"]
    oranlar = []
    for t1 in (1e-4, 1e-3, 1e-2):
        a1 = cozunurluk_bedeli(19.0, 3.0, t_simule_s=t1)["ensemble_gpu_gunu"]
        oranlar.append((a1 + taban) / taban)
    assert oranlar[0] < oranlar[1] < oranlar[2]      # monoton
    assert oranlar[1] < 1.01                          # t1=1e-3 -> %1'in alti
    assert oranlar[2] < 1.10                          # t1=1e-2 -> %10'un alti


def test_ADR_0043_var_ve_KILITLI_DEGIL() -> None:
    """Karar proje sahibinin; ADR `ÖNERİLDİ` durumunda kalmalı."""
    from pathlib import Path

    p = Path(__file__).resolve().parents[1] / "docs" / "adr" / \
        "ADR-0043-iki-asamali-cozunurluk.md"
    assert p.is_file()
    m = p.read_text(encoding="utf-8")
    assert "**ÖNERİLDİ**" in m and "kilitli değil" in m
    # Kilitlenmeden once olculmesi gerekenler YAZILI olmali.
    assert "kilitlenmeden** önce ölçülmesi" in m
    # Kolay ama YANLIS yol acikca reddedilmis olmali.
    assert "Reddedilmesi gereken kolay yol" in m
