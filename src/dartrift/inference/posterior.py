"""Posterior — vekil üzerinde **ızgara** ile.

## Neden ızgara, MCMC değil

Üç parametre. `60³ = 216 000` nokta bir saniyenin altında değerlenir ve
ızgara **deterministiktir** (ADR-0004): zincir yok, karışma yok,
tohum-duyarlı yakınsama yok. MCMC'nin kazancı yüksek boyutta ortaya
çıkar; burada bedeli var, kazancı yok.

> Parametre sayısı artarsa bu karar yeniden değerlendirilir — ızgara
> `d`'de üstel büyür.

## Olabilirlik

Gözlenebilirler bağımsız Gauss varsayılır:

```
−2 log L = Σ_k [ (g_k(θ) − d_k)² / (σ_k² + σ_vekil²) ]
```

`σ_vekil` **eklenir**: vekilin kendi hatası gözlem gürültüsünden büyükse
posterior yapay biçimde daralır. Bunu yok saymak, ölçülmemiş bir
kesinlik iddia etmektir.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .design import ParamSpace

__all__ = ["GridPosterior", "grid_posterior"]


@dataclass(frozen=True)
class GridPosterior:
    """Normalize edilmiş posterior + kenar özetleri."""

    space: ParamSpace
    grid_u: tuple            # her eksende (n,) birim kup dugumleri
    logp: np.ndarray         # (n,)*d normalize edilmemis log-posterior
    p: np.ndarray            # (n,)*d normalize edilmis
    mean_u: np.ndarray       # (d,) birim kupte posterior ortalama
    std_u: np.ndarray        # (d,) birim kupte posterior std
    hdi_u: np.ndarray        # (d,2) %68 esit-kuyruk araligi, birim kupte

    @property
    def mean(self) -> np.ndarray:
        """Doğal birimde posterior ortalama."""
        return self.space.from_unit(self.mean_u[None, :])[0]

    def marginal(self, j: int) -> np.ndarray:
        """`j`. eksenin kenar dağılımı."""
        eksen = tuple(k for k in range(self.space.ndim) if k != j)
        m = self.p.sum(axis=eksen)
        return m / m.sum()

    def hdi(self, j: int) -> np.ndarray:
        """`j`. eksenin `%68` aralığı, **doğal birimde**."""
        u = np.zeros((2, self.space.ndim))
        u[:, :] = self.mean_u[None, :]
        u[:, j] = self.hdi_u[j]
        return self.space.from_unit(u)[:, j]

    def contains(self, j: int, deger: float) -> bool:
        """`%68` aralığı verilen değeri içeriyor mu? (G4-C1)"""
        lo, hi = self.hdi(j)
        return bool(lo <= deger <= hi)

    @property
    def width_u(self) -> np.ndarray:
        """Birim küpte `%68` aralık genişliği — G4-C2'nin payı."""
        return self.hdi_u[:, 1] - self.hdi_u[:, 0]

    def pinned(self, j: int) -> bool:
        """`j`. eksende posterior **kenara çakılmış** mı?

        ## Neden bu tanı zorunlu

        Gerçek değer önsel aralığın **dışındaysa** posterior sınıra
        dayanır ve **çok dar** bir bant üretir — yani *"son derece
        bilgilendirici"* görünür. Oysa doğru okuma tam tersidir:
        **parametre aralığı yanlış seçilmiş**.

        Ölçüldü (`n_grid = 100`, tek gözlenebilir, `σ = 0,02`):

        | gerçek `u` | mod bini | kenarda mı | `%68` genişlik |
        |---|---|---|---|
        | 0,50 | 49 | hayır | 0,03955 |
        | 0,90 | 89 | hayır | 0,04059 |
        | 0,98 | 97 | hayır | 0,03545 |
        | **1,00** | **99** | **evet** | 0,02624 |
        | **1,50** | **99** | **evet** | **0,00687** |
        | **−0,30** | **0** | **evet** | **0,00000** |

        Genişliğin dışarı çıkıldıkça **daralması** sahte kesinliğin
        imzasıdır. Ayrım keskin ve **parametresiz**: mod en dış kutuda mı?

        > Bu, KAYIT-030'un hata sınıfıdır: çıktı makul görünür
        > (*"dar bant = iyi kurtarma"*), üreten mekanizma bozuktur.
        """
        m = self.marginal(j)
        return bool(int(np.argmax(m)) in (0, len(m) - 1))

    @property
    def pinned_any(self) -> bool:
        return any(self.pinned(j) for j in range(self.space.ndim))


def grid_posterior(space: ParamSpace, surrogates, data, sigma,
                   n_grid: int = 60) -> GridPosterior:
    """Izgara posterior.

    Parameters
    ----------
    surrogates
        Gözlenebilir başına bir `Surrogate` (ya da `predict(x)` sunan
        herhangi bir nesne).
    data
        Ölçülen gözlenebilirler, `surrogates` ile aynı sırada.
    sigma
        Gözlem gürültüsü (skaler ya da gözlenebilir başına).
    """
    surrogates = list(surrogates)
    data = np.asarray(data, dtype=np.float64).ravel()
    if len(surrogates) != len(data):
        raise ValueError(
            f"{len(surrogates)} vekil ama {len(data)} veri noktası")
    if len(surrogates) == 0:
        raise ValueError("en az bir gözlenebilir gerekir")
    sig = np.broadcast_to(np.asarray(sigma, dtype=np.float64).ravel(),
                          (len(data),)).astype(np.float64)
    if np.any(sig <= 0.0):
        raise ValueError("gözlem gürültüsü pozitif olmalı")
    if n_grid < 8:
        raise ValueError(f"n_grid >= 8 olmalı, {n_grid} geldi")

    eksen = np.linspace(0.0, 1.0, n_grid)
    izgara = np.meshgrid(*([eksen] * space.ndim), indexing="ij")
    u_flat = np.column_stack([g.ravel() for g in izgara])
    x_flat = space.from_unit(u_flat)

    ki2 = np.zeros(len(u_flat), dtype=np.float64)
    for s, d, sg in zip(surrogates, data, sig):
        tahmin = np.asarray(s.predict(x_flat), dtype=np.float64).ravel()
        # VEKIL HATASI GOZLEM GURULTUSUNE EKLENIR. Yok sayilirsa posterior
        # yapay bicimde daralir -- olculmemis bir kesinlik iddiasi olurdu.
        s_vekil = float(getattr(s, "sigma", 0.0))
        ki2 += (tahmin - d) ** 2 / (sg ** 2 + s_vekil ** 2)

    logp = -0.5 * ki2
    logp -= logp.max()
    p = np.exp(logp)
    p /= p.sum()
    sekil = (n_grid,) * space.ndim
    p = p.reshape(sekil)

    ort = np.empty(space.ndim)
    std = np.empty(space.ndim)
    hdi = np.empty((space.ndim, 2))
    for j in range(space.ndim):
        diger = tuple(k for k in range(space.ndim) if k != j)
        m = p.sum(axis=diger)
        m = m / m.sum()
        ort[j] = float(np.sum(m * eksen))
        std[j] = float(np.sqrt(max(np.sum(m * (eksen - ort[j]) ** 2), 0.0)))
        kum = np.cumsum(m)
        hdi[j, 0] = float(np.interp(0.16, kum, eksen))
        hdi[j, 1] = float(np.interp(0.84, kum, eksen))

    return GridPosterior(space=space, grid_u=tuple([eksen] * space.ndim),
                         logp=logp.reshape(sekil), p=p, mean_u=ort,
                         std_u=std, hdi_u=hdi)
