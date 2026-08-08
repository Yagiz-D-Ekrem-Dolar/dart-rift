"""FAZ 5 ensemble'ı **fizibil mi**? — A′'dan sonra yeniden hesap.

## Neden yeniden

`FIZIBILITE.md` §1 şunu yazdı:

| senaryo | toplam |
|---|---|
| 300 koşu × 1 s | **~30 GPU-günü** |
| 300 koşu × 10 s | ~300 GPU-günü |

> *"1 saniyelik koşularla ensemble fizibil. 10 saniyelik koşularla
> sınırda."*

Ama o hesap **tekdüze** bir sahnede yapıldı. A′ (ADR-0041) ölçüldü ve
DART geometrisinde **6,87×** parçacık tasarrufu veriyor (KAYIT-038).
Maliyet parçacık sayısıyla neredeyse doğrusal olduğu için **bu hesap
değişti** ve yeniden yapılmalı.

## Bu modül ne yapmıyor

**Gereken simüle süreyi bilmiyor.** O FAZ 4.5'in işi ve henüz
ölçülmedi (TRUBA kotası). Bu yüzden süre bir **parametre** olarak
taranıyor ve çıktı bir tek sayı değil, **fizibilite sınırı**:

> *"`X` GPU-günü bütçeyle, `N` koşuyla, en fazla `T` saniye simüle
> edilebilir."*

Bir sayı uydurmaktansa sınırı vermek doğrudur (RULES.txt).

## Ölçülen girdiler — hiçbiri tahmin değil

| büyüklük | değer | kaynak |
|---|---|---|
| adım maliyeti (tam fizik) | `8 658 µs / 1000 parçacık` | FIZIBILITE §2b, iş 1429628 (`N = 65 840`) |
| A′ parçacık sayısı | `11 164` | KAYIT-038 (`s = 7,0/3,5`, `r_iç = 25`) |
| tekdüze ince parçacık sayısı | `76 722` | aynı |
| `dt` | `6,9e-5 s` | FIZIBILITE §1 (`cfl·h/(c_s+v)`) |

> **`dt` A′ ile küçülür.** CFL `h`'ye bağlı ve ince bölgede `h` yarıya
> iniyor ⇒ `dt` de yarıya. Bu, tasarrufun bir kısmını **geri alır** ve
> hesaba **katılıyor** — atlanırsa A′ olduğundan ucuz görünür.

## ⚠ FIZIBILITE'nin sayılarıyla **doğrudan kıyaslanamaz**

`FIZIBILITE.md` §1 `N ≈ 2 000 000` parçacıklı bir sahne varsayıyor;
buradaki hesap `N ≈ 11 000`'lik DART sahnesinde (`s = 7 m`). İki mutlak
sayı **aynı şeyi ölçmüyor** ve birini diğerine karşı kanıt gibi sunmak
yanlış olur.

Ayrıca `FIZIBILITE` §1'in adım maliyeti **gözeneklilik ve öz-yerçekimi
kapalı** ölçülmüştü; §2b bunu düzeltti ve tam fizikte parçacık başına
maliyet **çok daha yüksek** çıktı (`8 658 µs/1000`, `N = 65 840`).
Burada §2b kullanılıyor.

> **Kıyaslanabilir olan tek şey ORAN**: A′ ile tekdüze ince arasındaki
> maliyet oranı. O da `6,87×` ve sahne ölçeğinden **bağımsız** (çünkü
> ikisi de aynı `µs/1000` ile çarpılıyor).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["OLCULEN", "adim_maliyeti_s", "kosu_maliyeti_s",
           "ensemble_gpu_gunu", "fizibilite_sinirlari"]

#: Ölçülen girdiler — **tek kaynak**. Değiştirilirse nedeni yazılmalı.
OLCULEN = {
    # FIZIBILITE §2b, is 1429628, TAM fizik (porozite + oz-yercekimi ACIK)
    "us_per_1000_parcacik": 8658.0,
    "olcum_N": 65840,
    # KAYIT-038, s = 7.0/3.5, r_ince = 25
    "N_aprime": 11164,
    "N_tumu_ince": 76722,
    "N_tumu_kaba": 10347,
    # FIZIBILITE §1
    "dt_kaba_s": 6.9e-5,
    "lam": 2.0,
}


def adim_maliyeti_s(n_parcacik: int) -> float:
    """Bir adımın duvar süresi [s] — ölçülen `µs/1000 parçacık` ile.

    Doğrusal ölçekleme **varsayımıdır** ve FIZIBILITE'de ölçülen iki
    nokta bunu tam desteklemiyor (`15 520 → 8 658 µs/1000` arasında
    `N` üç kat artarken maliyet **parçacık başına düşüyor** — komşu
    arama sabit maliyetinin amortismanı).

    > Yani bu tahmin **muhafazakârdır**: küçük `N`'de gerçek maliyet
    > daha yüksek olabilir. Yön açıkça yazılıyor.
    """
    if n_parcacik <= 0:
        raise ValueError(f"parçacık sayısı pozitif olmalı, {n_parcacik} geldi")
    return OLCULEN["us_per_1000_parcacik"] * 1e-6 * (n_parcacik / 1000.0)


def kosu_maliyeti_s(t_simule_s: float, n_parcacik: int, dt_s: float) -> float:
    """Tek bir koşunun duvar süresi [s]."""
    if t_simule_s <= 0.0:
        raise ValueError(f"simüle süre pozitif olmalı, {t_simule_s} geldi")
    if dt_s <= 0.0:
        raise ValueError(f"dt pozitif olmalı, {dt_s} geldi")
    adim = int(np.ceil(t_simule_s / dt_s))
    return adim * adim_maliyeti_s(n_parcacik)


@dataclass(frozen=True)
class Senaryo:
    ad: str
    n_parcacik: int
    dt_s: float

    def gpu_gunu(self, t_simule_s: float, n_kosu: int) -> float:
        tek = kosu_maliyeti_s(t_simule_s, self.n_parcacik, self.dt_s)
        return n_kosu * tek / 86400.0


def _senaryolar() -> list:
    """Üç senaryo: tekdüze kaba, A′, tekdüze ince.

    `dt` her senaryoda **en küçük `h`**'ye göre: CFL en kısıtlayıcı
    parçacığın hükmündedir.
    """
    dt_k = OLCULEN["dt_kaba_s"]
    lam = OLCULEN["lam"]
    return [
        # Tekduze kaba: mermi COZULMEMIS (ADR-0026) -- referans, kullanilamaz
        Senaryo("tekduze-kaba", OLCULEN["N_tumu_kaba"], dt_k),
        # A': ince bolge var -> dt lam kat KUCUK
        Senaryo("A-prime", OLCULEN["N_aprime"], dt_k / lam),
        # Tekduze ince: hem N buyuk hem dt kucuk
        Senaryo("tekduze-ince", OLCULEN["N_tumu_ince"], dt_k / lam),
    ]


def ensemble_gpu_gunu(t_simule_s: float, n_kosu: int = 300) -> dict:
    """Üç senaryonun ensemble maliyeti [GPU-günü]."""
    if n_kosu <= 0:
        raise ValueError(f"koşu sayısı pozitif olmalı, {n_kosu} geldi")
    s = _senaryolar()
    out = {x.ad: x.gpu_gunu(t_simule_s, n_kosu) for x in s}
    ap = out["A-prime"]
    out["_kazanc_tumu_inceye_gore"] = (out["tekduze-ince"] / ap if ap > 0
                                       else float("inf"))
    out["_t_simule_s"] = float(t_simule_s)
    out["_n_kosu"] = int(n_kosu)
    return out


def fizibilite_sinirlari(butce_gpu_gunu: float, n_kosu: int = 300) -> dict:
    """Verilen bütçeyle **en fazla** kaç saniye simüle edilebilir?

    Çıktı bir tek sayı değil; her senaryo için sınır. `t_simule` doğrusal
    girdiği için kapalı formda çözülüyor.
    """
    if butce_gpu_gunu <= 0.0:
        raise ValueError(f"bütçe pozitif olmalı, {butce_gpu_gunu} geldi")
    out = {}
    for x in _senaryolar():
        # 1 s icin maliyet -> bütçe / o = kac saniye
        bir_saniye = x.gpu_gunu(1.0, n_kosu)
        out[x.ad] = butce_gpu_gunu / bir_saniye if bir_saniye > 0 else float("inf")
    out["_butce_gpu_gunu"] = float(butce_gpu_gunu)
    out["_n_kosu"] = int(n_kosu)
    return out
