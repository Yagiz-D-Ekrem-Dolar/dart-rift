"""DART'ın **yayımlanmış gözlemleri** — tek kaynak, teyit düzeyiyle (ADR-0050).

Neden tek dosya: aynı sayı (β, ejekta kütlesi, koni açısı) betiklerde ayrı ayrı
yazılırsa biri güncellenip öteki unutulur. Buradaki her değerin yanında
**kaynağı** ve **teyit düzeyi** vardır:

- `tam_metin` — makalenin kendisi okundu.
- `sayfa_ozeti` — yayıncı sayfasından araç özeti.
- `arama_ozeti` — yalnız arama sonucu; **birebir teyit edilmedi**.

Ayrıntılı tablo: `docs/LITERATUR-DART-SIMULASYONLARI.md`.

> Bu modül **kilitli protokollerin** gözlem değerlerini değiştirmez. Protokol U
> ve V `period_interface.dart_beta_budget` ile üretilen `β = 3,12 ± 0,34`
> üzerinden yargı verdi; buradaki değerler yeni protokoller ve **yan yana**
> karşılaştırma içindir.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Gozlem", "GOZLEMLER", "cheng_beta", "EJEKTA_KUTLESI",
           "KONI_ACISI", "KONI_ACISI_HST", "KONI_ELIPTIK", "DIMORPHOS_SEKIL"]


@dataclass(frozen=True)
class Gozlem:
    """Tek bir gözlem: değer, 1σ, birim, kaynak, teyit düzeyi."""

    ad: str
    deger: float
    sigma: float
    birim: str
    kaynak: str
    teyit: str
    not_: str = ""


#: Cheng ve diğ. 2023 (*Nature* 616, 457): `β = 3,61 (+0,19 / −0,25)` (1σ),
#: Dimorphos yığın yoğunluğu `2400 kg/m³` varsayımıyla; `1500–3300 kg/m³`
#: aralığında `β = 2,2 – 4,9`. Yayımlanan bağıntı `β = 3,61 ρ/2400 − 0,03`.
CHENG_BETA_2400 = 3.61
CHENG_BETA_SIGMA = (0.25, 0.19)     # (-, +)
CHENG_SABIT = 0.03
CHENG_RHO_REF = 2400.0

#: Ejekta kütlesi (LICIACube): `1,6 ± 0,3 × 10⁷ kg` (Lolachi ve diğ. 2025).
EJEKTA_KUTLESI = Gozlem(
    "ejekta_kutlesi", 1.6e7, 0.3e7, "kg",
    "Lolachi ve dig. 2025, PSJ (doi:10.3847/PSJ/adec6b)", "arama_ozeti",
    "Graykowski ve dig. 2023 alt sinir olarak 1,3-2,2e7 kg veriyor")

#: Ejekta konisinin tam açıklığı: `140 ± 4°` (Dotto ve diğ. 2024).
KONI_ACISI = Gozlem(
    "ejekta_koni_tam_acisi", 140.0, 4.0, "derece",
    "Dotto ve dig. 2024, Nature (doi:10.1038/s41586-023-06998-2)",
    "arama_ozeti",
    "Baska analizde eliptik koni: ~94,8 x ~133,3 derece")

#: Ayni koninin DIGER olcumleri (2026-09-18 taramasi). Hepsi gorunen tozun
#: KENARINDAN olculuyor; model tarafinda kutle yuzdeligi DEGIL, `kenar`
#: (%99) acisi karsilastirilmali. Tanim farki yuzunden bu uc deger birbiriyle
#: de tam ortusmuyor -- tek bir "gozlem" gibi kullanilmamali.
KONI_ACISI_HST = Gozlem(
    "ejekta_koni_tam_acisi_hst", 125.0, 10.0, "derece",
    "HST gozlemleri (Li ve dig. 2023 / Hirabayashi ve dig. 2023, arama ozeti)",
    "arama_ozeti", "uc boyutlu acilma acisi, konum acilarindan basit modelle")
KONI_ELIPTIK = {
    "dar_derece": (94.8, 5.4), "genis_derece": (133.3, 9.2),
    "kaynak": "Hirabayashi ve dig. 2023 (HST + LICIACube LUKE)",
    "teyit": "arama_ozeti",
    "not": "koni tabani eliptik ve donuk; dairesel koni veriye uymuyor",
}

#: Dimorphos şekil modeli (çarpma öncesi): `177 × 174 × 116 m`,
#: hacim `1,81e6 m³` → eşdeğer yarıçap `~75,4 m`.
DIMORPHOS_SEKIL = {
    "eksenler_m": (177.0, 174.0, 116.0),
    "yari_eksenler_m": (88.5, 87.0, 58.0),
    "hacim_m3": 1.81e6,
    "kaynak": "Daly ve dig. 2023 (L2 uzerinden)",
    "teyit": "sayfa_ozeti",
}

#: Çarpma açısı: yüzey normalinden `~17°`, şekil merkezine `< 25 m`.
CARPMA_ACISI = Gozlem(
    "carpma_acisi_normalden", 17.0, 7.0, "derece",
    "Daly ve dig. 2023 (arama ozeti uzerinden)", "arama_ozeti",
    "sigma bir TAHMIN; makaleden teyit edilmeli")

GOZLEMLER = (EJEKTA_KUTLESI, KONI_ACISI, KONI_ACISI_HST, CARPMA_ACISI)


def cheng_beta(yogunluk: float | None = None, *,
               hedef_kutlesi: float | None = None,
               hacim_m3: float = DIMORPHOS_SEKIL["hacim_m3"]) -> dict:
    """Cheng ve diğ. 2023 bağıntısıyla gözlenen `β`.

    `β(ρ) = 3,61 · ρ/2400 − 0,03`. Kütle verilirse yoğunluk `ρ = M/V` ile
    (şekil modelinin hacmiyle) hesaplanır — sahnemizin hacmi şekil modelinden
    büyük olduğu için bu ayrım **önemlidir**: `β` kütleyle ölçekleniyor.

    Döner: `beta`, `beta_alt`, `beta_ust` (asimetrik 1σ), `yogunluk`.
    """
    if (yogunluk is None) == (hedef_kutlesi is None):
        raise ValueError("yogunluk YA DA hedef_kutlesi verin (biri)")
    if hedef_kutlesi is not None:
        if hedef_kutlesi <= 0.0 or hacim_m3 <= 0.0:
            raise ValueError("kutle ve hacim pozitif olmali")
        yogunluk = float(hedef_kutlesi) / float(hacim_m3)
    yogunluk = float(yogunluk)
    if yogunluk <= 0.0:
        raise ValueError(f"yogunluk pozitif olmali, {yogunluk} geldi")
    olcek = yogunluk / CHENG_RHO_REF
    b = CHENG_BETA_2400 * olcek - CHENG_SABIT
    return {
        "beta": float(b),
        "beta_alt": float((CHENG_BETA_2400 - CHENG_BETA_SIGMA[0]) * olcek
                          - CHENG_SABIT),
        "beta_ust": float((CHENG_BETA_2400 + CHENG_BETA_SIGMA[1]) * olcek
                          - CHENG_SABIT),
        "yogunluk": yogunluk,
        "kaynak": "Cheng ve dig. 2023, Nature 616, 457",
        "teyit": "tam_metin",
    }
