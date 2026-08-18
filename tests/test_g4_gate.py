"""G4 kapı yargısı **kod olarak** — kapının kendisi sınanıyor (FAZ 4.7)."""
from __future__ import annotations

import pytest

from dartrift.validation.g4_gate import (
    A1_MERMI_PARCACIK,
    A3_KUTLE_SAPMASI,
    B1_BETA_FARKI,
    KOSULLU_KABULLER,
    Olcut,
    degerlendir,
)

TAM_44 = {"A1_mermi_parcacik_cap": 2.6, "A2_r_ince_carpani": 8.0,
          "A3_kutle_sapmasi": 2.25e-05, "B1_beta_farki": 0.04,
          "B3_Aprime_daha_yakin": 1.0}
TAM_45 = {"B2_durulmus": 1.0, "B4_enerji_egim": 0.92}
TAM_46 = {"c1_kapsama": 1.0, "c2_en_dar": 0.142, "c3_gecti": True,
          "kuru": False}


def test_hicbir_olcum_yoksa_KAPI_GECMEZ() -> None:
    """Boşluk kontrolü: veri yokken kapı geçerse ölçüt boştur."""
    r = degerlendir()
    assert r.gecti is False
    assert len(r.kosulmayanlar) == 10
    assert r.dusenler == []


def test_TAM_veriyle_kapi_GECIYOR() -> None:
    r = degerlendir(TAM_44, TAM_45, TAM_46)
    assert r.a_gecti and r.b_gecti and r.c_gecti
    assert r.gecti is True
    assert r.kosulmayanlar == [] and r.dusenler == []


def test_KISMI_gecis_yok() -> None:
    """A ve B geçse bile C eksikse kapı geçmez."""
    r = degerlendir(TAM_44, TAM_45, None)
    assert r.a_gecti and r.b_gecti
    assert r.c_gecti is False
    assert r.gecti is False


def test_KURU_KIP_sayilmiyor() -> None:
    """Kuru kip hattın çalıştığını gösterir, kapıyı **geçirmez**."""
    r = degerlendir(TAM_44, TAM_45, dict(TAM_46, kuru=True))
    assert r.c_gecti is False
    assert set(r.kosulmayanlar) == {"C1", "C2", "C3"}
    assert r.gecti is False
    assert "kuru kip" in r.markdown()


@pytest.mark.parametrize("anahtar,deger,kimlik", [
    ("A1_mermi_parcacik_cap", 1.4, "A1"),
    ("A2_r_ince_carpani", 1.0, "A2"),
    ("A3_kutle_sapmasi", 0.02, "A3"),
    ("B1_beta_farki", 0.30, "B1"),
    ("B3_Aprime_daha_yakin", 0.0, "B3"),
])
def test_her_44_olcutu_AYRI_AYRI_dusebiliyor(anahtar, deger, kimlik) -> None:
    """ADR-0040: bir kriter düşebilmelidir — her biri **tek tek** sınanıyor."""
    r = degerlendir(dict(TAM_44, **{anahtar: deger}), TAM_45, TAM_46)
    assert kimlik in r.dusenler
    assert r.gecti is False


@pytest.mark.parametrize("anahtar,deger,kimlik", [
    ("B2_durulmus", 0.0, "B2"),
    ("B4_enerji_egim", 1.6, "B4"),
])
def test_her_45_olcutu_AYRI_AYRI_dusebiliyor(anahtar, deger, kimlik) -> None:
    r = degerlendir(TAM_44, dict(TAM_45, **{anahtar: deger}), TAM_46)
    assert kimlik in r.dusenler
    assert r.gecti is False


@pytest.mark.parametrize("anahtar,deger,kimlik", [
    ("c1_kapsama", 0.667, "C1"),
    ("c2_en_dar", 0.80, "C2"),
    ("c3_gecti", False, "C3"),
])
def test_her_46_olcutu_AYRI_AYRI_dusebiliyor(anahtar, deger, kimlik) -> None:
    r = degerlendir(TAM_44, TAM_45, dict(TAM_46, **{anahtar: deger}))
    assert kimlik in r.dusenler
    assert r.gecti is False


def test_EKSIK_anahtar_gecti_sayilmiyor() -> None:
    """Bir anahtar hiç yoksa `koşulmadı`dır, `geçti` değil."""
    eksik = {k: v for k, v in TAM_44.items() if k != "B1_beta_farki"}
    r = degerlendir(eksik, TAM_45, TAM_46)
    assert "B1" in r.kosulmayanlar
    assert "B1" not in r.dusenler
    assert r.gecti is False


