"""Parametre tanımlanabilirliği ve dejenerelik tanıları (ADR-0051).

## Neden

N ve P-v4 `α_b`'yi hiçbir gözlem vektörüyle çözemedi; literatür (L2, L11, L15)
**aynı β'yı birçok iç yapının** ürettiğini söylüyor. "Posterior çıktı" demek
yetmez: hangi parametrenin **veriden**, hangisinin **önselden** geldiği ayrıca
gösterilmeli. Üç bağımsız tanı:

1. **Posterior daralması** (Schad, Betancourt & Vasishth 2021, *Psychol.
   Methods* 26, 103): `c_j = 1 − Var_post / Var_önsel`. Birim küpte düzgün
   önselin varyansı `1/12`.
2. **Profil olabilirlik** (Raue ve diğ. 2009, *Bioinformatics* 25, 1923):
   `PL_j(u) = max_{diğerleri} log p`. Profil, en iyi değerinden her iki yönde
   `Δ = χ²₁(0,95)/2 = 1,92` düşmüyorsa parametre o yönde **pratik olarak
   tanımlanamaz**. Düz profil = dejenerelik.
3. **Fisher yönleri** (yerel): `F = Jᵀ Σ⁻¹ J`. `rank(F) ≤ min(k, d)` —
   `k` gözlenebilirle en çok `k` yön öğrenilir. **Yalnız β ile (k = 1) üç
   parametreden en çok bir birleşim çözülür**; bu bir aritmetik gerçektir,
   simülasyon kusuru değil.

## Eşikler (ölçümden önce)

| sabit | değer | anlamı |
|---|---|---|
| `DARALMA_OGRENILDI` | 0,5 | posterior sd ≤ önsel sd'nin `%71`'i |
| `DARALMA_ZAYIF` | 0,1 | altı: **önsel baskın** |
| `PROFIL_ESIGI` | 1,92 | `χ²₁(0,95)/2` |
| `FISHER_ESIGI` | 36 | yön boyunca yaklaşık posterior sd `< önsel sd / 2` |

(Önsel hassasiyeti birim küpte `12`.)
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np

__all__ = ["posterior_daralma", "profil_logp", "profil_tanisi",
           "kovaryans_yonleri", "yerel_jakobyen", "fisher_yonleri",
           "tanimlanabilirlik_ozeti", "ONSEL_VARYANS", "DARALMA_OGRENILDI",
           "DARALMA_ZAYIF", "PROFIL_ESIGI", "FISHER_ESIGI"]

ONSEL_VARYANS = 1.0 / 12.0
DARALMA_OGRENILDI = 0.5
DARALMA_ZAYIF = 0.1
PROFIL_ESIGI = 1.92
FISHER_ESIGI = 36.0


def _daralma_sinifi(c: float) -> str:
    if c >= DARALMA_OGRENILDI:
        return "OGRENILDI"
    if c >= DARALMA_ZAYIF:
        return "ZAYIF"
    return "ONSEL BASKIN"


def posterior_daralma(post) -> list[dict]:
    """Eksen başına `c = 1 − Var_post / Var_önsel` ve sınıfı."""
    out = []
    for j, ad in enumerate(post.space.names):
        v = float(post.std_u[j]) ** 2
        c = 1.0 - v / ONSEL_VARYANS
        out.append({"ad": ad, "daralma": c, "sd_oran": float(np.sqrt(v / ONSEL_VARYANS)),
                    "sinif": _daralma_sinifi(c)})
    return out


def profil_logp(post, j: int) -> np.ndarray:
    """`j`. eksenin profil log-posterioru (diğer eksenlerde **en büyük**)."""
    lp = np.asarray(post.logp, dtype=np.float64)
    diger = tuple(k for k in range(lp.ndim) if k != j)
    return lp.max(axis=diger) if diger else lp.copy()


def profil_tanisi(post, j: int, esik: float = PROFIL_ESIGI) -> dict:
    """Profilin en iyi değerden **iki yönde** `esik` kadar düşüp düşmediği.

    - `TANIMLANABILIR`: iki yönde de düşüyor (güven aralığı iki uçta kapalı)
    - `TEK YONLU`: yalnız bir yönde (ör. yalnız üst sınır)
    - `TANIMLANAMAZ`: hiçbir yönde (düz profil — dejenerelik)
    """
    pl = profil_logp(post, j)
    k = int(np.argmax(pl))
    tepe = float(pl[k])
    alt = bool(np.any(pl[:k] <= tepe - esik)) if k > 0 else False
    ust = bool(np.any(pl[k + 1:] <= tepe - esik)) if k < len(pl) - 1 else False
    sinif = ("TANIMLANABILIR" if (alt and ust) else
             "TEK YONLU" if (alt or ust) else "TANIMLANAMAZ")
    eksen = np.asarray(post.grid_u[j], dtype=np.float64)
    icerde = pl >= tepe - esik
    return {"ad": post.space.names[j], "sinif": sinif, "alt_kapali": alt,
            "ust_kapali": ust, "tepe_u": float(eksen[k]),
            "aralik_u": [float(eksen[icerde].min()), float(eksen[icerde].max())],
            "esik": float(esik)}


def kovaryans_yonleri(post) -> dict:
    """Birim küpte posterior kovaryansı ve **öz yönleri**.

    En küçük öz değerin yönü, verinin **en iyi** kısıtladığı parametre
    **birleşimidir** (ör. `log Y₀ + 0,6 f`). Öz sd'ler önsel sd'ye
    (`√(1/12)`) oranlanır.
    """
    p = np.asarray(post.p, dtype=np.float64)
    d = p.ndim
    eksenler = [np.asarray(g, dtype=np.float64) for g in post.grid_u]
    ort = np.array([float(np.sum(post.marginal(j) * eksenler[j])) for j in range(d)])
    C = np.empty((d, d))
    for a in range(d):
        for b in range(a, d):
            diger = tuple(k for k in range(d) if k not in (a, b))
            m2 = p.sum(axis=diger) if diger else p
            if a == b:
                m1 = post.marginal(a)
                C[a, a] = float(np.sum(m1 * (eksenler[a] - ort[a]) ** 2))
                continue
            ua = (eksenler[a] - ort[a])[:, None]
            ub = (eksenler[b] - ort[b])[None, :]
            C[a, b] = C[b, a] = float(np.sum(m2 * ua * ub))
    w, V = np.linalg.eigh(0.5 * (C + C.T))
    w = np.maximum(w, 0.0)
    sd_oran = np.sqrt(w / ONSEL_VARYANS)
    return {"kovaryans": C.tolist(), "ortalama_u": ort.tolist(),
            "oz_sd_oran": sd_oran.tolist(), "oz_yonler": V.T.tolist(),
            "en_iyi_yon": V[:, 0].tolist(), "en_iyi_sd_oran": float(sd_oran[0])}


def yerel_jakobyen(f: Callable, u0, adim: float = 1e-3) -> np.ndarray:
    """Birim küpte merkezi farkla `J = ∂f/∂u`, şekil `(k, d)`.

    Sınıra yakın noktada tek yönlü farka düşer (küp dışına çıkılmaz).
    """
    u0 = np.asarray(u0, dtype=np.float64).ravel()
    f0 = np.atleast_1d(np.asarray(f(u0), dtype=np.float64))
    J = np.empty((f0.size, u0.size))
    for j in range(u0.size):
        a = u0.copy()
        b = u0.copy()
        a[j] = max(u0[j] - adim, 0.0)
        b[j] = min(u0[j] + adim, 1.0)
        if b[j] <= a[j]:
            raise ValueError("adim sifir aralik verdi")
        J[:, j] = (np.atleast_1d(f(b)) - np.atleast_1d(f(a))) / (b[j] - a[j])
    return J


def fisher_yonleri(J, kov, esik: float = FISHER_ESIGI) -> dict:
    """`F = Jᵀ Σ⁻¹ J` öz ayrışımı ve **öğrenilebilir yön** sayısı.

    Yaklaşık posterior sd (Gauss önsel, hassasiyet 12): `1/√(λ + 12)`.
    `λ > esik` olan yönler "öğrenilir". Üst sınır `min(k, d)` ayrıca yazılır.
    """
    J = np.atleast_2d(np.asarray(J, dtype=np.float64))
    kov = np.atleast_2d(np.asarray(kov, dtype=np.float64))
    k, d = J.shape
    if kov.shape != (k, k):
        raise ValueError(f"kov {kov.shape}, ({k}, {k}) bekleniyordu")
    L = np.linalg.cholesky(0.5 * (kov + kov.T))
    A = np.linalg.solve(L, J)
    F = A.T @ A
    lam, V = np.linalg.eigh(0.5 * (F + F.T))
    lam = np.maximum(lam[::-1], 0.0)
    V = V[:, ::-1]
    sd = 1.0 / np.sqrt(lam + 1.0 / ONSEL_VARYANS)
    return {"ozdegerler": lam.tolist(), "yonler": V.T.tolist(),
            "yaklasik_sd_oran": (sd / np.sqrt(ONSEL_VARYANS)).tolist(),
            "ogrenilen_yon_sayisi": int(np.count_nonzero(lam > esik)),
            "ust_sinir": int(min(k, d)), "esik": float(esik)}


def tanimlanabilirlik_ozeti(post) -> dict:
    """Daralma + profil + kovaryans yönleri — eksen başına tek tablo."""
    dar = posterior_daralma(post)
    prof = [profil_tanisi(post, j) for j in range(post.space.ndim)]
    satirlar = []
    for a, b in zip(dar, prof, strict=True):
        # Iki tani ayri seyler olcer: daralma "ne kadar", profil "iki uc kapali mi".
        if a["sinif"] == "OGRENILDI" and b["sinif"] == "TANIMLANABILIR":
            genel = "TANIMLANABILIR"
        elif a["sinif"] == "ONSEL BASKIN" and b["sinif"] == "TANIMLANAMAZ":
            genel = "TANIMLANAMAZ"
        else:
            genel = "KISMEN"
        satirlar.append({"ad": a["ad"], "daralma": a["daralma"],
                         "daralma_sinifi": a["sinif"], "profil": b["sinif"],
                         "genel": genel})
    return {"eksenler": satirlar, "yonler": kovaryans_yonleri(post)}
