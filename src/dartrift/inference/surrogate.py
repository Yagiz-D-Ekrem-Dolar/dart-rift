"""Vekil model (emülatör) — pahalı ileri modelin ucuz yaklaşımı.

## Neden vekil

Posterior binlerce ileri değerlendirme ister. Her biri bir GPU
benzetimiyse bu imkânsızdır. Onlarca koşuyla bir vekil kurulur ve
posterior **vekil üzerinde** hesaplanır.

## Neden ikinci derece polinom (Gauss süreci değil)

| ölçüt | polinom | GP |
|---|---|---|
| az veriyle (`~20–30` nokta) | **çalışır** | çekirdek parametreleri belirsiz kalır |
| deterministik | **evet** | optimizasyona bağlı |
| belirsizlik kestirimi | artıklardan + LOO | doğal ama hiperparametreye duyarlı |
| dış bağımlılık | **yok** | `scipy`/`sklearn` |

ADR-0004 (determinizm) ve TRUBA'nın kurulum kısıtı (`/arf`'a pip yok)
birlikte polinomu işaret ediyor. Model **yetmezse** bu bir ADR ile
değiştirilir — vekilin yeterliliği ölçülür, varsayılmaz.

## Yeterlilik **ölçülür**: bırak-birini (LOO) çapraz doğrulama

Bir vekil "uyduruyor" olabilir: `n` nokta ile `n` katsayı her zaman tam
uyar ve hata sıfır görünür. LOO bunu yakalar — her nokta sırayla dışarıda
bırakılıp tahmin edilir.

> `q2 = 1 − SS_LOO / SS_toplam`. `q2 ≤ 0` ise vekil **ortalamadan bile
> kötüdür** ve kullanılmamalıdır. Bu bir uyarı değil, bir **hatadır**.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .design import ParamSpace

__all__ = ["Surrogate", "fit_surrogate", "design_matrix"]


def design_matrix(u: np.ndarray) -> np.ndarray:
    """İkinci derece tam polinom: `1, uᵢ, uᵢuⱼ (i ≤ j)`.

    `d = 3` için `1 + 3 + 6 = 10` terim.
    """
    u = np.atleast_2d(np.asarray(u, dtype=np.float64))
    n, d = u.shape
    suton = [np.ones(n)]
    suton.extend(u[:, j] for j in range(d))
    for i in range(d):
        for j in range(i, d):
            suton.append(u[:, i] * u[:, j])
    return np.column_stack(suton)


@dataclass(frozen=True)
class Surrogate:
    """Eğitilmiş vekil + **ölçülmüş** yeterlilik tanıları."""

    space: ParamSpace
    coef: np.ndarray          # (p,) katsayilar
    sigma: float              # artik standart sapmasi
    q2: float                 # LOO belirleme katsayisi
    rmse_loo: float
    n_egitim: int
    y_ortalama: float
    y_yayilim: float

    def predict(self, x) -> np.ndarray:
        """Doğal birimdeki noktalarda vekil tahmini."""
        u = self.space.to_unit(x)
        return design_matrix(u) @ self.coef

    @property
    def sabit(self) -> bool:
        """Gözlenebilir **hiç değişmiyor** mu?

        Bu, *"vekil yetersiz"*ten **farklı bir tanıdır** ve farklı bir
        eylem gerektirir:

        | tanı | olası neden | ne yapmalı |
        |---|---|---|
        | `sabit` | ileri model bozuk (`θ` sahneye ulaşmıyor) | **koşuyu durdur** |
        | `q2` düşük, `sabit` değil | vekil biçimi yetersiz | daha çok nokta / başka vekil |

        İkisi de `guvenilir = False` verir; ayrımı `q2` yapmaz çünkü
        sabit `y`'de `q2` **`nan`**'dır. `forward.py`'nin başlığında
        anlatılan hata (`Y₀` yanlış alana yazılır → bütün tasarım aynı
        sahneyi koşturur) tam olarak burada görünür.
        """
        return bool(self.y_yayilim <= 0.0)

    @property
    def guvenilir(self) -> bool:
        """`q2 > 0,5` — vekil varyansın yarısından fazlasını açıklıyor mu?

        Eşik keyfî değil: `q2 = 0,5` vekilin hatası ile verinin doğal
        yayılımının **eşit** olduğu noktadır. Altında vekil, sabit bir
        ortalamadan anlamlı biçimde daha iyi değildir.
        """
        return bool(self.q2 > 0.5)


def fit_surrogate(space: ParamSpace, x, y, ridge: float = 1.0e-10) -> Surrogate:
    """En küçük kareler + **LOO ile ölçülmüş** yeterlilik.

    `ridge` yalnızca sayısal koşullama içindir (tasarım matrisi tekil
    olabilir); düzenlileştirme amacı **taşımaz** ve varsayılanı ihmal
    edilebilir düzeydedir.
    """
    x = np.atleast_2d(np.asarray(x, dtype=np.float64))
    y = np.asarray(y, dtype=np.float64).ravel()
    if len(x) != len(y):
        raise ValueError(f"x ({len(x)}) ve y ({len(y)}) aynı uzunlukta olmalı")
    if not np.all(np.isfinite(y)):
        raise ValueError(f"y içinde {int(np.count_nonzero(~np.isfinite(y)))} "
                         f"sonlu olmayan değer var")
    A = design_matrix(space.to_unit(x))
    n, p = A.shape
    if n <= p:
        raise ValueError(
            f"{n} nokta ile {p} katsayı öğrenilemez (n > p gerekir). "
            f"LOO anlamsız olurdu: her nokta TAM uyardı.")

    G = A.T @ A + ridge * np.eye(p)
    coef = np.linalg.solve(G, A.T @ y)
    artik = y - A @ coef
    dof = max(n - p, 1)
    sigma = float(np.sqrt(np.sum(artik ** 2) / dof))

    # LOO artigi KAPALI FORMDA: e_loo_i = e_i / (1 - h_ii). n kez yeniden
    # cozmeye gerek yok ve sonuc AYNI (Allen 1974). Bunu ayrica sinayan
    # bir test var -- kapali form dogru mu, elle LOO ile karsilastiriliyor.
    Ginv = np.linalg.inv(G)
    hii = np.einsum("ij,jk,ik->i", A, Ginv, A)
    hii = np.clip(hii, 0.0, 1.0 - 1.0e-12)
    e_loo = artik / (1.0 - hii)
    ss_loo = float(np.sum(e_loo ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    q2 = float(1.0 - ss_loo / ss_tot) if ss_tot > 0.0 else float("nan")

    return Surrogate(space=space, coef=coef, sigma=sigma, q2=q2,
                     rmse_loo=float(np.sqrt(ss_loo / n)), n_egitim=n,
                     y_ortalama=float(np.mean(y)),
                     y_yayilim=float(np.std(y)))
