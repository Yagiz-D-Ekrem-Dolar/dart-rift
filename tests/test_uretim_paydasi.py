"""PROTOKOL-HAVUZ §5'in ilan ettiği üretim paydası KOŞULABİLİR mi?

## Niçin bu sınav var

2026-10-13'te şu bulundu: `cozunurluk_yakin` terimi protokolde ilan
edilmiş, ölçümü 19–20 Eylül'de koşmuş, indirgemesi 29 Eylül'de
arşivlenmiş — ama koda **hiç bağlanmamış**, `nan` duruyordu. Mevcut
betikler eski dört terimli pilot seçimini kullandığı için hiçbir sınav
düşmedi. Üretim posterioru ilk çağrıda `ValueError` ile düşecekti ve bu
ancak havuz dolduktan sonra, en sıkışık anda görülecekti.

Bu, depoda tekrarlayan bir kusur sınıfının (A116: *"yazılmış ama
bağlanmamış"*) sayısal sabitlerdeki hâlidir. Geçen bir sınav takımı,
bağlanmış bir üretim yolu demek değildir.

Buradaki iki sınav o boşluğu kapatır:

1. İlan edilen her terim **sonlu** mu — yani payda gerçekten hesaplanabilir mi;
2. Koddaki sabit, **arşivlenmiş ölçüm dosyasıyla** tutuyor mu — yani
   biri değeri elle değiştirirse yakalanır mı.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from dartrift.inference.tarih_esleme import (
    MODEL_EKSIKLIGI_KAYNAKLI,
    model_eksikligi_kaynakli,
)

#: Paydaya giren altı terim — KAYIT-076 §7 (en güncel seçim).
#:
#: PROTOKOL-HAVUZ §5 bu satırı `carpma_yeri` (L12 ödünç `0,10`) ile
#: yazmıştı; DN koşusu 2026-10-06'da ölçünce kayıt onu
#: `carpma_yeri_olculen` `0,030` ile DEĞİŞTİRDİ. Eski ödünç küme
#: `σ_model = 0,291` veriyordu, ölçülen küme `0,181`: payda `%38`
#: küçüldü, yani sınav ZORLAŞTI. Yanlış adı seçmek paydayı sahte
#: biçimde gevşetir, bu yüzden ad burada sabittir.
URETIM_TERIMLERI_BETA = (
    "gerceklem_beta_DART",
    "cozunurluk_uzak",
    "cozunurluk_yakin",
    "plato_olculen_DART",
    "hedef_sekli_olculen",
    "carpma_yeri_olculen",
)

#: KAYIT-076 §7'nin bildirdiği bağıl toplam.
URETIM_SIGMA_BAGIL = 0.0658

#: Aynı belgenin `M_ejekta` satırı.
URETIM_TERIMLERI_MEJ = ("gerceklem_M_ejekta_DART",)

#: UY2 kesişim ölçümünün arşivi (KAYIT-071).
S_UY2 = Path(__file__).resolve().parents[1] / (
    "docs/olcumler/UY2_DY_2026-09-29/S_UY2.json")


@pytest.mark.parametrize("ad", URETIM_TERIMLERI_BETA + URETIM_TERIMLERI_MEJ)
def test_ilan_edilen_her_terim_OLCULMUS(ad: str) -> None:
    """Protokolde ilan edilen bir terim `nan` kalamaz.

    `nan` bir terimi sessizce sıfır saymak, ölçülmemiş bir kesinlik
    iddiasıdır; bu yüzden `model_eksikligi_kaynakli` hata verir. O hata
    doğru davranıştır — ama üretim gününde değil, BUGÜN görülmelidir.
    """
    assert ad in MODEL_EKSIKLIGI_KAYNAKLI, (
        f"{ad} protokolde ilan edildi ama MODEL_EKSIKLIGI_KAYNAKLI'da yok")
    deger, kaynak = MODEL_EKSIKLIGI_KAYNAKLI[ad]
    assert math.isfinite(deger), (
        f"{ad} hala olculmedi ({kaynak}). PROTOKOL-HAVUZ §5 bu terimi "
        f"ILAN ETTIGI icin uretim posterioru duser.")


def test_uretim_paydasi_HESAPLANABILIYOR() -> None:
    """Payda uçtan uca çağrılabiliyor mu — tek tek terim değil, bütün."""
    sonuc = model_eksikligi_kaynakli(1.0, list(URETIM_TERIMLERI_BETA))
    assert math.isfinite(sonuc["sigma"]) and sonuc["sigma"] > 0.0
    assert set(sonuc["terimler"]) == set(URETIM_TERIMLERI_BETA)


def test_uretim_paydasi_KAYITLA_TUTUYOR() -> None:
    """Hesaplanan toplam, KAYIT-076 §7'nin bildirdiği sayıyla tutmalı.

    Kayıttaki `0,0658` terimler `0,053` gibi yuvarlanmış yazılarak
    hesaplanmıştı; kod arşivdeki tam değeri (`0,053438`) kullanıyor.
    Bu yüzden eşitlik değil, `%1` tolerans aranır. Daha büyük bir sapma
    terim kümesinin DEĞİŞTİĞİ anlamına gelir ve bakılmalıdır.
    """
    sigma = model_eksikligi_kaynakli(1.0, list(URETIM_TERIMLERI_BETA))["sigma"]
    assert sigma == pytest.approx(URETIM_SIGMA_BAGIL, rel=0.01), (
        f"payda {sigma:.5f}, KAYIT-076 {URETIM_SIGMA_BAGIL} diyor")


def test_odunc_carpma_yeri_SECILMEMELI() -> None:
    """`carpma_yeri` (L12 ödünç `0,10`) üretim kümesinde OLMAMALI.

    Ölçülen `0,030` yerine ödünç `0,10` seçilirse payda `0,0654`'ten
    `0,116`'ya çıkar — `%77` gevşer. Tarih eşleme kesmesi (`I > 3`) o
    paydayla neredeyse hiçbir noktayı dışlamaz; dejenerasyon ölçülemez
    hâle gelir. Sessizce yanlış tarafa kayan bir hata olduğu için
    ayrıca sınanır.
    """
    assert "carpma_yeri" not in URETIM_TERIMLERI_BETA
    odunc = float(MODEL_EKSIKLIGI_KAYNAKLI["carpma_yeri"][0])
    olculen = float(MODEL_EKSIKLIGI_KAYNAKLI["carpma_yeri_olculen"][0])
    assert olculen < odunc, "olculen deger oduncten kucuk olmali"


def test_cozunurluk_yakin_ARSIVLE_TUTUYOR() -> None:
    """Koddaki sabit, ölçümün arşivlendiği dosyayla aynı olmalı.

    Sabit elle değiştirilirse ya da arşiv güncellenip kod unutulursa bu
    sınav düşer. İki kaynağın sessizce ayrışmasını engeller.
    """
    if not S_UY2.exists():
        pytest.skip(f"arsiv yok: {S_UY2}")
    arsiv = json.loads(S_UY2.read_text(encoding="utf-8"))
    beklenen = float(arsiv["delta_kesisim"])
    kodda = float(MODEL_EKSIKLIGI_KAYNAKLI["cozunurluk_yakin"][0])
    assert kodda == pytest.approx(beklenen, rel=1e-4, abs=1e-6), (
        f"kod {kodda} != arsiv {beklenen} (S_UY2.json delta_kesisim)")


def test_cozunurluk_yakin_UY_DEGIL_UY2() -> None:
    """Yanlış ölçümü bağlamaya karşı koruma.

    `S_UY.json` de bir `sigma_cozunurluk` tutuyor (`0,098`) ama o
    `t_gecis = 0,2 s`'te ölçüldü — üretim ayarı değil. Üretim `1,0 s`
    kullanıyor ve doğru değer UY2'nin `delta_kesisim`'idir. İkisi
    karıştırılırsa payda neredeyse iki katına çıkar ve karşılaştırma
    sahte biçimde gevşer.
    """
    kodda = float(MODEL_EKSIKLIGI_KAYNAKLI["cozunurluk_yakin"][0])
    assert kodda < 0.08, (
        f"{kodda} UY'nin 0,098'ine yakin -- UY2 (0,0534) baglanmali, "
        "UY degil (t_gecis 0,2 s uretim ayari DEGIL)")
