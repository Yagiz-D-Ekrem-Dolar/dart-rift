"""ADR-0052 — çözünürlük standartlaştırması: ölçülmüş kayıt ve kuralları."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference import cozunurluk_standardi as S

# Olculen degerler (S_UY.json, S_A104.json, S_UG.json; KAYIT-069)
B_KABA = 3.68641784260915        # kaba merdiven, t_gecis 0,2 s, beta(300 s)
B_ORTA = 3.97837344216752
B_K15 = 4.023288070492537
B_O15 = 4.00625137799782
B_KABA_600 = 3.666916369763733   # ayni kol, 600 s (gecis ekseni bu anda olculdu)
B_G25 = 4.16680963998394         # kaba merdiven, t_gecis 2,5 s (600 s)
B_G50 = 4.164724275319047
B_L1 = 4.18                      # Raducan & Jutzi 2022, Tablo 2


def test_kayitlar_olculmus_degerlerle_tutuyor():
    h = S.olcum_bul("kaba@tg0.2", "yakinsak_h@tg0.2")
    beklenen = (np.mean([B_K15 - 1, B_ORTA - 1, B_O15 - 1])) / (B_KABA - 1.0)
    assert h.carpan == pytest.approx(beklenen, rel=1e-9)
    assert h.carpan == pytest.approx(1.118, abs=2e-3)      # "1,13 gibi bir katsayi"
    g = S.olcum_bul("kaba@tg0.2", "kaba@tg_yakinsak")
    # gecis ekseni 600 s degerlerinden olculdu (kaba kol 600 s'de 3,66692)
    assert g.carpan == pytest.approx((np.mean([B_G25, B_G50]) - 1.0)
                                     / (B_KABA_600 - 1.0), rel=1e-9)
    assert g.carpan == pytest.approx(1.187, abs=2e-3)
    for o in S.OLCUMLER:
        assert o.kanit and o.tarih and o.sigma > 0.0


def test_standartla_beta_eksi_1_uzerinden_ve_sigma_tasir():
    r = S.standartla(B_KABA, kaynak="kaba@tg0.2", hedef="yakinsak_h@tg0.2")
    assert r["beta"] == pytest.approx(1.0 + np.mean([B_K15 - 1, B_ORTA - 1, B_O15 - 1]),
                                     rel=1e-9)
    assert r["beta_sigma"] == pytest.approx((r["beta"] - 1.0) * 0.0076, rel=1e-9)
    # girdi hatasi ve carpan hatasi karelerin toplamiyla birlesir
    r2 = S.standartla(B_KABA, kaynak="kaba@tg0.2", hedef="yakinsak_h@tg0.2",
                      beta_sigma=0.1)
    bagil = np.hypot(0.1 / (B_KABA - 1.0), 0.0076)
    assert r2["beta_sigma"] == pytest.approx((r2["beta"] - 1.0) * bagil, rel=1e-9)
    # beta = 1 (hic ejekta) degismez
    assert S.standartla(1.0, kaynak="kaba@tg0.2", hedef="kaba@tg_yakinsak")["beta"] == 1.0


def test_OLCULMEMIS_donusum_REDDEDILIR():
    with pytest.raises(KeyError, match="OLCULMEDI"):
        S.standartla(B_KABA, kaynak="kaba@tg0.2", hedef="yakinsak_h@tg_yakinsak")
    with pytest.raises(ValueError, match="tanimsiz durum"):
        S.standartla(B_KABA, kaynak="kaba@tg0.2", hedef="ince@tg9")


def test_CARPMA_YASAK_ve_gerekcesi_sayiyla():
    h = S.olcum_bul("kaba@tg0.2", "yakinsak_h@tg0.2")
    g = S.olcum_bul("kaba@tg0.2", "kaba@tg_yakinsak")
    with pytest.raises(ValueError, match="CARPILMAZ"):
        S.carpan_carp(h, g)
    # yasagin sebebi: carpim, BIRLIKTE olculen noktayi %9'dan fazla asiyor
    carpim = 1.0 + h.carpan * g.carpan * (B_KABA - 1.0)
    assert carpim > B_G25 * 1.09 and carpim > B_L1 * 1.09


def test_guc_yasasi_uydurma_dort_olculmus_nokta():
    h = [1.0, 0.75, 0.5, 0.375]
    b = [B_KABA, B_K15, B_ORTA, B_O15]
    f = S.guc_yasasi_uydur(h, b)
    assert f["beta_sonsuz"] == pytest.approx(4.06, abs=0.05)
    assert f["p"] > 2.0                      # hata h ile HIZLI oluyor (esik gibi)
    assert f["artik_rms"] < 0.07
    with pytest.raises(ValueError):
        S.guc_yasasi_uydur([1.0, 0.5], [B_KABA, B_ORTA])


def test_iki_nokta_richardson_UYARIR_ve_p_varsayimi_kaydirir():
    r033 = S.richardson_iki_nokta(1.0, B_KABA, 0.5, B_ORTA, p=0.328)
    assert r033["beta_sonsuz"] == pytest.approx(5.11, abs=0.02)   # olculen 4,01
    assert "p VARSAYILDI" in r033["uyari"]
    r2 = S.richardson_iki_nokta(1.0, B_KABA, 0.5, B_ORTA, p=2.0)
    assert r2["beta_sonsuz"] == pytest.approx(4.08, abs=0.02)
    # yanlis p'nin bedeli: gercek olculen limite gore %25'ten fazla sapma
    assert abs(r033["beta_sonsuz"] - 4.01) / (4.01 - 1.0) > 0.25
    with pytest.raises(ValueError):
        S.richardson_iki_nokta(0.5, B_ORTA, 1.0, B_KABA, p=1.0)


def test_doyma_esigi():
    assert S.DOYMA_H_ORANI == 0.75
    assert S.yeterli_mi(0.5)["yeterli"] and S.yeterli_mi(0.75)["yeterli"]
    assert not S.yeterli_mi(1.0)["yeterli"]
    with pytest.raises(ValueError):
        S.yeterli_mi(0.0)


def test_olcum_dogrulamasi():
    with pytest.raises(ValueError, match="tanimsiz durum"):
        S.Olcum("x", "yok", "kaba@tg0.2", 1.0, 0.0, "k", "t")
    with pytest.raises(ValueError, match="carpan"):
        S.Olcum("x", "kaba@tg0.2", "kaba@tg_yakinsak", 0.0, 0.0, "k", "t")
    with pytest.raises(ValueError, match="sigma"):
        S.Olcum("x", "kaba@tg0.2", "kaba@tg_yakinsak", 1.0, -1.0, "k", "t")