def test_NAN_gecti_sayilmiyor() -> None:
    r = degerlendir(dict(TAM_44, B1_beta_farki=float("nan")), TAM_45, TAM_46)
    assert "B1" in r.kosulmayanlar
    assert r.gecti is False


def test_rapor_KOSULLU_KABULLERI_yaziyor() -> None:
    """Kapı geçse **bile** koşullar raporda kalmalı."""
    m = degerlendir(TAM_44, TAM_45, TAM_46).markdown()
    assert "GEÇİLDİ" in m
    assert "Koşullu kabuller" in m
    for k in KOSULLU_KABULLER:
        assert k[:40] in m


def test_rapor_GECEMEDIGINDE_nedeni_yaziyor() -> None:
    m = degerlendir(TAM_44, TAM_45, None).markdown()
    assert "GEÇİLEMEDİ" in m
    assert "koşulmayan ölçütler" in m
    assert "Kısmi geçiş yoktur" in m


def test_esikler_BELGE_ile_ayni() -> None:
    """Aynı sayı iki yerde yazılı; ayrışırsa test kırılsın (2. turun dersi)."""
    from pathlib import Path

    m = (Path(__file__).resolve().parents[1] / "docs" /
         "G4-OLCUTLERI.md").read_text(encoding="utf-8")
    assert f"{A1_MERMI_PARCACIK:g}".replace(".", ",") in m
    assert f"%{B1_BETA_FARKI * 100:g}" in m
    assert f"%{A3_KUTLE_SAPMASI * 100:g}".replace(".", ",") in m


def test_olcut_yonu_HER_IKI_yonde_calisiyor() -> None:
    assert Olcut("x", "", 0.5, 1.0, "<").gecti is True
    assert Olcut("x", "", 1.5, 1.0, "<").gecti is False
    assert Olcut("x", "", 1.5, 1.0, ">=").gecti is True
    assert Olcut("x", "", 0.5, 1.0, ">=").gecti is False
    assert Olcut("x", "", None, 1.0, "<").gecti is False


def test_NUMPY_tipleri_kosulmadi_SAYILMIYOR() -> None:
    """Ölçülen bir ölçüt **koşulmamış sayılmamalı** — kapının aynası.

    Bulunan kusur: `_al` `isinstance(v, (int, float))` ile süzüyordu ve
    numpy tiplerinin yalnızca bir kısmı Python sayılarının alt sınıfıdır:

    | tip | alt sınıf mı |
    |---|---|
    | `np.float64` | **evet** |
    | `np.int64` | hayır |
    | `np.bool_` | hayır |
    | `np.float32` | hayır |

    Ölçüldü — `np.float32` ve `np.bool_` girdilerle kapı
    `kosulmayan: ['A2', 'B2']` ve `dusen: ['C3']` diyordu. Üçü de
    **ölçülmüştü**.
    """
    import numpy as np

    o44 = {"A1_mermi_parcacik_cap": np.float64(2.6),
           "A2_r_ince_carpani": np.float32(8.0),
           "A3_kutle_sapmasi": np.float64(2e-5),
           "B1_beta_farki": np.float64(0.04),
           "B3_Aprime_daha_yakin": np.float64(1.0)}
    o45 = {"B2_durulmus": np.bool_(True), "B4_enerji_egim": np.float64(0.92)}
    o46 = {"c1_kapsama": np.float64(1.0), "c2_en_dar": np.float64(0.21),
           "c3_gecti": np.bool_(True), "kuru": False}
    r = degerlendir(o44, o45, o46)
    assert r.kosulmayanlar == [], r.kosulmayanlar
    assert r.dusenler == [], r.dusenler
    assert r.gecti is True


def test_numpy_bool_FALSE_dusuyor_KOSULMADI_degil() -> None:
    """`np.bool_(False)` `düştü` demeli, `koşulmadı` değil — ayrım önemli."""
    import numpy as np

    o44 = {"A1_mermi_parcacik_cap": 2.6, "A2_r_ince_carpani": 8.0,
           "A3_kutle_sapmasi": 2e-5, "B1_beta_farki": 0.04,
           "B3_Aprime_daha_yakin": 1.0}
    o45 = {"B2_durulmus": np.bool_(False), "B4_enerji_egim": 0.92}
    r = degerlendir(o44, o45, TAM_46)
    assert "B2" in r.dusenler
    assert "B2" not in r.kosulmayanlar


def test_sayiya_cevrilemeyen_deger_KOSULMADI() -> None:
    """Metin/liste gelirse `koşulmadı` — sessizce sayıya zorlanmamalı."""
    for bozuk in ("evet", [1.0], {"a": 1}, None):
        r = degerlendir(dict(TAM_44, B1_beta_farki=bozuk), TAM_45, TAM_46)
        assert "B1" in r.kosulmayanlar, bozuk


