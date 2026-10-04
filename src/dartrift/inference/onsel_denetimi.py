"""Önsel denetimi — ölçülen `β(Y₀)` eğrisinden **önselin** sınanması (ADR-0053).

Niçin gerekli: `recovery.py`'nin `C2` ölçütü **kenara çakılmış** bir ekseni
bilgilendirici saymaz (haklı olarak: gerçek değer önselin dışındaysa posterior
sınıra dayanır ve aldatıcı biçimde dar görünür). Bu modül aynı tuzağı
**havuzdan önce** yakalar: ölçülen `β(Y₀)` eğrisini tersine çevirip gözlemin
hangi `Y₀`'ya düştüğünü söyler ve önsel aralığın o noktayı içerip içermediğine
**kilitli** bir yargı verir.

Kural: dışdeğerleme sessiz geçmez. Çözülen `Y₀` ölçüm aralığının dışındaysa
sonuç `disdegerleme = True` ile döner ve yargı bunu söyler.

Kilitli eşikler
---------------
``ESIK_KENAR_DEKAD = 0.5``
    Gözlemin düştüğü `Y₀`, önsel kenarına bu kadar **dekaddan** yakınsa yargı
    `GOZLEM ONSEL KENARINDA`. Gerekçe: `C2`'nin çakılma denetimi ancak gerçek
    değer aralığın *içinde ve kenardan uzakta* iken anlamlı bir bant üretir;
    yarım dekad, `β`'nın `Y₀`'ya duyarlılığı (`p ≈ 0,08`) ile çarpıldığında
    `b`'de `~%4`, yani gözlem sd'sinin `~%25`'i kadar yer bırakır.
``ESIK_DISDEGERLEME = 1.0``
    Çözülen `Y₀`, ölçülen `Y₀` aralığından bu kadar **dekaddan** fazla
    uzaktaysa `cok_uzak = True` — sayı yazılır ama **ölçümle doğrulanmalıdır**.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["ESIK_KENAR_DEKAD", "ESIK_DISDEGERLEME", "ESIK_CARPAN_TANIMLI",
           "OLCULEN_Y0_BETA", "OLCULEN_Y0_SERILERI", "Uydurma", "Gozlemli",
           "guc_yasasi_uydur", "beta_tahmin", "y0_coz", "duyarlilik_carpani",
           "onsel_denetle", "duyarlilik_tablosu", "uretim_gozlemlileri"]

ESIK_KENAR_DEKAD = 0.5
ESIK_DISDEGERLEME = 1.0
#: Bir gözlemli `Y₀`'yu bu **çarpandan** daha iyi sıkıştırıyorsa "tanımlayıcı"
#: sayılır. `3,0` ≈ `0,48` dekad; `4` dekadlık önselde `~8` kat daralma, yani
#: `tanimlanabilirlik.DARALMA_OGRENILDI = 0,5` eşiğinin rahat üstü.
ESIK_CARPAN_TANIMLI = 3.0

#: Ölçülen `(Y₀ [Pa], β(600 s))` çiftleri — **kıyas sahnesi** (W2: 75 m homojen
#: küre, dik çarpma, tek küre mermi, kaba merdiven). Kaynak: KAYIT-067 §2 ve
#: `docs/olcumler/W2_UA_2026-09-19/`. Anahtar `t_geçiş`; üretim değeri `1,0 s`
#: (PROTOKOL-UG). Bu çiftler **uydurulmadı**, koşulardan okundu.
OLCULEN_Y0_BETA: dict[float, dict[float, float]] = {
    0.2: {1.0: 3.9920, 10.0: 3.6669, 50.0: 3.2953},
    1.0: {1.0: 4.3889, 10.0: 4.0699, 50.0: 3.4938},
}


@dataclass(frozen=True)
class Uydurma:
    """`b = β − 1 = C · Y₀^p` güç yasası (log-log doğrusal en küçük kareler)."""

    C: float
    p: float
    Y_alt: float
    Y_ust: float
    n: int
    artik_en_buyuk: float
    """`b`'de en büyük bağıl artık — uydurmanın ne kadar iyi olduğu."""

    def __post_init__(self) -> None:
        if not (self.C > 0.0 and np.isfinite(self.p)):
            raise ValueError(f"gecersiz uydurma: C={self.C}, p={self.p}")


