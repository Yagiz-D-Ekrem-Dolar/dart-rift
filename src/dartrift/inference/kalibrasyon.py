"""Posterior kalibrasyonu — simülasyon tabanlı kalibrasyon (SBC) ve kapsama (ADR-0051).

## Neden

P2 (dış örneklem) **KALİBRASYON DÜŞTÜ**, P-v4b GP **AŞIRI GÜVENLİ** çıktı
(`docs/SONUC-M-N-P-J-T.md` §1, §2d). G4-C tek bir "gerçek" θ ile sınıyordu:
tek noktada bant gerçeği içerebilir ama posterior yine de **sistematik olarak**
dar olabilir. Doğru sınama (Cook, Gelman & Rubin 2006; Talts ve diğ. 2018,
arXiv:1804.06788):

1. gerçeği **önselden** çek,
2. o gerçekle veri üret (gürültüsüyle),
3. posterioru hesapla,
4. gerçeğin posterior CDF'deki yerini (PIT) kaydet.

Kalibre bir çıkarımda PIT **tam olarak** `U(0, 1)`'dir. Izgara posteriorunda
PIT, SBC'nin sıra istatistiğinin sürekli karşılığıdır.

## Ne ölçülüyor

- `pit_degeri`: tek eksende `F_post(θ_gerçek)`; kenar yoğunluğu düğümler
  arasında **doğrusal** kabul edilir ve CDF tam integrallenir (A85/A87'nin
  yarım bölme kayması burada yok).
- `kapsama_egrisi`: merkezi `%50 / %68 / %90 / %95` aralıklarının deneysel
  kapsaması ve binom standart hatası. Merkezi `L` aralığı gerçeği içerir ⇔
  `|PIT − 0,5| ≤ L/2`.
- `pit_tanisi`: KS düzgünlük sınaması + biçim (sabitler aşağıda, **ölçümden
  önce** yazıldı):

| tanı | koşul |
|---|---|
| AŞIRI GÜVENLİ | `%68` kapsama `< 0,68 − 2 SE` (PIT uçlara yığılıyor) |
| AŞIRI TEMKİNLİ | `%68` kapsama `> 0,68 + 2 SE` (PIT ortaya yığılıyor) |
| YANLI | ortalama PIT, `0,5`'ten `2 SE`'den uzak (`SE = √(1/12n)`) |
| KALİBRE | hiçbiri **ve** KS `p ≥ 0,05` |
| DÜZGÜN DEĞİL | biçim tanılarından hiçbiri ama KS `p < 0,05` |
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

__all__ = ["pit_degeri", "kapsama_egrisi", "pit_tanisi", "ks_duzgunluk",
           "SBCSonuc", "sbc_calistir", "SEVIYELER", "KS_ESIGI", "SE_KATI"]

#: Kapsama eğrisinin nominal düzeyleri.
SEVIYELER = (0.50, 0.68, 0.90, 0.95)
#: KS düzgünlük sınamasının anlamlılık eşiği.
KS_ESIGI = 0.05
#: Biçim tanılarında kaç standart hata sapma "anlamlı" sayılır.
SE_KATI = 2.0


def _kenar_yogunlugu(post, j: int) -> np.ndarray:
    m = np.asarray(post.marginal(j), dtype=np.float64)
    if m.ndim != 1 or len(m) < 2 or not np.all(np.isfinite(m)) or np.any(m < 0):
        raise ValueError(f"{j}. eksenin kenar dağılımı geçersiz")
    return m


def _cdf_parcali_dogrusal(f: np.ndarray, u: float) -> float:
    """Eşit aralıklı `[0,1]` düğümlerinde doğrusal yoğunluğun CDF'si."""
    n = len(f)
    d = 1.0 / (n - 1)
    parca = 0.5 * d * (f[:-1] + f[1:])          # her aralığın integrali
    toplam = float(parca.sum())
    if toplam <= 0.0:
        raise ValueError("kenar yoğunluğunun integrali sıfır")
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    k = min(int(u / d), n - 2)
    s = (u - k * d) / d
    ic = d * (s * f[k] + 0.5 * s * s * (f[k + 1] - f[k]))
    return float((parca[:k].sum() + ic) / toplam)


def pit_degeri(post, j: int, gercek: float) -> float:
    """`j`. eksende gerçeğin posterior CDF'deki yeri (doğal birimde `gercek`).

    Gerçek önsel aralığın dışındaysa `0` ya da `1` döner (kırpma **açıkça**:
    aralık dışı gerçek, zaten kalibre olamayan bir durumdur).
    """
    space = post.space
    x = np.array(space.from_unit(np.full((1, space.ndim), 0.5))[0], dtype=np.float64)
    x[j] = float(gercek)
    u = float(space.to_unit(x[None, :])[0, j])
    return _cdf_parcali_dogrusal(_kenar_yogunlugu(post, j), u)


