"""Gözlemliler arası artık korelasyonu `R` — **ölçülür, varsayılmaz**.

## Niçin ayrı bir modül

ADR-0058 §4.3 kuralı kilitli: *"`R` ÖLÇÜLÜR, varsayılmaz. Kaynağı:
havuzun kendi vekil artıkları (`β` ve `M_ejekta` artıklarının örnek
korelasyonu, `θ`-gruplu CV ile)."* Kural vardı, **uygulaması yoktu**;
`grid_posterior_hetero` bir `R` istiyor ve provada `R = I` verilmişti.

Bunun bedeli ADR-0058 §3'te ölçüldü ve beklenenin tersi çıktı:

| `ρ(β, M_ejekta)` | `α_b` daralması |
|---|---|
| `0,00` | `0,372` |
| `0,80` | `0,708` |

`R = I` almak bilgiyi şişirmiyor, **yanlış yere dağıtıyor**: iki
gözlemlinin *farkı* korelasyon arttıkça keskinleşen bir birleşim olur ve
`α_b` tam o fark yönüne biner. Yani **`α_b`'nin çıkarılabilir olup
olmaması `R`'ye bağlı** — `R`'yi varsaymak, projenin ikinci parametresi
hakkındaki sonucu varsaymaktır.

## Küçültme neden korelasyonu sadece ölçekliyor

Kovaryans köşegene doğru küçültülür (`p_kalibrasyon_raporu.KUCULTME`):

    S' = (1 − λ) S + λ diag(S)

Köşegen değişmez: `(1−λ)S_ii + λS_ii = S_ii`. Dolayısıyla korelasyona
çevirince köşegen dışı terimler **tam olarak** `(1−λ)` ile çarpılır:

    R_ij = (1 − λ) r_ij   (i ≠ j),      R_ii = 1

Bu, `λ > 0` için `R`'yi pozitif tanımlı tutar (örnek korelasyon yarı
tanımlıyken bile) ve küçültmenin ne yaptığını tek satırda görünür kılar:
ölçülen korelasyonu `%30` geri çeker, işaretini değiştirmez.

## Kullanım

    R, tani = artik_korelasyonu(E)          # E: (n, k) gruplu CD artıkları
    R0, Rm = korelasyon_ikilisi(E)          # ADR-0058 §4.3 yan yana kolu
"""

from __future__ import annotations

import numpy as np

__all__ = ["KUCULTME", "artik_korelasyonu", "korelasyon_ikilisi"]

#: `scripts/p_kalibrasyon_raporu.KUCULTME` ile aynı. Burada yeniden
#: yazıldı çünkü bu modül betiğe bağımlı olmamalı; sınav ikisinin
#: eşitliğini doğrular.
KUCULTME = 0.3

#: Altında korelasyon okunmaz: az örnekle korelasyon kestirimi gürültüdür.
ASGARI_ORNEK = 12


def artik_korelasyonu(E, lam: float = KUCULTME) -> tuple[np.ndarray, dict]:
    """`(n, k)` gruplu çapraz doğrulama artıklarından küçültülmüş `R`.

    Dönen `R` **korelasyondur** (birim köşegen), kovaryans değil:
    `grid_posterior_hetero` varyansı `θ`'ya bağlı `D(θ)`'dan alır ve
    `S(θ) = D(θ)^½ R D(θ)^½` kurar. Buraya kovaryans verilirse varyans
    **iki kez** sayılır.

    `tani` sözlüğü ham (küçültülmemiş) korelasyonu da taşır ki
    küçültmenin etkisi raporlanabilsin.
    """
    E = np.atleast_2d(np.asarray(E, dtype=np.float64))
    if E.ndim != 2:
        raise ValueError(f"E (n, k) olmali, {E.shape} geldi")
    n, k = E.shape
    if not np.isfinite(E).all():
        raise ValueError("artiklarda sonlu olmayan deger var")
    if k < 2:
        raise ValueError(f"en az 2 gozlemli gerekir, {k} geldi")
    if n < ASGARI_ORNEK:
        raise ValueError(
            f"{n} ornekle korelasyon okunmaz (asgari {ASGARI_ORNEK}); "
            "az orneklemde korelasyon kestirimi gurultudur")
    if not (0.0 <= lam < 1.0):
        raise ValueError(f"lam [0, 1) araliginda olmali, {lam} geldi")

    S = np.cov(E, rowvar=False, ddof=1).reshape(k, k)
    sd = np.sqrt(np.diag(S))
    if not (sd > 0).all():
        raise ValueError("bir gozemlinin artik sacilmasi sifir -- "
                         "korelasyon tanimsiz")
    ham = S / np.outer(sd, sd)
    np.fill_diagonal(ham, 1.0)

    # Kucultme korelasyonda sadece kosegen disini (1-lam) ile olcekler;
    # turetmesi modul basligindaki aciklamada.
    R = (1.0 - lam) * ham
    np.fill_diagonal(R, 1.0)

    ozdeger = np.linalg.eigvalsh(R)
    if ozdeger.min() <= 0.0:
        raise ValueError(f"R pozitif tanimli degil (en kucuk ozdeger "
                         f"{ozdeger.min():.3e})")

    tani = {
        "n": int(n),
        "k": int(k),
        "lam": float(lam),
        "ham_korelasyon": ham.tolist(),
        "R": R.tolist(),
        "en_kucuk_ozdeger": float(ozdeger.min()),
        "kosul_sayisi": float(ozdeger.max() / ozdeger.min()),
        "artik_std": sd.tolist(),
    }
    if k == 2:
        tani["rho_ham"] = float(ham[0, 1])
        tani["rho_kuculmus"] = float(R[0, 1])
    return R, tani


def korelasyon_ikilisi(E, lam: float = KUCULTME) -> tuple[np.ndarray, np.ndarray]:
    """ADR-0058 §4.3'ün **yan yana** kolu: `(R_bagimsiz, R_olculen)`.

    Kural, `R` ölçülemezse posteriorun iki ayrı `ρ` ile koşulup ikisinin
    yan yana raporlanmasını istiyor: `0` ve ölçülen. `R` ölçülebiliyorsa
    esas olan ölçülendir; bu yardımcı yine de ikisini birden döndürür,
    çünkü ADR-0058 §3 `α_b` sonucunun `ρ`'ye bağlı olduğunu ölçtü ve
    farkın raporlanması okura `R`'nin ne kadar belirleyici olduğunu
    gösterir.
    """
    R, _ = artik_korelasyonu(E, lam)
    return np.eye(len(R)), R
