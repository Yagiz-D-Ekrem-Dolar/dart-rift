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
           "makul_mu", "KESME", "MODEL_EKSIKLIGI_KAYNAKLI",
           "model_eksikligi_kaynakli", "kod_kiyasi_olc", "uygunsuzluk_cok"]

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


# ---------------------------------------------------------------------------
# ADR-0051 (2026-09-19): KAYNAKLI model eksikligi.
#
# `MODEL_EKSIKLIGI` (yukarida) dort TAHMINDI ve hicbiri bizim kodumuzla
# olculmemisti. Asagidaki tablo her terimi KAYNAGIYLA tutar; `nan` = henuz
# olculmedi. `nan` bir terim secilirse HATA verilir -- olculmemis bir terimi
# sessizce sifir saymak, olculmemis bir kesinlik iddiasidir.
# Degerler `beta - 1` uzerinden BAGIL.
# ---------------------------------------------------------------------------
_NAN = float("nan")

MODEL_EKSIKLIGI_KAYNAKLI = {
    "cozunurluk_uzak": (0.004, "UA: Delta(3,5 m; 7 m), S_UA.json (KAYIT-067)"),
    "cozunurluk_yakin": (_NAN, "PROTOKOL-UY kosuyor (1569287_0/1)"),
    "gecis_ani": (_NAN, "PROTOKOL-UG kosuyor (1569287_2/3); W2'de 0,2 -> 1,0 s +%9-15"),
    "kod_kiyasi": (_NAN, "uretim t_gecis'inde W2/UG kolundan kod_kiyasi_olc ile; "
                         "0,2 s'de 0,16 (L1'e 0,82-0,87)"),
    "plato": (0.01, "W2 beta(t): 200 -> 600 s %1-3 geri cekme (KAYIT-067 §2b)"),
    # OLCULDU (2026-09-28, KAYIT-070): ayni theta, FARKLI sahne tohumu ->
    # blok dizilimi degisiyor. 15 theta cifti (U/V havuzu, iki tohum):
    # beta-1 bagil fark ortanca %4,6 -> sd = |fark|/sqrt(2) ~ %3,3.
    # GERCEK DART da tek bir gerceklemedir: bu terim, tek gozleme asiri
    # uymayi (overfit) engelleyen TABANDIR, atlanamaz.
    "gerceklem_beta": (0.033, "U/V 15 theta cifti, iki tohum (KAYIT-070)"),
    # Ayni olcum M_ejekta icin: bagil fark ortanca %20,9 -> sd ~ %15.
    "gerceklem_M_ejekta": (0.15, "U/V 15 theta cifti, iki tohum (KAYIT-070)"),
    "carpma_yeri": (0.10, "L12 Senel ve dig. 2025 MNRAS: yakin bloklar beta'yi "
                          "<= %7,6 degistiriyor -> beta-1'de ~%10 (beta ~3,2)"),
    "mermi_geometrisi": (0.15, "L9 Owen ve dig. 2022: kure mermi %10-20; UC KURE "
                               "mermiyle kalan terim OLCULMEDI (ust sinir)"),
    "hedef_sekli": (0.20, "L1: elipsoit/kure %15-21; ELIPSOIT sahnede kalan "
                          "terim OLCULMEDI (ust sinir)"),
    "carpma_acisi": (0.05, "L5, L13, L20; Daly ve dig. 2023: 17 +- 7 derece"),
}


def model_eksikligi_kaynakli(deger: float, secim) -> dict:
    """Seçilen **kaynaklı** terimlerden mutlak `σ_model` (`deger = β − 1`).

    `secim` terim adları listesi; boş olamaz. Ölçülmemiş (`nan`) bir terim
    seçilirse `ValueError` — protokol ya terimi ölçmeli ya da **açıkça**
    dışarıda bırakıp gerekçesini yazmalı.
    """
    secim = list(secim)
    if not secim:
        raise ValueError("en az bir terim secilmeli")
    bil = {}
    for ad in secim:
        if ad not in MODEL_EKSIKLIGI_KAYNAKLI:
            raise ValueError(f"bilinmeyen terim: {ad}")
        s, kaynak = MODEL_EKSIKLIGI_KAYNAKLI[ad]
        if not np.isfinite(s):
            raise ValueError(f"{ad} henuz OLCULMEDI ({kaynak})")
        bil[ad] = s
    return {"sigma": model_eksikligi_sigma(deger, bil), "terimler": bil}


def kod_kiyasi_olc(bizim, literatur) -> float:
    """Kodlar arası fark: `(β − 1)` bağıl farklarının karekök ortalaması."""
    b = np.asarray(bizim, dtype=np.float64).ravel() - 1.0
    L = np.asarray(literatur, dtype=np.float64).ravel() - 1.0
    if b.shape != L.shape or b.size == 0 or np.any(L <= 0.0):
        raise ValueError("bizim/literatur ayni uzunlukta, beta_L > 1 olmali")
    return float(np.sqrt(np.mean(((b - L) / L) ** 2)))


def uygunsuzluk_cok(modeller, gozlemler, sigmalar, *, ikinci: bool = False):
    """Çok çıktılı uygunsuzluk `I_M = max_k I_k` (Vernon ve diğ., L19).

    `modeller` `(N, k)`, `gozlemler` `(k,)`, `sigmalar` `(k,)` ya da `(N, k)`
    **toplam** sd (gözlem + vekil + model eksikliği). `ikinci=True` en büyük
    ikinci `I`'yı verir (tek bir çıktının vekil hatasına karşı sağlam).
    """
    m = np.atleast_2d(np.asarray(modeller, dtype=np.float64))
    z = np.asarray(gozlemler, dtype=np.float64).ravel()
    s = np.broadcast_to(np.asarray(sigmalar, dtype=np.float64), m.shape)
    if m.shape[1] != z.size:
        raise ValueError(f"modeller {m.shape}, {z.size} gozlem")
    if np.any(~np.isfinite(s)) or np.any(s <= 0.0):
        raise ValueError("sigmalar pozitif ve sonlu olmali")
    ii = np.abs(m - z[None, :]) / s
    if ikinci:
        if m.shape[1] < 2:
            raise ValueError("ikinci en buyuk icin en az 2 cikti gerekir")
        return np.sort(ii, axis=1)[:, -2]
    return ii.max(axis=1)
