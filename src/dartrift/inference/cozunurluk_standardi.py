"""Çözünürlükler arası **standartlaştırma** — ölçülmüş düzeltmeler kaydı (ADR-0052).

## Neden

Aynı `θ`, farklı sayısal ayar → farklı `β`. Bu bir kod hatası değil,
**ayrıklaştırma hatasıdır**: kaba ızgarada şok bir parçacık boyuna yayılır,
yapay viskozite `h` ile büyür (A98), geç evreye erken geçilirse akış donar
(A97). Havuzu ucuz ayarla koşup sonucu "standart" ayara taşımak istiyoruz.

Bu **mühendisliktir, fizik değildir** ve üç kuralla yapılırsa savunulabilir:

1. Düzeltme **ölçülür**, seçilmez. Her kayıt hangi koşulardan çıktığını yazar.
2. Düzeltme **hata payıyla** taşınır; `standartla` her zaman `sigma` döndürür.
3. **Ayrı ölçülmüş iki eksenin çarpanı ÇARPILMAZ** (`carpan_carp` hata verir).

## Üçüncü kural neden var (ölçüldü, 2026-09-28)

L1 kıyas sahnesinde `Y₀ = 10 Pa`, `β(300 s)`:

| eksen | kaynak → hedef | çarpan (`β − 1`) |
|---|---|---|
| çözünürlük (`h`) | kaba → yakınsak (`t_geçiş = 0,2 s`) | **1,118** |
| geçiş anı | `0,2 s` → yakınsak (kaba merdiven) | **1,187** |

İkisini çarparsak `1,327` → `β = 4,57`. Oysa aynı sahnede literatür değeri
`4,18` ve **birlikte ölçülen** nokta (kaba + `t_geçiş = 2,5 s`) `4,167`.
Yani iki hata bağımsız değil; çarpmak aynı eksikliği iki kez sayıyor.
`A103` da aynı şeyi merdivenin bölgeleri için ölçtü: katkılar **toplamsal
değil**.

## `β` mi, `β − 1` mi

Bütün çarpanlar `β − 1` (ejekta katkısı) üzerinden tanımlıdır. `β`'nın
kendisi üzerinden çarpmak `β = 1` (hiç ejekta) durumunu da ölçeklerdi;
mermiden gelen `1` sayısal ayardan etkilenmez.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = ["Olcum", "OLCUMLER", "standartla", "olcum_bul", "carpan_carp",
           "guc_yasasi_uydur", "richardson_iki_nokta", "yeterli_mi",
           "DOYMA_H_ORANI", "DURUMLAR"]

#: Ölçülen doyma eşiği: `h_bağıl ≤ 0,75`'te üç kol `β = 4,02 ± 0,02`
#: (`%0,6`). Bunun altında inceltmek ölçüm hassasiyetinde bir şey
#: değiştirmedi (A104 + UY).
DOYMA_H_ORANI = 0.75

#: Tanımlı sayısal durumlar (ad → açıklama). `standartla` yalnız bu adları alır.
DURUMLAR = {
    "kaba@tg0.2": "kaba merdiven (h_bagil 1,0), t_gecis = 0,2 s",
    "kaba@tg_yakinsak": "kaba merdiven, t_gecis >= 2,5 s (UG: yakinsamis)",
    "yakinsak_h@tg0.2": "h_bagil <= 0,75 (orta / k15 / o15), t_gecis = 0,2 s",
    "yakinsak_h@tg_yakinsak": "h yakinsak VE t_gecis yakinsak (OLCULMEDI)",
}


@dataclass(frozen=True)
class Olcum:
    """Tek bir **ölçülmüş** durum dönüşümü (`β − 1` çarpanı)."""

    eksen: str
    kaynak: str
    hedef: str
    carpan: float
    sigma: float          # bağıl (çarpanın kendi belirsizliği)
    kanit: str
    tarih: str

    def __post_init__(self) -> None:
        for ad in (self.kaynak, self.hedef):
            if ad not in DURUMLAR:
                raise ValueError(f"tanimsiz durum: {ad}")
        if not (self.carpan > 0.0 and math.isfinite(self.carpan)):
            raise ValueError(f"carpan pozitif ve sonlu olmali: {self.carpan}")
        if not (self.sigma >= 0.0 and math.isfinite(self.sigma)):
            raise ValueError(f"sigma >= 0 ve sonlu olmali: {self.sigma}")


#: Çarpanların çıktığı **ölçülmüş** `β` değerleri (L1 kıyas sahnesi,
#: `Y₀ = 10 Pa`). Çarpan elle yazılmaz, buradan hesaplanır — sayı ile kanıt
#: arasında kopukluk olmasın.
OLCULEN_BETA = {
    # h ekseni: beta(300 s), t_gecis = 0,2 s
    "kaba@tg0.2": 3.68641784260915,          # W2_Y10_g0p2 (h_bagil 1,0)
    "A104_k15@tg0.2": 4.023288070492537,     # ayni N, h/s = 1,5 (h_bagil 0,75)
    "UY_orta@tg0.2": 3.97837344216752,       # 48 m ici 2x ince (h_bagil 0,5)
    "A104_o15@tg0.2": 4.00625137799782,      # orta + h/s = 1,5 (h_bagil 0,375)
    # gecis ani ekseni: beta(600 s), kaba merdiven
    "kaba@tg0.2_600": 3.666916369763733,
    "kaba@tg2.5_600": 4.16680963998394,
    "kaba@tg5.0_600": 4.164724275319047,
}


def _b(ad: str) -> float:
    return OLCULEN_BETA[ad] - 1.0


_YAKINSAK_H = (_b("A104_k15@tg0.2") + _b("UY_orta@tg0.2")
               + _b("A104_o15@tg0.2")) / 3.0
_YAKINSAK_TG = 0.5 * (_b("kaba@tg2.5_600") + _b("kaba@tg5.0_600"))

#: **Ölçülmüş** dönüşümler. Yeni bir satır ancak koşu kanıtıyla eklenir.
OLCUMLER: tuple[Olcum, ...] = (
    Olcum(
        eksen="cozunurluk_h",
        kaynak="kaba@tg0.2", hedef="yakinsak_h@tg0.2",
        carpan=_YAKINSAK_H / _b("kaba@tg0.2"),
        # uc yakinsak kolun sacilmasi (ornek sd / ortalama) = 0,0076
        sigma=0.0076,
        kanit="S_UY.json + S_A104.json (UY_orta, A104_k15, A104_o15, W2_Y10_g0p2)",
        tarih="2026-09-28"),
    Olcum(
        eksen="gecis_ani",
        kaynak="kaba@tg0.2", hedef="kaba@tg_yakinsak",
        carpan=_YAKINSAK_TG / _b("kaba@tg0.2_600"),
        # Y0'a gore kayma: 0,2 -> 1,0 carpani Y50/Y10/Y1'de
        # 1,0865 / 1,1511 / 1,1327 -> bagil yayilim ~0,03
        sigma=0.03,
        kanit="S_UG.json (UG_Y10_g2p5, UG_Y10_g5p0, W2_Y10_g0p2/g1p0)",
        tarih="2026-09-28"),
)


def olcum_bul(kaynak: str, hedef: str) -> Olcum:
    """`kaynak → hedef` için **ölçülmüş** kaydı getir; yoksa `KeyError`."""
    for o in OLCUMLER:
        if o.kaynak == kaynak and o.hedef == hedef:
            return o
    for ad in (kaynak, hedef):
        if ad not in DURUMLAR:
            raise ValueError(f"tanimsiz durum: {ad}")
    raise KeyError(
        f"'{kaynak}' -> '{hedef}' OLCULMEDI. Iki ayri eksende olculmus "
        f"carpanlari CARPARAK bu donusumu uretmek yasak (modul basligi): "
        f"olculen tek ortak nokta kaba@tg_yakinsak; onun otesi icin "
        f"orta merdiven x t_gecis >= 2,5 s kosusu gerekir.")


def standartla(beta: float, *, kaynak: str, hedef: str,
               beta_sigma: float = 0.0) -> dict:
    """`β`'yı `kaynak` ayarından `hedef` ayarına **ölçülmüş** çarpanla taşı.

    `β_hedef = 1 + çarpan · (β_kaynak − 1)`; hata payı çarpanın kendi
    belirsizliğiyle birleştirilir (bağıl karelerin toplamı).
    """
    if not math.isfinite(beta) or beta < 1.0:
        raise ValueError(f"beta >= 1 ve sonlu olmali, {beta} geldi")
    if beta_sigma < 0.0 or not math.isfinite(beta_sigma):
        raise ValueError("beta_sigma >= 0 ve sonlu olmali")
    o = olcum_bul(kaynak, hedef)
    b = beta - 1.0
    b_yeni = o.carpan * b
    # bagil hatalar: girdiden gelen + carpanin kendi belirsizligi
    bagil_girdi = (beta_sigma / b) if b > 0.0 else 0.0
    bagil = math.hypot(bagil_girdi, o.sigma)
    return {"beta": 1.0 + b_yeni,
            "beta_sigma": b_yeni * bagil,
            "carpan": o.carpan,
            "carpan_sigma": o.sigma,
            "olcum": o}


def carpan_carp(*olcumler: Olcum) -> float:
    """**Her zaman hata verir** — ayrı ölçülmüş çarpanlar çarpılamaz.

    Bu işlev bilerek vardır: çarpmak isteyen kod burada durur ve modül
    başlığındaki ölçümü (1,118 × 1,187 = 1,327 → `β = 4,57`, oysa birlikte
    ölçülen 4,167) okur.
    """
    adlar = " x ".join(f"{o.eksen}" for o in olcumler) or "(bos)"
    raise ValueError(
        f"AYRI OLCULMUS CARPANLAR CARPILMAZ ({adlar}). Iki eksenin ortak "
        f"etkisi BIRLIKTE olculmelidir; carpmak ayni eksikligi iki kez sayar "
        f"(olculdu: 1,118 x 1,187 = 1,327 -> beta 4,57; birlikte olculen "
        f"nokta 4,167, literatur 4,18).")


def guc_yasasi_uydur(h, beta, *, p_araligi=(0.1, 3.0), n_p: int = 291) -> dict:
    """`β(h) = β_∞ − C·h^p` uydur (ızgarada `p`, `β_∞` ve `C` en küçük kare).

    En az üç nokta ister: iki noktayla `p` **veriden çıkmaz**, varsayılır ve
    varsayım yanlışsa sonuç çok kayar (bkz. `richardson_iki_nokta`).
    """
    h = np.asarray(h, dtype=np.float64).ravel()
    b = np.asarray(beta, dtype=np.float64).ravel()
    if h.shape != b.shape or h.size < 3:
        raise ValueError("h ve beta ayni uzunlukta ve en az 3 nokta olmali")
    if np.any(h <= 0.0) or not np.all(np.isfinite(b)):
        raise ValueError("h > 0 ve beta sonlu olmali")
    en_iyi = None
    for p in np.linspace(p_araligi[0], p_araligi[1], int(n_p)):
        X = np.column_stack([np.ones_like(h), -h ** p])
        coef, *_ = np.linalg.lstsq(X, b, rcond=None)
        art = b - X @ coef
        rms = float(np.sqrt(np.mean(art ** 2)))
        if en_iyi is None or rms < en_iyi["artik_rms"]:
            en_iyi = {"beta_sonsuz": float(coef[0]), "C": float(coef[1]),
                      "p": float(p), "artik_rms": rms}
    return en_iyi


def richardson_iki_nokta(h_kaba: float, beta_kaba: float,
                         h_ince: float, beta_ince: float, *, p: float) -> dict:
    """İki noktalı Richardson — **varsayılan `p` ile**; uyarı zorunlu.

    Ölçüldü (L1 kıyas sahnesi): `p` kontrollü deneyden alınan `0,33` ile
    `β_∞ = 5,11` çıkıyordu; gerçekte ölçülen `4,01`. **`%27` fazla.**
    Bu yüzden dönen sözlükte `uyari` alanı her zaman doludur.
    """
    if not (h_kaba > h_ince > 0.0):
        raise ValueError("h_kaba > h_ince > 0 olmali")
    if p <= 0.0 or not math.isfinite(p):
        raise ValueError("p pozitif ve sonlu olmali")
    r = h_kaba / h_ince
    pay = (beta_ince - 1.0) - (beta_kaba - 1.0)
    b_inf = (beta_ince - 1.0) + pay / (r ** p - 1.0)
    return {"beta_sonsuz": 1.0 + b_inf, "oran": r, "p": p,
            "uyari": "IKI NOKTA: p VARSAYILDI, olculmedi. p yanlissa sonuc "
                     "buyuk kayar (olculdu: p=0,33 varsayimi %27 fazla verdi)."}


def yeterli_mi(h_orani: float) -> dict:
    """`h_bağıl` doyma eşiğinin altında mı (ölçülen `0,75`)?"""
    if not (h_orani > 0.0 and math.isfinite(h_orani)):
        raise ValueError("h_orani pozitif ve sonlu olmali")
    yeter = h_orani <= DOYMA_H_ORANI
    return {"h_orani": float(h_orani), "esik": DOYMA_H_ORANI, "yeterli": yeter,
            "not": ("olculen doyma bolgesinde (uc kol %0,6 icinde)" if yeter
                    else "doyma esiginin USTUNDE: duzeltme gerekir")}
