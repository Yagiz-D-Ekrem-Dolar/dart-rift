"""Ara an (snapshot) kare planı — **logaritmik** zamanlar ve **sabit** altörnek.

## Niçin bu modül var

`io_hdf5.write_snapshot` yazılmış, sınavlanmış ve **hiçbir yerden
çağrılmıyor** (A116, üçüncü örnek). Bağlanmadan önce iki karar doğru
verilmeli; ikisi de yanlış verilirse geri dönüşü pahalı:

### 1. Kareler eşit aralıklı OLAMAZ

Koşu `600 s` ama ilginç olan ilk saniyeler: şok cephesi, kazı, koninin
doğuşu. `600 s`'yi `180` eşit parçaya bölersek aralık `3,33 s` olur ve
**çarpmanın tamamı tek karede** geçer. Geri kalan `179` kare neredeyse
donmuş bir görüntüdür.

Çare: **bölümlü** plan — erken aralıkta sık, geç aralıkta seyrek.

### 2. Altörnek kareler arasında DEĞİŞMEMELİ

Depolama için parçacıkların bir alt kümesi yazılır. Alt küme her karede
yeniden çekilirse parçacıklar kare kare **görünüp kaybolur**; video
gürültüye döner ve hiçbir şey izlenemez. Alt küme **bir kez** seçilip
bütün karelerde **aynı** kalmalı.

Bu modül ikisini de deterministik olarak üretir ve sınavlar. Karar kuralı
değildir: hangi planın kullanılacağını protokol kilitler.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "Bolum",
    "kare_zamanlari",
    "AnlikPlanlayici",
    "sabit_altornek",
    "VIDEO_PLANI",
    "A95_PLANI",
]


@dataclass(frozen=True)
class Bolum:
    """Tek bir zaman bölümü: `[t0, t1]` arasında `n` kare.

    `log=True` ise kareler geometrik (logaritmik) aralıklı. `t0 = 0` ile
    `log=True` tanımsızdır (`log 0`), bu yüzden reddedilir — sıfır anını
    isteyen bölüm `log=False` olmalı ya da `t0` küçük bir taban almalı.
    """

    t0: float
    t1: float
    n: int
    log: bool = False

    def __post_init__(self) -> None:
        if not (np.isfinite(self.t0) and np.isfinite(self.t1)):
            raise ValueError("t0 ve t1 sonlu olmali")
        if self.t1 <= self.t0:
            raise ValueError(f"t1 > t0 olmali: {self.t0} -> {self.t1}")
        if self.n < 1:
            raise ValueError("n >= 1 olmali")
        if self.log and self.t0 <= 0.0:
            raise ValueError("log bolumde t0 > 0 olmali (log 0 tanimsiz)")

    def zamanlar(self) -> np.ndarray:
        """Bu bölümün kare zamanları; `t0` **dahil değil**, `t1` dahil.

        `t0` dışarıda bırakılır ki ardışık bölümler sınırda kare
        tekrarlamasın: bir önceki bölüm `t1`'i zaten yazdı.
        """
        if self.log:
            return np.geomspace(self.t0, self.t1, self.n + 1)[1:]
        return np.linspace(self.t0, self.t1, self.n + 1)[1:]


def kare_zamanlari(bolumler, *, t_sifir: bool = True) -> np.ndarray:
    """Bölümlerden tek bir artan, **tekrarsız** kare zamanı dizisi.

    `t_sifir=True` ise `t = 0` başa eklenir (çarpma öncesi an; videonun
    açılış karesi ve `β` karşılaştırması için gerekli).

    Bölümler bitişik olmak zorunda: `bolum[i].t1 == bolum[i+1].t0`.
    Boşluk ya da örtüşme sessizce kabul edilmez — plan okunabilir olmalı.
    """
    bl = list(bolumler)
    if not bl:
        raise ValueError("en az bir bolum gerekli")
    # `strict=False`: uzunluklar KASTEN bir fark eder (ardisik ciftler).
    for a, b in zip(bl, bl[1:], strict=False):
        if not np.isclose(a.t1, b.t0, rtol=0.0, atol=1e-12):
            raise ValueError(
                f"bolumler bitisik degil: {a.t1} -> {b.t0}")
    parcalar = [np.asarray([0.0])] if t_sifir else []
    parcalar += [b.zamanlar() for b in bl]
    t = np.concatenate(parcalar)
    # Kayan nokta yuvarlamasi sinirda kopya uretebilir; `unique` hem
    # siralar hem tekillestirir. Tekrarlayan kare = ayni an iki kez
    # yazilir = dosya sisir, video takilir.
    t = np.unique(t)
    if np.any(np.diff(t) <= 0.0):
        raise AssertionError("kare zamanlari kesin artan olmali")
    return t


class AnlikPlanlayici:
    """Entegrasyon döngüsünde "şimdi kare yazmalı mıyım" sorusunu yanıtlar.

    Zaman adımı değişken; bir adım **birden çok** kare zamanını atlayabilir.
    `gereken(t_onceki, t_simdi)` o aralığa düşen **bütün** kare
    indekslerini verir, böylece hiçbir kare kaçmaz.

    Aralık `(t_onceki, t_simdi]` — yarı açık. Böylece ardışık çağrılarda
    aynı kare **iki kez** dönmez.
    """

    def __init__(self, zamanlar) -> None:
        t = np.asarray(zamanlar, dtype=np.float64).ravel()
        if t.size == 0:
            raise ValueError("en az bir kare zamani gerekli")
        if np.any(~np.isfinite(t)):
            raise ValueError("kare zamanlari sonlu olmali")
        if np.any(np.diff(t) <= 0.0):
            raise ValueError("kare zamanlari kesin artan olmali")
        self.zamanlar = t
        self._yazildi = np.zeros(t.size, dtype=bool)

    @property
    def n_kare(self) -> int:
        return int(self.zamanlar.size)

    def gereken(self, t_onceki: float, t_simdi: float) -> list[int]:
        """`(t_onceki, t_simdi]` aralığına düşen kare indeksleri."""
        if not (np.isfinite(t_onceki) and np.isfinite(t_simdi)):
            raise ValueError("t_onceki ve t_simdi sonlu olmali")
        if t_simdi < t_onceki:
            raise ValueError("t_simdi >= t_onceki olmali")
        sol = int(np.searchsorted(self.zamanlar, t_onceki, side="right"))
        sag = int(np.searchsorted(self.zamanlar, t_simdi, side="right"))
        idx = list(range(sol, sag))
        self._yazildi[sol:sag] = True
        return idx

    def eksik(self) -> list[int]:
        """Henüz yazılmamış kare indeksleri (koşu sonunda denetim için)."""
        return [int(i) for i in np.flatnonzero(~self._yazildi)]


def sabit_altornek(n: int, hedef: int, *, tohum: int) -> np.ndarray:
    """Kareler arasında **değişmeyen** altörnek indeksleri (artan sırada).

    `n` toplam parçacık, `hedef` istenen sayı. `hedef >= n` ise bütün
    indeksler döner (altörnekleme yok).

    Bu fonksiyon koşu başında **bir kez** çağrılır ve dönen dizi bütün
    karelerde kullanılır. Her karede yeniden çağırmak — aynı tohumla bile
    — doğru olurdu, ama parçacık sayısı değişirse (kaçanların dondurulması,
    A92) farklı küme çıkar; bu yüzden çağrı **tek** olmalı ve sonuç
    saklanmalı. Çağrı yeri bunu belgelemekle yükümlü.
    """
    if n < 0:
        raise ValueError("n >= 0 olmali")
    if hedef < 1:
        raise ValueError("hedef >= 1 olmali")
    if hedef >= n:
        return np.arange(n, dtype=np.int64)
    rng = np.random.default_rng(tohum)
    idx = rng.choice(n, size=hedef, replace=False)
    return np.sort(idx).astype(np.int64)


# --- hazır planlar (protokol bunları seçer, bu modül karar vermez) -------

#: Sinematik video planı: `0-1 s` sık, `1-60 s` orta, `60-600 s` seyrek.
#: `0 s` dahil → `181` kare. Logaritmik bölümler erken anı çözer.
VIDEO_PLANI = (
    Bolum(0.0, 1.0, 60),
    Bolum(1.0, 60.0, 60, log=True),
    Bolum(60.0, 600.0, 60, log=True),
)

#: A95 koni düzeltmesi: koni `~170 s` civarında **konumdan** ölçülecek.
#: Tek an yetmez (ölçümün ana duyarlılığı bilinmiyor), bu yüzden
#: `100-250 s` arası sık örneklenir.
A95_PLANI = (
    Bolum(0.0, 100.0, 10),
    Bolum(100.0, 250.0, 30),
    Bolum(250.0, 600.0, 10),
)