def test_TANILAR_olcut_DEGIL_ama_raporda_var() -> None:
    """Ölçümden sonra ölçülen bir büyüklük **ölçüt yapılmaz** (ADR-0040).

    Ama bilgi de gizlenmez: dikiş oranı ve tasarruf raporda görünüyor ve
    yanında *"ölçüt değil"* yazıyor.
    """
    o44 = dict(TAM_44, dikis_en_yakin_oran=0.6521, tasarruf=6.87)
    r = degerlendir(o44, TAM_45, TAM_46)
    assert r.tanilar == {"dikis_en_yakin_oran": 0.6521, "tasarruf": 6.87}
    # Tani DUSUK olsa BILE kapiyi etkilememeli -- olcut degil.
    r2 = degerlendir(dict(o44, dikis_en_yakin_oran=0.05), TAM_45, TAM_46)
    assert r2.gecti is True, "tani kapiyi etkiledi -- olcut olmus"
    assert r2.dusenler == []
    m = r2.markdown()
    assert "ölçüt değil" in m
    assert "0.05" in m


def test_TANILAR_yoksa_bolum_YAZILMIYOR() -> None:
    """Boş bir tanı tablosu yazmak gürültüdür."""
    m = degerlendir(TAM_44, TAM_45, TAM_46).markdown()
    assert "Tanılar" not in m


def test_kosucu_TANILARI_ust_duzeye_yaziyor() -> None:
    from pathlib import Path

    kaynak = (Path(__file__).resolve().parents[1] / "scripts" /
              "faz44_dart_yakinsama.py").read_text(encoding="utf-8")
    for k in ("dikis_en_yakin_oran", "tasarruf"):
        assert f'"{k}": ' in kaynak, k


# ------------------------------ TANILAR: "neden kosulmadi" gorunur olsun

def test_tani_kaynaklari_DOGRU_dosyadan_okunuyor():
    """`B2_sabit_seri` `faz45`'ten gelir; hepsini `faz44`'ten okumak onu
    sessizce **düşürürdü**."""
    from dartrift.validation.g4_gate import TANI_KAYNAGI, degerlendir
    r = degerlendir(faz44={"esit_t_sim": True},
                    faz45={"B2_sabit_seri": True, "B4_enerji_egim": 0.3})
    # `_al` her seyi float'a ceviriyor (np.bool_ dahil), yani bool -> 1.0.
    assert r.tanilar["esit_t_sim"] == 1.0
    assert r.tanilar["B2_sabit_seri"] == 1.0
    assert TANI_KAYNAGI["B2_sabit_seri"] == "faz45"
    # `faz45` verilmezse `B2_sabit_seri` HIC gorunmemeli.
    yalniz44 = degerlendir(faz44={"esit_t_sim": True})
    assert "B2_sabit_seri" not in yalniz44.tanilar


def test_tanilar_KAPIYI_gecirmiyor_ve_dusurmuyor():
    """Tanılar ölçüt **değil** — sonucu değiştirmemeli."""
    from dartrift.validation.g4_gate import degerlendir
    a = degerlendir(faz44={"A1_mermi_parcacik_cap": 3.0})
    b = degerlendir(faz44={"A1_mermi_parcacik_cap": 3.0, "esit_t_sim": False,
                           "dikis_en_yakin_oran": 0.01})
    assert a.gecti == b.gecti
    # `dusenler`/`kosulmayanlar` zaten KIMLIK dizesi donduruyor.
    assert a.dusenler == b.dusenler
    assert a.kosulmayanlar == b.kosulmayanlar
    # Tanilar RAPORDA gorunuyor ama karara girmiyor.
    assert "esit_t_sim" in b.tanilar and "esit_t_sim" not in a.tanilar


def test_her_TANI_icin_kaynak_gecerli():
    """`TANI_KAYNAGI` bilinmeyen bir kaynak gösterirse `KeyError` olurdu."""
    from dartrift.validation.g4_gate import TANI_KAYNAGI, TANILAR
    assert set(TANI_KAYNAGI) <= set(TANILAR)
    assert set(TANI_KAYNAGI.values()) <= {"faz44", "faz45", "faz46"}