def _guc_yasasi_ham(Y0, deger) -> Uydurma:
    """`v = C · Y₀^p` — log-log en küçük kareler. `deger` **olduğu gibi** alınır."""
    y = np.asarray(Y0, dtype=np.float64).ravel()
    v = np.asarray(deger, dtype=np.float64).ravel()
    if y.size != v.size or y.size < 2:
        raise ValueError("en az 2 nokta ve esit uzunluk gerekir")
    if np.any(y <= 0.0) or np.any(v <= 0.0):
        raise ValueError("Y0 > 0 ve deger > 0 olmali")
    p, lc = np.polyfit(np.log(y), np.log(v), 1)
    C = float(np.exp(lc))
    tahmin = C * y ** p
    return Uydurma(C=C, p=float(p), Y_alt=float(y.min()), Y_ust=float(y.max()),
                   n=int(y.size),
                   artik_en_buyuk=float(np.max(np.abs(tahmin - v) / v)))


def guc_yasasi_uydur(Y0, beta) -> Uydurma:
    """`(Y₀, β)` çiftlerine `b = C · Y₀^p` uydurur (`b = β − 1`).

    En az 2 nokta ister; `Y₀ > 0` ve `β > 1` olmalı (aksi hâlde `log` tanımsız
    ve `b ≤ 0` fiziksel değil).
    """
    b = np.asarray(beta, dtype=np.float64).ravel() - 1.0
    if np.any(b <= 0.0):
        raise ValueError("beta > 1 olmali")
    return _guc_yasasi_ham(Y0, b)


def beta_tahmin(uy: Uydurma, Y0) -> np.ndarray:
    """Uydurmanın `Y₀`'da öngördüğü `β`."""
    y = np.asarray(Y0, dtype=np.float64)
    if np.any(y <= 0.0):
        raise ValueError("Y0 > 0 olmali")
    return 1.0 + uy.C * y ** uy.p


def y0_coz(uy: Uydurma, beta_hedef: float) -> float:
    """`β_hedef`'i veren `Y₀` (güç yasasının tersi).

    `p = 0` ise `β`, `Y₀`'dan bağımsızdır ve ters çözüm yoktur → `ValueError`.
    """
    b = float(beta_hedef) - 1.0
    if b <= 0.0:
        raise ValueError(f"beta_hedef > 1 olmali, {beta_hedef} geldi")
    if uy.p == 0.0:
        raise ValueError("p = 0: beta, Y0'dan bagimsiz -- ters cozum yok")
    return float(np.exp((np.log(b) - np.log(uy.C)) / uy.p))


def duyarlilik_carpani(uy: Uydurma, sigma_bagil: float) -> float:
    """`b`'de `1σ`'ya karşılık gelen `Y₀` **çarpanı**.

    `σ_bağıl`, `b` üzerinden bağıl toplam sd (ör. `payda / (β − 1)`).
    Dönen sayı büyükse `β` tek başına `Y₀`'yu ayırt etmiyor demektir:
    `10` çarpanı "bir dekad belirsizlik" anlamına gelir.
    """
    s = float(sigma_bagil)
    if not (s > 0.0):
        raise ValueError("sigma_bagil > 0 olmali")
    if uy.p == 0.0:
        return float("inf")
    return float(np.exp(abs(np.log1p(s) / uy.p)))


