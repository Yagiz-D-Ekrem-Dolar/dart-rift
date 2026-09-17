"""Tarih eşleme (*history matching*) ve **model eksikliği** terimi (ADR-0050).

## Neden

Protokol U/V kararı `|z| ≤ 2` ile verildi; paydada yalnız gözlem belirsizliği
(ve kütle kaldıracı) vardı. Literatürdeki standart yöntem (Vernon, Goldstein &
Bower, *Stat. Sci.* 29(1); `docs/LITERATUR-DART-SIMULASYONLARI.md` L19) **model
eksikliğini** (model discrepancy) açıkça paydaya koyar:

    I(θ) = |E[f(θ)] − z| / √( Var_vekil + σ²_gözlem + σ²_model )

ve `I < 3` (Pukelsheim 3σ) eşiğiyle "makul" bölgeyi daraltır.

> **Geriye dönük DEĞİL.** U ve V'nin kilitli yargısı olduğu gibi kalır
> (kural koşudan önce yazılmıştı). Bu modül **yeni** protokoller içindir ve
> her yeni protokol hangi eksiklik terimlerini kullandığını koşudan önce
> yazmak zorundadır.

## Model eksikliği nereden geliyor

Ölçülmüş/yayımlanmış sistematikler (bağıl, `β − 1` üzerinden):

- **mermi geometrisi** (küre yerine gerçek uzay aracı), bağıl `σ = 0,15`:
  Owen ve diğ. 2022 — küre `β`'yı zayıf hedefte `%10–20` fazla veriyor (L9).
- **çözünürlük**, `0,15`: Raducan & Jutzi 2022 — düşük çözünürlük hızlı
  ejektayı `~%15` fazla veriyor (L1); bizde kaba → orta `−%13`.
- **hedef şekli** (küre yerine elipsoit), `0,20`: L1 — elipsoit `β` küreden
  `%15–21` yüksek.
- **çarpma açısı** (`~17°`), `0,05`: L5, L13, L20.

Hepsi bağımsız varsayılıp **karelerin toplamı** alınır. Bu bir tahmindir;
protokol başka değer kilitleyebilir, ama boş bırakamaz.
"""
from __future__ import annotations

import numpy as np

__all__ = ["MODEL_EKSIKLIGI", "model_eksikligi_sigma", "uygunsuzluk",
           "makul_mu", "KESME"]

#: Pukelsheim 3σ kuralı — tek çıktılı uygunsuzluk eşiği (L19).
KESME = 3.0

#: Bağıl model eksikliği bileşenleri (`β − 1` üzerinden).
MODEL_EKSIKLIGI = {
    "mermi_geometrisi": 0.15,
    "cozunurluk": 0.15,
    "hedef_sekli": 0.20,
    "carpma_acisi": 0.05,
}


def model_eksikligi_sigma(deger: float, bilesenler=None) -> float:
    """Mutlak model eksikliği `σ_model` — `deger` üzerinden bağıl bileşenler.

    `deger` olarak **`β − 1`** verilmelidir (ejekta katkısı); `β`'nın kendisi
    verilirse sistematikler yapay olarak büyür (`β = 1` bile `0,3` σ alırdı).
    """
    b = dict(MODEL_EKSIKLIGI if bilesenler is None else bilesenler)
    if not b:
        return 0.0
    for ad, s in b.items():
        if not np.isfinite(s) or s < 0.0:
            raise ValueError(f"{ad}: bagil sigma >= 0 ve sonlu olmali, {s}")
    return float(abs(deger) * np.sqrt(sum(s * s for s in b.values())))


def uygunsuzluk(model, gozlem, *, sigma_gozlem: float,
                var_vekil: float = 0.0, sigma_model: float = 0.0):
    """`I = |model − gözlem| / √(Var_vekil + σ²_gözlem + σ²_model)`.

    `model` dizi olabilir; `I` aynı şekilde döner.
    """
    if sigma_gozlem <= 0.0:
        raise ValueError(f"sigma_gozlem pozitif olmali, {sigma_gozlem} geldi")
    if var_vekil < 0.0 or sigma_model < 0.0:
        raise ValueError("var_vekil ve sigma_model negatif olamaz")
    payda = np.sqrt(float(var_vekil) + float(sigma_gozlem) ** 2
                    + float(sigma_model) ** 2)
    return np.abs(np.asarray(model, dtype=np.float64) - float(gozlem)) / payda


def makul_mu(model, gozlem, *, sigma_gozlem: float, var_vekil: float = 0.0,
             sigma_model: float = 0.0, kesme: float = KESME) -> dict:
    """Tarih eşleme kararı: `I < kesme` olan noktalar **elenmemiş**tir.

    Döner: `I` dizisi, `makul` maskesi, `en_kucuk_I` ve eşik. "Makul" demek
    **doğru** demek değildir; yalnız "bu gözlemle çelişmiyor" demektir.
    """
    ii = uygunsuzluk(model, gozlem, sigma_gozlem=sigma_gozlem,
                     var_vekil=var_vekil, sigma_model=sigma_model)
    ii = np.atleast_1d(ii)
    makul = ii < float(kesme)
    return {
        "I": [float(t) for t in ii],
        "makul": [bool(t) for t in makul],
        "en_kucuk_I": float(np.min(ii)) if ii.size else float("nan"),
        "n_makul": int(np.count_nonzero(makul)),
        "kesme": float(kesme),
        "payda": {"sigma_gozlem": float(sigma_gozlem),
                  "var_vekil": float(var_vekil),
                  "sigma_model": float(sigma_model)},
    }
