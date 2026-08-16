"""Deney tasarımı — ileri koşuların **hangi** parametrelerde yapılacağı.

## Kısıt: koşular pahalı

Her nokta bir GPU benzetimidir. Üç parametre (`α₀`, `Y₀`, `f_boulder`)
için tam çarpanlı tasarım `3³ = 27` koşu eder; Latin hiperküp aynı
kapsamayı **daha az** noktayla verir.

## Determinizm (ADR-0004)

Tasarım `root_seed`'e bağlıdır ve `rng.stream_generator` kullanır —
proje genelindeki tek akış kaynağı. Aynı tohum aynı tasarımı verir;
farklı tohum farklı ama **tekrarlanabilir** bir tasarım verir.

## `Y₀` neden logaritmik

`Y₀` kohezyondur ve `1e3 … 1e7 Pa` gibi **dört mertebe** tarar. Doğrusal
örnekleme noktaların neredeyse tamamını üst mertebeye yığar. ADR-0009'un
malzeme aralıkları da logaritmik verilmiştir.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["ParamSpace", "factorial_design", "lhs_design",
           "DART_UZAYI", "DART_UZAYI_S3"]


@dataclass(frozen=True)
class ParamSpace:
    """Parametre adları, sınırları ve ölçekleri.

    `log` işaretli parametreler **logaritmik** örneklenir; sınırlar yine
    doğal birimde verilir.
    """

    names: tuple[str, ...]
    lo: tuple[float, ...]
    hi: tuple[float, ...]
    log: tuple[bool, ...]

    def __post_init__(self) -> None:
        n = len(self.names)
        if not (len(self.lo) == len(self.hi) == len(self.log) == n):
            raise ValueError("names/lo/hi/log aynı uzunlukta olmalı")
        if n == 0:
            raise ValueError("en az bir parametre gerekir")
        for a, b, ad in zip(self.lo, self.hi, self.names):
            if not (b > a):
                raise ValueError(f"{ad}: hi > lo olmalı ({a} → {b})")
        for a, lg, ad in zip(self.lo, self.log, self.names):
            if lg and a <= 0.0:
                raise ValueError(f"{ad}: logaritmik parametre pozitif olmalı")

    @property
    def ndim(self) -> int:
        return len(self.names)

    def to_unit(self, x) -> np.ndarray:
        """Doğal birim → `[0,1]^d`. Logaritmik eksenler `log10`'da düzleşir."""
        x = np.atleast_2d(np.asarray(x, dtype=np.float64))
        if x.shape[1] != self.ndim:
            raise ValueError(f"şekil {x.shape}, (*, {self.ndim}) olmalı")
        u = np.empty_like(x)
        for j, lg in enumerate(self.log):
            a, b = self.lo[j], self.hi[j]
            if lg:
                u[:, j] = (np.log10(x[:, j]) - np.log10(a)) / (np.log10(b) - np.log10(a))
            else:
                u[:, j] = (x[:, j] - a) / (b - a)
        return u

    def from_unit(self, u) -> np.ndarray:
        """`[0,1]^d` → doğal birim. `to_unit`'in **tam** tersi."""
        u = np.atleast_2d(np.asarray(u, dtype=np.float64))
        if u.shape[1] != self.ndim:
            raise ValueError(f"şekil {u.shape}, (*, {self.ndim}) olmalı")
        x = np.empty_like(u)
        for j, lg in enumerate(self.log):
            a, b = self.lo[j], self.hi[j]
            if lg:
                x[:, j] = 10.0 ** (np.log10(a) + u[:, j] * (np.log10(b) - np.log10(a)))
            else:
                x[:, j] = a + u[:, j] * (b - a)
        return x

    def prior_width(self) -> np.ndarray:
        """Önselin **`%68` aralığı** — G4-C2'nin paydası.

        ## Bu `1,0` değildir

        İlk yazdığımda `1,0` döndürüyordum: *"birim küpte önsel bir
        birim geniştir."* **Yanlış payda.** C2 posteriorun `%68`
        aralığını ölçüyor; onu önselin **tam genişliğiyle** kıyaslamak
        elmayla armut kıyaslamaktır.

        Düzgün dağılımın `16–84` yüzdelikleri arası **tam `0,68`**'dir.
        Ölçüldü: bilgisiz bir posteriorda (`predict ≡ 0`, `n_grid = 200`)
        `width_u = 0,68342` — ayrıklaştırma payıyla birlikte.

        Hatanın yönü önemli: eski payda C2'yi **belgede yazandan zayıf**
        yapıyordu. `%50` eşiği `0,50` yerine `0,34` demeliydi; yani
        bilgisiz bir posterior `0,683` ile eşiğe `%37` yaklaşıyordu,
        oysa `%100` uzak olmalıydı.
        """
        return np.full(self.ndim, 0.68, dtype=np.float64)


#: FAZ 4.6'nın parametre uzayı. Sınırlar ADR-0009 (malzeme) ve FAZ 3'ün
#: moloz-yığını üreticisinden gelir; **burada uydurulmadı**.
DART_UZAYI = ParamSpace(
    names=("alpha0", "Y0", "f_boulder"),
    lo=(1.10, 1.0e3, 0.0),
    hi=(2.00, 1.0e7, 0.50),
    log=(False, True, False),
)
#: .. deprecated:: ADR-0044 (KABUL EDİLDİ, 2026-08-09)
#:    **Bu uzay `ρ_yığın` kısıtıyla TUTARSIZ ve uygulanabilir oranı `0`.**
#:    Varsayılan artık :data:`DART_UZAYI_S3`. Bu tanım **silinmedi** ki
#:    karar geri alınabilsin ve gerileme testleri koşabilsin.
#:    `ρ_yığın` sabitken `matrix_alpha0`, `f_boulder`'ın fonksiyonudur;
#:    ayrıca `f_boulder = 0` `M1` sınıfında yasaktır. Ölçüm ve dört
#:    seçenek: :doc:`ADR-0044 <../../../docs/adr/ADR-0044-cikarim-parametre-uzayi-tutarsiz>`.
#:    Değiştirilmedi çünkü karar **kilitlenmedi** (RULES.txt).

