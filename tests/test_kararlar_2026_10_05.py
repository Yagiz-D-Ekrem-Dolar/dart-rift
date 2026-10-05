"""Beş kararın (A2, C1, A105, A109, ADR-0058) **kabul edilmiş** hâli.

Kararlar 2026-10-05'te kullanıcı tarafından Claude'a devredildi ve verildi;
gerekçe ve geri alma koşulu KAYIT-075'te. Bu sınavlar kararların **koda ve
belgeye geçtiğini** kilitler.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "scripts"))


def test_bes_ADR_de_KABUL_EDILDI():
    adlar = ("ADR-0053-y0-onseli-ve-tanimlayici-gozlemli",
             "ADR-0054-c1-gozlenen-beta-hangi-sayi",
             "ADR-0056-a105-matris-cekme-dayanimi",
             "ADR-0057-a109-hangi-blok-modeli",
             "ADR-0058-uretim-posteriorunun-tarifi")
    for ad in adlar:
        m = (KOK / "docs" / "adr" / f"{ad}.md").read_text(encoding="utf-8")
        assert "**KABUL EDİLDİ** (2026-10-05)" in m, ad
        assert "KAYIT-075" in m, ad
        assert "ÖNERİ (karar kullanıcıda" not in m, ad


# --------------------------------------------------- C1 (ADR-0054)
def test_C1_uretim_hedefi_sahnenin_kutlesinden():
    from dartrift.observables.dart_gozlemleri import uretim_hedef_beta
    d = uretim_hedef_beta(4.2980e9)
    assert d["beta"] == pytest.approx(3.5418, abs=0.001)
    assert d["sigma_ust"] == pytest.approx(0.188, abs=0.002)
    assert d["sigma_alt"] == pytest.approx(0.247, abs=0.002)
    # kutle degisirse hedef DE degisir (beta ~ M); eski sabit sayi DEGIL
    d2 = uretim_hedef_beta(4.5e9)
    assert d2["beta"] > d["beta"]
    assert d["yerine_gectigi"]["deger"] == 3.12      # eski deger KAYITTA
    assert "ADR-0054" in d["karar"]
    with pytest.raises(ValueError):
        uretim_hedef_beta(0.0)


# --------------------------------------------------- A109 (ADR-0057)
def test_A109_blok_yaricaplari_SAYI_olarak_kilitli():
    from dartrift.setup.rubble_generator import URETIM_BLOK as B
    assert (B["r_min"], B["r_max"], B["q"]) == (14.0, 56.0, 3.0)
    # cismin kisa yari ekseni 58 m; r_max onun ALTINDA olmali
    assert B["r_max"] < 58.0
    # kapsam siniri YAZILI
    assert "cikarimin erisiminde DEGIL" in B["kapsam"]
    assert "ADR-0057" in B["karar"]


# --------------------------------------------------- A105 (ADR-0056)
def test_A105_kosullu_cumle_HER_raporda():
    import dy_dart_raporu as DY
    assert "KOSULLUDUR" in DY.KOSULLU_CEKME
    assert "%23" in DY.KOSULLU_CEKME and "ADR-0056" in DY.KOSULLU_CEKME
    # cekme terimi butceye GIRMEMIS olmali
    assert "matris_cekme" not in DY.TERIMLER


def test_A105_rapor_cumleyi_yaziyor(tmp_path, capsys):
    import json

    import dy_dart_raporu as DY
    import numpy as np
    d = tmp_path / f"{DY.AD_DY2}.durumlar"
    d.mkdir(parents=True)
    t = np.geomspace(1e-3, 600.0, 30)
    egri = [[float(x), 1.0, 3.75, 1e6] for x in t]
    np.savez(d / "nokta_0000_a.npz",
             fizik_tani=json.dumps({"beta_hedef": 3.75, "M_ejekta": 2e7,
                                    "impuls_egrisi": egri,
                                    "beta_iki_yontem": {"beta_km": 3.8}}),
             gecerlilik=json.dumps({"gecerli": True}), m=np.ones(50))
    yol = tmp_path / "S.json"
    assert DY.main(["--kok", str(tmp_path), "--ad", DY.AD_DY2,
                    "--json", str(yol)]) == 0
    kayit = json.loads(yol.read_text(encoding="utf-8"))
    assert "KOSULLUDUR" in kayit["kosullu_cekme"]
    assert "[kosul]" in capsys.readouterr().out


# ------------------------------------- PROTOKOL-HAVUZ (kosudan ONCE yazildi)
def test_PROTOKOL_HAVUZ_bes_karari_da_iceriyor():
    m = (KOK / "docs" / "truba" / "PROTOKOL-HAVUZ-URETIM.md").read_text(
        encoding="utf-8")
    assert "havuz gönderilmeden ÖNCE" in m
    for adr in ("ADR-0053", "ADR-0054", "ADR-0055", "ADR-0056", "ADR-0057",
                "ADR-0058"):
        assert adr in m, adr
    # Onselin DO'ya bagli kapisi: UC yargi + OKUNMAZ dali
    for yargi in ("ONSEL GOZLEMI ICERMIYOR", "GOZLEM ONSEL KENARINDA",
                  "ONSEL GOZLEMI ICERIYOR", "OKUNMAZ"):
        assert yargi in m, yargi
    # SBC KAPISI ve paydayi buyutme yasagi
    assert "SBC KAPISI" in m and "YAYIMLANMAZ" in m
    assert "Paydayı büyütüp geçmek yasak" in m
    # beklenen sayim (kural 8) ve kayip esikleri
    assert "beklediğini sayar" in m and "> %20" in m
    # kapsam siniri ve "uc parametreyi cozduk" demeyecegi
    assert "çıkarımın erişiminde" in m
    assert "Üç parametreyi çözdük" in m


def test_KAYIT075_her_karar_icin_DUSURECEK_olcumu_yaziyor():
    m = (KOK / "docs" / "defter" /
         "KAYIT-075_2026-10-05_bes-karar-verildi.md").read_text(encoding="utf-8")
    # bes karar + her birinin geri alma kosulu
    assert m.count("Bu kararı düşürecek şey") >= 4
    assert "kararları sen ver" in m          # yetkinin devri kayitta
    assert "sonuçlarını görmedim" in m       # DO/DC/DN kosarken verildi
