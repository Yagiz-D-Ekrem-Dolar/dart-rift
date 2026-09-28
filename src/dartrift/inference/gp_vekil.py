"""Gauss süreci vekili — ikinci derece polinom yetmezse (Protokol P, §4c).

## Neden şimdi

`surrogate.py` polinomu seçti ve gerekçesi hâlâ geçerli (az veri,
determinizm, bağımlılık yok). Ama G1 ölçtü: `Y₀` → krater derinliği bir
**eşik** (plato + dik düşüş); ikinci derece `R² = 0,928`, sigmoid
gerekti (`vekil_posterior.py`). Üç eksende sigmoid biçimi elle
seçilemez. GP biçim varsaymaz.

Bu modül **kararı değiştirmez**: Protokol P'de polinom birincil yoldur;
GP yalnız §4c'deki kilitli kuralla devreye girer.

## Determinizm (ADR-0004)

Hiperparametreler log-marjinal olabilirliği **deterministik** bir
çok-başlangıçlı örüntü aramasıyla (tohum yok, `scipy` yok) maksimize
edilir. Aynı veri → bit-aynı hiperparametre.

## Model

Birim küpte ARD kare-üstel çekirdek, sabit ortalama (standartlaştırılmış
`y`'de sıfır), gerçekleme gürültüsü `σn²` çekirdek köşegeninde:

    k(u, u') = s² exp(−½ Σ_j (u_j − u'_j)² / ℓ_j²) + σn² δ

Yeni bir **gerçekleme** için öngörü varyansı `var_gizli + σn²`'dir:
gerçek Dimorphos da tek bir gerçeklemedir.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .design import ParamSpace

__all__ = ["GpVekil", "gp_uydur", "gp_grup_loo", "gp_varyans_kalibre"]

#: Log-uzay sınırları (standartlaştırılmış `y`).
LOG_SINIR = {"s2": (np.log(1e-3), np.log(1e2)),
             "l": (np.log(0.05), np.log(10.0)),
             "n2": (np.log(1e-6), np.log(1.0))}


def _cekirdek(U1, U2, s2, ell):
    d = (U1[:, None, :] - U2[None, :, :]) / ell[None, None, :]
    return s2 * np.exp(-0.5 * np.sum(d * d, axis=-1))


def _nlml(logp, U, y):
    """Negatif log-marjinal olabilirlik (sabit terim hariç)."""
    s2, ell, n2 = np.exp(logp[0]), np.exp(logp[1:-1]), np.exp(logp[-1])
    K = _cekirdek(U, U, s2, ell) + (n2 + 1e-10) * np.eye(len(U))
    try:
        L = np.linalg.cholesky(K)
    except np.linalg.LinAlgError:
        return np.inf
    a = np.linalg.solve(L.T, np.linalg.solve(L, y))
    return float(0.5 * y @ a + np.sum(np.log(np.diag(L))))


def _sinirla(logp, d):
    lo = np.array([LOG_SINIR["s2"][0]] + [LOG_SINIR["l"][0]] * d + [LOG_SINIR["n2"][0]])
    hi = np.array([LOG_SINIR["s2"][1]] + [LOG_SINIR["l"][1]] * d + [LOG_SINIR["n2"][1]])
    return np.clip(logp, lo, hi)


def _oruntu_arama(logp, U, y, adim0=1.0, en_kucuk=1e-3, en_cok=400):
    d = U.shape[1]
    p = _sinirla(np.asarray(logp, float), d)
    f = _nlml(p, U, y)
    adim = adim0
    for _ in range(en_cok):
        gelisti = False
        for j in range(len(p)):
            for isaret in (1.0, -1.0):
                q = p.copy()
                q[j] += isaret * adim
                q = _sinirla(q, d)
                fq = _nlml(q, U, y)
                if fq < f - 1e-12:
                    p, f, gelisti = q, fq, True
        if not gelisti:
            adim *= 0.5
            if adim < en_kucuk:
                break
    return p, f


@dataclass(frozen=True)
class GpVekil:
    space: ParamSpace
    U: np.ndarray
    y_ort: float
    y_olcek: float
    logp: np.ndarray
    alfa: np.ndarray
    L: np.ndarray
    nlml: float
    #: Öngörü varyansı çarpanı (Bachoc 2013 çapraz doğrulama ölçeği;
    #: `gp_varyans_kalibre`). `1,0` → eski davranış, bit-aynı.
    varyans_carpani: float = 1.0

    @property
    def s2(self) -> float:
        return float(np.exp(self.logp[0]))

    @property
    def ell(self) -> np.ndarray:
        return np.exp(self.logp[1:-1])

    @property
    def n2(self) -> float:
        return float(np.exp(self.logp[-1]))

    def predict_u(self, Uy, *, yeni_gerceklem: bool = True, parca: int = 20000):
        """Birim küpte `(ortalama, varyans)` — doğal `y` biriminde."""
        Uy = np.atleast_2d(np.asarray(Uy, float))
        mu = np.empty(len(Uy))
        var = np.empty(len(Uy))
        for b in range(0, len(Uy), parca):
            Ks = _cekirdek(Uy[b:b + parca], self.U, self.s2, self.ell)
            mu[b:b + parca] = Ks @ self.alfa
            v = np.linalg.solve(self.L, Ks.T)
            var[b:b + parca] = np.maximum(self.s2 - np.sum(v * v, axis=0), 0.0)
        if yeni_gerceklem:
            var = var + self.n2
        if self.varyans_carpani != 1.0:
            var = var * self.varyans_carpani
        return self.y_ort + self.y_olcek * mu, (self.y_olcek ** 2) * var

    def predict(self, x):
        return self.predict_u(self.space.to_unit(x))[0]


def gp_uydur(space: ParamSpace, x, y, *, baslangic=None) -> GpVekil:
    """Hiperparametreler deterministik çok-başlangıçlı aramayla.

    `baslangic` verilirse (ör. tam veride bulunmuş `logp`) yalnız oradan
    yerel arama yapılır — kapalı döngünün 24 katında ucuz yeniden uydurma.
    """
    x = np.atleast_2d(np.asarray(x, float))
    y = np.asarray(y, float).ravel()
    if len(x) != len(y) or not np.all(np.isfinite(y)):
        raise ValueError("x/y uzunlukları farklı ya da y sonlu değil")
    U = space.to_unit(x)
    ort = float(y.mean())
    olcek = float(y.std()) or 1.0
    ys = (y - ort) / olcek
    d = space.ndim
    if baslangic is not None:
        p, f = _oruntu_arama(baslangic, U, ys, adim0=0.5)
    else:
        en_iyi = (None, np.inf)
        for l0 in (0.2, 0.6, 2.0):
            for n0 in (1e-3, 3e-2, 0.3):
                p0 = np.array([0.0] + [np.log(l0)] * d + [np.log(n0)])
                p, f = _oruntu_arama(p0, U, ys)
                if f < en_iyi[1]:
                    en_iyi = (p, f)
        p, f = en_iyi
    s2, ell, n2 = np.exp(p[0]), np.exp(p[1:-1]), np.exp(p[-1])
    K = _cekirdek(U, U, s2, ell) + (n2 + 1e-10) * np.eye(len(U))
    L = np.linalg.cholesky(K)
    alfa = np.linalg.solve(L.T, np.linalg.solve(L, ys))
    return GpVekil(space=space, U=U, y_ort=ort, y_olcek=olcek, logp=p,
                   alfa=alfa, L=L, nlml=float(f))


def gp_grup_loo(v: GpVekil, y, gruplar) -> tuple[np.ndarray, np.ndarray]:
    """Bırak-bir-grup artıkları ve öngörü varyansları (doğal birimde).

    Kapalı form (Rasmussen & Williams 2006, §5.4.2'nin grup genellemesi):
    `e_G = (K⁻¹_GG)⁻¹ (K⁻¹ y)_G`, `Cov(e_G) = (K⁻¹_GG)⁻¹`. Hiperparametreler
    sabit tutulur.
    """
    y = np.asarray(y, float).ravel()
    ys = (y - v.y_ort) / v.y_olcek
    Kinv = np.linalg.solve(v.L.T, np.linalg.solve(v.L, np.eye(len(ys))))
    a = Kinv @ ys
    gruplar = np.asarray(gruplar).ravel()
    e = np.empty(len(ys))
    s2 = np.empty(len(ys))
    for g in np.unique(gruplar):
        k = np.flatnonzero(gruplar == g)
        B = np.linalg.inv(Kinv[np.ix_(k, k)])
        e[k] = B @ a[k]
        s2[k] = np.diag(B)
    return v.y_olcek * e, (v.y_olcek ** 2) * s2


def gp_varyans_kalibre(v: GpVekil, y, gruplar, *,
                       yalniz_buyut: bool = True) -> tuple[GpVekil, dict]:
    """Öngörü varyansını **bırak-bir-grup** artıklarıyla kalibre et (ADR-0051).

    ## Neden

    P-v4b GP dış doğrulamada **AŞIRI GÜVENLİ** çıktı (kapsama68 `0,34–0,44`).
    Hiperparametreler en çok olabilirlikle (ML) seçiliyor; çekirdek yanlış
    belirlenmişse ML varyansı **küçük** tahmin eder. Bachoc (2013, *CSDA* 66,
    55) yanlış belirlenmiş modelde çapraz doğrulamanın (CV) varyans ölçeğini
    ML'den iyi kestirdiğini gösterdi:

        k = (1/N) Σ_G  e_Gᵀ C_G⁻¹ e_G

    `e_G` grubun bırak-dışarı artığı, `C_G` onun öngörü kovaryansı. Kalibre
    bir GP'de `E[k] = 1`. Ortalama değişmez (çekirdeğin tamamı `k` ile
    ölçeklenince `K⁻¹y` ile `k(x, X)` birbirini götürür), yalnız varyans `k`
    ile çarpılır.

    Kapalı form: `C_G = (K⁻¹_GG)⁻¹`, `e_G = C_G (K⁻¹y)_G` ⇒
    `e_Gᵀ C_G⁻¹ e_G = (K⁻¹y)_Gᵀ C_G (K⁻¹y)_G`.

    `yalniz_buyut=True` (varsayılan): `k < 1` ise varyans **küçültülmez** —
    az noktayla ölçülen bir ölçekle posterioru daraltmak, kanıtlanmamış
    kesinlik iddiasıdır.
    """
    y = np.asarray(y, float).ravel()
    ys = (y - v.y_ort) / v.y_olcek
    Kinv = np.linalg.solve(v.L.T, np.linalg.solve(v.L, np.eye(len(ys))))
    a = Kinv @ ys
    gruplar = np.asarray(gruplar).ravel()
    if len(gruplar) != len(ys):
        raise ValueError("gruplar ile y ayni uzunlukta olmali")
    q = 0.0
    z = np.empty(len(ys))
    for g in np.unique(gruplar):
        k_ = np.flatnonzero(gruplar == g)
        C = np.linalg.inv(Kinv[np.ix_(k_, k_)])
        q += float(a[k_] @ C @ a[k_])
        z[k_] = (C @ a[k_]) / np.sqrt(np.diag(C))
    k = q / len(ys)
    if not np.isfinite(k) or k <= 0.0:
        raise ValueError(f"CV varyans olcegi gecersiz: {k}")
    # ML varyansi zaten `varyans_carpani`yla carpilmis olabilir; olcek HAM
    # cekirdege gore olculdu -> dogrudan yazilir, carpilmaz.
    kullan = max(k, 1.0) if yalniz_buyut else k
    return replace(v, varyans_carpani=float(kullan)), {
        "k_cv": float(k), "k_kullanilan": float(kullan), "n": int(len(ys)),
        "grup_sayisi": int(len(np.unique(gruplar))),
        "z_ortalama": float(z.mean()), "z_kare_ortalama": float(np.mean(z * z)),
        "yalniz_buyut": bool(yalniz_buyut)}