#: ADR-0044 **Seçenek 3** — `matrix_alpha0` artık serbest değil,
#: `ρ_yığın`'dan **türetiliyor**; yerine `boulder_alpha0` çıkarıma
#: giriyor (şu an `1,05`'te sabit kodlu ve gerçekte bilinmiyor).
#:
#: | sınır | gerekçe |
#: |---|---|
#: | `boulder_alpha0 ∈ [1,00 , 1,30]` | `1,0` = tam katı blok; `1,30` üstü türetilen matris `α₀`'ı `%67` gözenekliliğin üstüne çıkarır |
#: | `f_boulder ∈ [0,05 , 0,50]` | alt sınır `0` **olamaz** (M1 blok ister); üst sınır yasak eğrinin (`0,667`) altında |
#:
#: **KABUL EDİLDİ (ADR-0044) — çıkarımın VARSAYILAN uzayı budur.**
#:
#: ADR-0044 §6 madde 2 (gözlenebilirler bunları ayırt ediyor mu) ucuza
#: ölçülemedi; ölçüm **G4-C `C2`'nin içine** taşındı. `C2` düşerse uzay
#: dejenere demektir ve ADR-0044 yeniden açılır.
DART_UZAYI_S3 = ParamSpace(
    names=("boulder_alpha0", "Y0", "f_boulder"),
    lo=(1.00, 1.0e3, 0.05),
    hi=(1.30, 1.0e7, 0.50),
    log=(False, True, False),
)


def factorial_design(space: ParamSpace, levels: int = 3) -> np.ndarray:
    """Tam çarpanlı tasarım — `levels^d` nokta, **kenarlar dahil**.

    Kenarları içerdiği için vekilin **dışdeğerleme** yapması gerekmez;
    bedeli nokta sayısının katlanarak büyümesidir.
    """
    if levels < 2:
        raise ValueError(f"levels >= 2 olmalı, {levels} geldi")
    eksen = np.linspace(0.0, 1.0, levels)
    izgara = np.meshgrid(*([eksen] * space.ndim), indexing="ij")
    u = np.column_stack([g.ravel() for g in izgara])
    return space.from_unit(u)


def lhs_design(space: ParamSpace, n: int, root_seed: int = 0,
               stream: str = "inference_design") -> np.ndarray:
    """Latin hiperküp — her eksende `n` katman, her katmanda **tam bir** nokta.

    Tam çarpanlıya göre aynı kapsamayı çok daha az noktayla verir; bedeli
    kenarların garanti **olmamasıdır** (katman içinde rastgele konum).
    Bu yüzden `factorial_design` ile birlikte kullanılması önerilir:
    kenarlar oradan, iç kapsama buradan.
    """
    if n < 2:
        raise ValueError(f"n >= 2 olmalı, {n} geldi")
    from ..rng import stream_generator

    g = stream_generator(root_seed, stream)
    u = np.empty((n, space.ndim), dtype=np.float64)
    for j in range(space.ndim):
        katman = (np.arange(n) + g.random(n)) / n
        u[:, j] = g.permutation(katman)
    return space.from_unit(u)


#: **ADR-0046 KARARI (2026-08-11): çıkarım uzayı ölçülebilir olana indirildi.**
#:
#: `DART_UZAYI_S3`'ün üç parametresi **yapısı gereği tek boyutlu** çıktı.
#: Ölçülen gerekçe (FAZ 4.11/4.12, KAYIT-046):
#:
#: * `Y0` dört mertebe (`10³→10⁷ Pa`) değişirken `β` `0,001`, derinlik
#:   `0,077 m` oynuyor — `t = 20 s`'de bile. `Y0` **gözlenemeyen alt
#:   uzayda** (boş uzay yönünün en büyük bileşeni, `0,81`).
#: * Kalan ikisinin `2×2` Jacobian'ının **koşul sayısı `79,5`**; ikinci
#:   yönü kurtarmak `%0,067` gözlem kesinliği ister, DART'ın `β` ölçümü
#:   `~%5`.
#: * Kök neden: `ρ_yığın` ADR-0030 gereği **sabit**, dolayısıyla üretici
#:   `matrix_alpha0`'ı `(boulder_alpha0, f_boulder)`'dan **türetiyor**.
#:   Derinlik ile matris `α₀` korelasyonu `r = −0,9932`.
#:
#: Yani çarpma **matris gözenekliliğini** hissediyor; ona nasıl
#: varıldığını hissetmiyor. Serbest bırakılan şey artık doğrudan o.
#:
#: **Sınırlar keyfi değil:** mevcut ensemble'ın `(boulder_alpha0,
#: f_boulder)` kutusunun ürettiği matris `α₀` aralığıdır
#: (`1,5122 – 3,0000`). Dışına çıkmak **dışdeğerleme** olurdu.
#:
#: > **Bilimsel iddia daraldı ve bu gizlenmiyor:** *"iç yapıyı
#: > çıkardık"* değil **"matris gözenekliliğini çıkardık"**.
#: > `f_boulder` (Hera'nın görüntüleyeceği büyüklük) artık serbest
#: > değil. Bunun bedeli ADR-0046 §4'te yazılı.
DART_UZAYI_S1 = ParamSpace(
    names=("matrix_alpha0",),
    lo=(1.5122,),
    hi=(3.0000,),
    log=(False,),
)