def onsel_denetle(uy: Uydurma, *, beta_gozlem: float, sigma_toplam: float,
                  onsel_lo: float, onsel_hi: float) -> dict:
    """**KİLİTLİ yargı:** önsel aralık gözlemin `Y₀`'sını içeriyor mu?

    | yargı | koşul |
    |---|---|
    | `ONSEL GOZLEMI ICERMIYOR` | çözülen `Y₀` `[lo, hi]` dışında |
    | `GOZLEM ONSEL KENARINDA` | kenara `≤ ESIK_KENAR_DEKAD` dekad |
    | `ONSEL GOZLEMI ICERIYOR` | ikisi de değil |

    `disdegerleme` / `cok_uzak`, çözülen `Y₀`'nın ölçüm aralığının dışında
    olup olmadığını söyler; yargıyı **değiştirmez**, yanına yazılır.
    """
    if not (0.0 < onsel_lo < onsel_hi):
        raise ValueError("0 < onsel_lo < onsel_hi olmali")
    y = y0_coz(uy, beta_gozlem)
    d_lo = float(np.log10(y / onsel_lo))
    d_hi = float(np.log10(onsel_hi / y))
    disinda = d_lo < 0.0 or d_hi < 0.0
    kenarda = (not disinda) and min(d_lo, d_hi) <= ESIK_KENAR_DEKAD
    genel = ("ONSEL GOZLEMI ICERMIYOR" if disinda else
             "GOZLEM ONSEL KENARINDA" if kenarda else "ONSEL GOZLEMI ICERIYOR")
    disdegerleme = not (uy.Y_alt <= y <= uy.Y_ust)
    uzaklik = 0.0 if not disdegerleme else float(
        max(np.log10(uy.Y_alt / y), np.log10(y / uy.Y_ust)))
    s_bagil = float(sigma_toplam) / (float(beta_gozlem) - 1.0)
    return {"Y0_gozlem": y, "dekad_alt_kenara": d_lo, "dekad_ust_kenara": d_hi,
            "onsel": [float(onsel_lo), float(onsel_hi)],
            "onsel_dekad": float(np.log10(onsel_hi / onsel_lo)),
            "beta_onsel_alt_kenarda": float(beta_tahmin(uy, onsel_lo)),
            "beta_onsel_ust_kenarda": float(beta_tahmin(uy, onsel_hi)),
            "sigma_bagil": s_bagil,
            "Y0_carpani_1sigma": duyarlilik_carpani(uy, s_bagil),
            "olcum_araligi": [uy.Y_alt, uy.Y_ust],
            "disdegerleme": disdegerleme, "dekad_olcum_disi": uzaklik,
            "cok_uzak": bool(uzaklik > ESIK_DISDEGERLEME),
            "p": uy.p, "C": uy.C, "artik_en_buyuk": uy.artik_en_buyuk,
            "genel": genel}


#: Ölçülen `Y₀ → gözlemli` serileri — **W2 kıyas sahnesi**, `t_geçiş = 1,0 s`
#: (üretim değeri, PROTOKOL-UG), `600 s`. `β` dışındakiler `impuls_sekli` ve
#: `fizik_tani`'dan okundu (KAYIT-067 koşuları, 2026-10-04'te yeniden okundu).
OLCULEN_Y0_SERILERI: dict[str, dict[float, float]] = {
    "beta": {1.0: 4.3889, 10.0: 4.0699, 50.0: 3.4938},
    "M_ejekta": {1.0: 5.6714e7, 10.0: 3.0290e7, 50.0: 1.5957e7},
    "t50": {1.0: 1.6741, 10.0: 1.0095, 50.0: 0.4613},
    "t90": {1.0: 25.758, 10.0: 11.419, 50.0: 4.423},
}


@dataclass(frozen=True)
class Gozlemli:
    """Bir gözlemlinin `Y₀` serisi, toplam bağıl sd'si ve **gözlenip gözlenmediği**.

    `gozlenen = False` ise bu büyüklüğün DART için ölçülmüş bir karşılığı
    **yoktur**: posteriora giremez, yalnız mekanizma tanısı olur (KAYIT-072 §3).
    Tabloda görünür ama "tanımlayıcı" seçilemez.
    """

    ad: str
    seri: dict[float, float]
    sd_bagil: float
    gozlenen: bool
    eksi_bir: bool = False
    kaynak: str = ""

    def __post_init__(self) -> None:
        if not (self.sd_bagil > 0.0):
            raise ValueError(f"{self.ad}: sd_bagil > 0 olmali")
        if len(self.seri) < 2:
            raise ValueError(f"{self.ad}: en az 2 nokta gerekir")