def kapsama_egrisi(pit, seviyeler=SEVIYELER) -> list[dict]:
    """Merkezi aralıkların deneysel kapsaması (tek eksen PIT dizisi)."""
    pit = np.asarray(pit, dtype=np.float64).ravel()
    if pit.size == 0 or np.any(~np.isfinite(pit)):
        raise ValueError("PIT dizisi boş ya da sonlu değil")
    n = pit.size
    out = []
    for L in seviyeler:
        if not 0.0 < L < 1.0:
            raise ValueError(f"seviye (0,1) içinde olmalı, {L}")
        k = float(np.mean(np.abs(pit - 0.5) <= 0.5 * L))
        out.append({"nominal": float(L), "deneysel": k,
                    "se": float(np.sqrt(L * (1.0 - L) / n)), "n": n})
    return out


def ks_duzgunluk(pit) -> tuple[float, float]:
    """KS istatistiği `D` ve asimptotik `p` (Stephens düzeltmesiyle)."""
    x = np.sort(np.asarray(pit, dtype=np.float64).ravel())
    n = x.size
    if n == 0:
        raise ValueError("PIT dizisi boş")
    i = np.arange(1, n + 1)
    D = float(max(np.max(i / n - x), np.max(x - (i - 1) / n)))
    lam = (np.sqrt(n) + 0.12 + 0.11 / np.sqrt(n)) * D
    k = np.arange(1, 101)
    p = 2.0 * np.sum((-1.0) ** (k - 1) * np.exp(-2.0 * k * k * lam * lam))
    return D, float(min(max(p, 0.0), 1.0))


def pit_tanisi(pit) -> dict:
    """Tek eksen PIT dizisi → kapsama, KS ve **biçim** tanısı."""
    pit = np.asarray(pit, dtype=np.float64).ravel()
    n = pit.size
    kap = kapsama_egrisi(pit)
    k68 = next(k for k in kap if k["nominal"] == 0.68)
    D, p = ks_duzgunluk(pit)
    ort = float(pit.mean())
    se_ort = float(np.sqrt(1.0 / (12.0 * n)))
    bicim = []
    if k68["deneysel"] < 0.68 - SE_KATI * k68["se"]:
        bicim.append("ASIRI GUVENLI")
    if k68["deneysel"] > 0.68 + SE_KATI * k68["se"]:
        bicim.append("ASIRI TEMKINLI")
    if abs(ort - 0.5) > SE_KATI * se_ort:
        bicim.append("YANLI")
    if bicim:
        tani = " + ".join(bicim)
    elif p >= KS_ESIGI:
        tani = "KALIBRE"
    else:
        tani = "DUZGUN DEGIL"
    return {"tani": tani, "n": n, "kapsama": kap, "ks_D": D, "ks_p": p,
            "pit_ortalama": ort, "pit_ortalama_se": se_ort}


@dataclass(frozen=True)
class SBCSonuc:
    """SBC çıktısı: tekrar × eksen PIT'leri ve eksen başına tanı."""

    adlar: tuple
    pit: np.ndarray                      # (n_tekrar, d)
    gercekler: np.ndarray                # (n_tekrar, d) dogal birimde
    tanilar: list = field(default_factory=list)

    @property
    def genel(self) -> str:
        t = [d["tani"] for d in self.tanilar]
        return "KALIBRE" if all(x == "KALIBRE" for x in t) else \
            "KALIBRASYON DUSTU: " + ", ".join(
                f"{a}={x}" for a, x in zip(self.adlar, t, strict=True) if x != "KALIBRE")


def sbc_calistir(space, uret: Callable, cikarim: Callable, n_tekrar: int, *,
                 tohum: int) -> SBCSonuc:
    """Simülasyon tabanlı kalibrasyon döngüsü.

    Parameters
    ----------
    uret
        `uret(x, rng) -> veri`: doğal birimde `x` gerçeğiyle **gürültülü** veri.
        Gürültü modeli çıkarımınkiyle aynıysa ve vekil kusursuzsa PIT tam
        düzgündür; sapma çıkarımın (vekil, gürültü, model eksikliği) kusurudur.
    cikarim
        `cikarim(veri) -> GridPosterior`.
    tohum
        Belirlenimci tekrar için **zorunlu** (ADR-0004).
    """
    if n_tekrar < 10:
        raise ValueError(f"n_tekrar >= 10 olmali, {n_tekrar}")
    rng = np.random.default_rng(int(tohum))
    d = space.ndim
    pit = np.empty((n_tekrar, d))
    gercek = np.empty((n_tekrar, d))
    for r in range(n_tekrar):
        u = rng.random(d)
        x = space.from_unit(u[None, :])[0]
        post = cikarim(uret(x, rng))
        gercek[r] = x
        for j in range(d):
            pit[r, j] = pit_degeri(post, j, float(x[j]))
    tanilar = [pit_tanisi(pit[:, j]) for j in range(d)]
    return SBCSonuc(adlar=tuple(space.names), pit=pit, gercekler=gercek,
                    tanilar=tanilar)