def test_faz47_HAM_ciktiyi_OZETLIYOR():
    """Kapı koşucusu ham çıktıyı kapı anahtarlarına çevirmeli.

    Bulunan kusur: `_oku` ham dosyayı **olduğu gibi** döndürüyordu ve
    `faz44_ozet`/`faz45_ozet` hiç çağrılmıyordu. Kapı üst düzeyde
    `A1_mermi_parcacik_cap` arıyor; ham çıktıda o değer `sonuclar`
    altında iç içe. Sonuç: `A1`–`B4`'ün **yedisi birden** *"KOSULMADI"*
    çıkıyordu — ölçümler vardı, dönüştürülmüyorlardı.
    """
    import importlib.util as iu
    from pathlib import Path
    yol = Path(__file__).resolve().parents[1] / "scripts" / "faz47_g4_kapi.py"
    s = iu.spec_from_file_location("_faz47", yol)
    m = iu.module_from_spec(s)
    s.loader.exec_module(m)

    kaynak = yol.read_text(encoding="utf-8")
    assert "faz44_ozet" in kaynak and "faz45_ozet" in kaynak, \
        "ozet fonksiyonlari cagrilmiyor"
    # `_oku` ozetleyiciyi kabul etmeli
    import inspect
    assert "ozetle" in inspect.signature(m._oku).parameters


def test_faz47_ozetlenmis_dosyaya_DOKUNMUYOR(tmp_path):
    """Zaten özetlenmiş bir dosyaya özet uygulanırsa boş dönerdi."""
    import importlib.util as iu
    import json
    from pathlib import Path
    yol = Path(__file__).resolve().parents[1] / "scripts" / "faz47_g4_kapi.py"
    s = iu.spec_from_file_location("_faz47b", yol)
    m = iu.module_from_spec(s)
    s.loader.exec_module(m)

    p = tmp_path / "ozet.json"
    p.write_text(json.dumps({"A1_mermi_parcacik_cap": 2.04}), encoding="utf-8")
    d = m._oku(str(p), lambda h: {})       # ozetleyici bos donse bile
    assert d == {"A1_mermi_parcacik_cap": 2.04}, d


def test_A1_kaynagi_faz48_oldugunda_KABULLERDE_yaziyor():
    """`A1`'in kaynağı değiştiyse rapor bunu **söylemeli**.

    `faz44` yakınsama **kollarını** ölçüyor (tekdüze / iki bölgeli);
    `A1` ise çıkarımın kullandığı **sahneyi** sormalı ve ensemble iki
    aşamalı modelle koşuldu. `faz44`'ün kendi `A1`'i `0,215`, üretimde
    `2,0391` — aradaki fark ölçüt için hayati.

    Sessiz bir kaynak değişikliği, yanlış bir sayı kadar zararlıdır:
    okuyan `A1`'in nereden geldiğini bilmeden *"geçti"* görür.
    """
    from dartrift.validation.g4_gate import KOSULLU_KABULLER
    metin = " ".join(KOSULLU_KABULLER)
    assert "faz48" in metin and "A1" in metin, \
        "A1 kaynak degisikligi kosullu kabullerde yazili degil"


def test_faz47_faz48_bayragi_var():
    from pathlib import Path
    yol = Path(__file__).resolve().parents[1] / "scripts" / "faz47_g4_kapi.py"
    kaynak = yol.read_text(encoding="utf-8")
    assert "--faz48" in kaynak
    # Degistirilen deger GORUNUR olmali: eski deger de basiliyor mu
    assert "KULLANILMADI" in kaynak


def test_B2_yolda_madde_varsa_YAZILMIYOR():
    """`β` düz olabilir çünkü **bitti**, ya da çünkü **daha başlamadı**.

    Ölçüldü (A9): DART koşusunda `t = 20 s`'de `2786` parçacık hâlâ
    yolda, geçiş süresi medyan `57–75 s`. O seride `β` bit düzeyinde
    düzdü ve eski ölçüt *"durulmuş"* diyordu.
    """
    from dartrift.validation.g4_ozet import faz45_ozet
    temel = {"beta_bound_settled": True,
             "beta_bound_settling_diag": {"sabit": False}}
    yolda = faz45_ozet({**temel, "n_bekleyen_son": 2786})
    assert "B2_durulmus" not in yolda, "yolda madde varken B2 yazilmamali"
    assert yolda["B2_yolda_madde"] == 2786
    bos = faz45_ozet({**temel, "n_bekleyen_son": 0})
    assert bos["B2_durulmus"] == 1.0


def test_B2_tani_yoksa_BAYRAK_kalkiyor():
    """Eski koşular tanıyı taşımıyor: `B2` yazılır ama **işaretlenir**.

    Bilinmeyeni sessizce *"geçti"* saymak A9'un şikâyetiydi; burada
    geçiyor ama **görünür** biçimde denetlenmemiş sayılıyor.
    """
    from dartrift.validation.g4_ozet import faz45_ozet
    o = faz45_ozet({"beta_bound_settled": True,
                    "beta_bound_settling_diag": {"sabit": False}})
    assert o["B2_durulmus"] == 1.0
    assert o["B2_gecis_denetlenmedi"] is True
