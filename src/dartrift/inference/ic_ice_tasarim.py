"""İç içe (nested) ince tasarım — ADR-0059 §3.2'nin **maximin** alt kümesi.

Çok doğruluklu vekil (`cok_dogruluk`, Kennedy–O'Hagan AR(1)) ince
noktaların kaba noktaların **alt kümesi** olmasını ister: iç içe
tasarımda `δ` özyinelemeli kestirimi **kesin**, değilse yaklaşık.

Bu modül `n` kaba noktadan `k` tanesini seçer. İki şart:

1. **Deterministik ve tohumsuz.** Aynı tasarım → bit-aynı seçim.
   Rastgelelik yok; beraberlik en küçük indeks lehine bozulur.
2. **Veriye bakmaz.** Seçim yalnız `θ` konumlarına bakar, hiçbir `y`
   değerine değil. Böylece havuz okunmadan **önce** koşabilir ve
   ADR-0059'un `CD` kapısı seçim etkisinden arınmış olur.

Ölçüt **maximin**: seçilen kümedeki en küçük ikili uzaklığı büyütmek.
Tam çözüm NP-zor; standart **açgözlü en uzak nokta** yaklaşımı
kullanılıyor (Kennard–Stone / farthest-point sampling) ve bu *bir
yaklaşımdır*, eniyi değil — seçimi savunulabilir kılan onun **önceden
ve kurala göre** yapılmış olmasıdır, eniyi olması değil.

Uzaklık **birim küpte** (`ParamSpace.to_unit`) ölçülür: `Y₀` beş
mertebe, `α_b` `0,30` genişlikte; doğal birimde Öklid uzaklığı
`Y₀`'nın egemenliğine girerdi.
"""
from __future__ import annotations

import numpy as np

__all__ = ["maximin_alt_kume", "ic_ice_mi", "ayrim_raporu"]


def maximin_alt_kume(u, k: int) -> np.ndarray:
    """`u` (`n×d`, birim küp) içinden `k` noktanın indeksleri, artan sırada.

    Açgözlü: ilk nokta **merkeze en yakın** olan (beraberlikte en küçük
    indeks), sonra her adımda seçilmişlere olan en küçük uzaklığı en
    büyük olan nokta eklenir.

    İlk noktanın merkezden seçilmesi bilinçli: köşeden başlamak zincirin
    kenarlar boyunca ilerlemesine ve ortanın boş kalmasına yol açıyor.
    """
    u = np.asarray(u, dtype=np.float64)
    if u.ndim != 2:
        raise ValueError(f"u (n, d) olmali, {u.shape} geldi")
    n = u.shape[0]
    if not (1 <= k <= n):
        raise ValueError(f"1 <= k <= n olmali (k={k}, n={n})")
    if np.any(~np.isfinite(u)):
        raise ValueError("u sonlu olmali")

    merkez = u.mean(axis=0)
    # `argmin` beraberlikte ZATEN en kucuk indeksi verir -> deterministik.
    ilk = int(np.argmin(((u - merkez) ** 2).sum(axis=1)))
    secili = [ilk]
    # `en_yakin[i]` = i'nin secili kumeye uzakligi (kare).
    en_yakin = ((u - u[ilk]) ** 2).sum(axis=1)
    for _ in range(k - 1):
        en_yakin[secili] = -1.0          # secilmis nokta yeniden secilmesin
        yeni = int(np.argmax(en_yakin))
        secili.append(yeni)
        d = ((u - u[yeni]) ** 2).sum(axis=1)
        en_yakin = np.minimum(en_yakin, d)
    return np.sort(np.asarray(secili, dtype=np.int64))


def ic_ice_mi(ince, kaba, *, tol: float = 1e-12) -> bool:
    """İnce tasarımın her noktası kaba tasarımda **var mı** (ADR-0059 kapı 1).

    Kapı sınavı: yalnız indeksle değil, **değerle** doğrular. İnce koşu
    yanlış `θ` ile gönderilmişse indeks listesi yine de doğru görünür.
    """
    a = np.atleast_2d(np.asarray(ince, dtype=np.float64))
    b = np.atleast_2d(np.asarray(kaba, dtype=np.float64))
    if a.shape[1] != b.shape[1]:
        raise ValueError(f"boyutlar uyusmuyor: {a.shape} vs {b.shape}")
    for satir in a:
        if not np.any(np.all(np.isclose(b, satir, rtol=0.0, atol=tol),
                             axis=1)):
            return False
    return True


def ayrim_raporu(u, indeks) -> dict:
    """Seçimin kapsama niteliği — rapora **ölçülmüş** sayı olarak girer.

    `min_ikili`: seçilenler arasındaki en küçük uzaklık (büyük olması iyi).
    `en_uzak_ortulmemis`: seçilmeyen bir noktanın seçilenlere olan en
    büyük uzaklığı (küçük olması iyi; uzayın boş bölgesi kalmadı demek).
    `rastgele_ortalama_min_ikili`: aynı `k` için rastgele alt kümelerin
    ortalama `min_ikili`'si — maximin'in gerçekten iyileştirip
    iyileştirmediğini gösteren **kıyas**. Tohum sabit (`0`), yalnız bu
    kıyas için kullanılır, seçimi etkilemez.
    """
    u = np.asarray(u, dtype=np.float64)
    idx = np.asarray(indeks, dtype=np.int64)
    if idx.size < 2:
        raise ValueError("rapor icin en az 2 nokta gerekli")
    s = u[idx]
    d2 = ((s[:, None, :] - s[None, :, :]) ** 2).sum(axis=-1)
    np.fill_diagonal(d2, np.inf)
    min_ikili = float(np.sqrt(d2.min()))

    disarida = np.setdiff1d(np.arange(u.shape[0]), idx)
    if disarida.size:
        dd = ((u[disarida][:, None, :] - s[None, :, :]) ** 2).sum(axis=-1)
        en_uzak = float(np.sqrt(dd.min(axis=1).max()))
    else:
        en_uzak = 0.0

    g = np.random.default_rng(0)
    orns = []
    for _ in range(200):
        r = g.choice(u.shape[0], size=idx.size, replace=False)
        sr = u[r]
        dr = ((sr[:, None, :] - sr[None, :, :]) ** 2).sum(axis=-1)
        np.fill_diagonal(dr, np.inf)
        orns.append(np.sqrt(dr.min()))
    return {
        "k": int(idx.size),
        "n": int(u.shape[0]),
        "min_ikili": min_ikili,
        "en_uzak_ortulmemis": en_uzak,
        "rastgele_ortalama_min_ikili": float(np.mean(orns)),
    }