def _uydur(g: Gozlemli) -> Uydurma:
    Y = sorted(g.seri)
    d = [g.seri[y] for y in Y]
    return guc_yasasi_uydur(Y, d) if g.eksi_bir else _guc_yasasi_ham(Y, d)


def duyarlilik_tablosu(gozlemliler) -> dict:
    """Hangi gözlemli `Y₀`'yu ne kadar sıkıştırıyor — **kilitli yargı**.

    Her gözlemli için güç yasası üssü `p` ve `1σ`'ya karşılık gelen `Y₀`
    **çarpanı** hesaplanır. Yargı yalnız `gozlenen = True` olanlara bakar:

    | yargı | koşul |
    |---|---|
    | `Y0'I TANIMLAYAN GOZLEMLI VAR` | en iyi gözlenen çarpan `< ESIK_CARPAN_TANIMLI` |
    | `Y0 GOZLEMLILERLE TANIMLANAMAZ` | hepsi `≥ ESIK_CARPAN_TANIMLI` |
    """
    satir = []
    for g in gozlemliler:
        uy = _uydur(g)
        satir.append({"ad": g.ad, "p": uy.p, "carpan_1sigma": duyarlilik_carpani(
            uy, g.sd_bagil), "sd_bagil": g.sd_bagil, "gozlenen": g.gozlenen,
            "artik_en_buyuk": uy.artik_en_buyuk, "kaynak": g.kaynak,
            "dekad_1sigma": float(np.log10(duyarlilik_carpani(uy, g.sd_bagil)))})
    satir.sort(key=lambda r: r["carpan_1sigma"])
    gozlenenler = [r for r in satir if r["gozlenen"]]
    if not gozlenenler:
        raise ValueError("en az bir gozlenen gozlemli gerekir")
    en_iyi = gozlenenler[0]
    genel = ("Y0'I TANIMLAYAN GOZLEMLI VAR"
             if en_iyi["carpan_1sigma"] < ESIK_CARPAN_TANIMLI
             else "Y0 GOZLEMLILERLE TANIMLANAMAZ")
    ref = next((r for r in satir if r["ad"] == "beta"), None)
    return {"satirlar": satir, "en_iyi_gozlenen": en_iyi["ad"],
            "en_iyi_carpan": en_iyi["carpan_1sigma"],
            "esik": ESIK_CARPAN_TANIMLI,
            "beta_ya_gore_kazanc": (None if ref is None else
                                    ref["carpan_1sigma"] / en_iyi["carpan_1sigma"]),
            "genel": genel}


def uretim_gozlemlileri(*, sigma_beta_toplam: float, beta_gozlem: float,
                        sigma_M_bagil: float) -> list[Gozlemli]:
    """Üretim ayarındaki dört gözlemli (`OLCULEN_Y0_SERILERI`'nden).

    `t50`/`t90` **gözlenmiyor** (DART için ölçülmüş karşılığı yok) —
    tabloda tanı olarak görünürler, posteriora girmezler.
    """
    S = OLCULEN_Y0_SERILERI
    return [
        Gozlemli("beta", S["beta"], sigma_beta_toplam / (beta_gozlem - 1.0),
                 True, eksi_bir=True, kaynak="PROTOKOL-U S1 + model eksikligi"),
        Gozlemli("M_ejekta", S["M_ejekta"], sigma_M_bagil, True,
                 kaynak="L17 Lolachi (1,6 +- 0,3e7) + gerceklem_M_ejekta"),
        Gozlemli("t50", S["t50"], 0.20, False, kaynak="KAYIT-070 S2 tanisi"),
        Gozlemli("t90", S["t90"], 0.20, False, kaynak="KAYIT-070 S2 tanisi"),
    ]
