"""G4-C: bilinen parametreler **geri bulunuyor mu**?

Eşikler [`docs/G4-OLCUTLERI.md`](../../../docs/G4-OLCUTLERI.md) §4'te
**ölçümden önce** sabitlendi ve burada tekrar yazılmıyor — oradan
okunuyor gibi davranmak yerine tek kaynak olarak bu modülde tanımlı
sabitlere bağlanıyor, ve bir test ikisinin tutarlılığını sınıyor.

| ölçüt | eşik | ne sınıyor |
|---|---|---|
| **C1** | 3/3 parametre `%68` bandında | temel doğruluk |
| **C2** | en az biri: bant < önselin `%50`'si | veri **bilgi taşıyor mu** |
| **C3** | gürültü artınca bant **genişlemeli** | çıkarım veriyi **kullanıyor mu** |

## C3 neden zorunlu — KAYIT-030'un dersi

Bir kurtarma "çalışıyor" görünebilir çünkü posterior **önselin
kendisidir**: bant gerçek değeri içerir (çünkü her şeyi içerir) ve
sonuç doğru sanılır. Gürültüye tepki vermeyen bir çıkarım hiçbir şey
öğrenmiyordur.

> Bu, KAYIT-030'da `np.interp`'in aralık dışını **kırpması** yüzünden
> uydurulmuş oranlar (1,60 / 1,14) üretmesiyle aynı sınıftır: çıktı
> makul göründü, üreten mekanizma bozuktu.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["G4C", "recovery_verdict", "C1_KAPSAMA", "C2_DARALMA",
           "C3_MONOTONLUK"]

#: C1: kaç parametrenin `%68` bandı gerçek değeri içermeli (hepsi).
C1_KAPSAMA = 1.0
#: C2: en az bir parametrenin bandı önselin bu kesrinden **dar** olmalı.
C2_DARALMA = 0.50
#: C3: gürültü artırıldığında bant genişlemesinde izin verilen **geri
#: adım** payı. Tam monotonluk sayısal gürültüde gerçekçi değil; `%2`'lik
#: bir daralma tolere edilir, daha fazlası tepkisizlik sayılır.
C3_MONOTONLUK = 0.02


@dataclass(frozen=True)
class G4C:
    """G4-C'nin üç sınavı ve **hangisinin** düştüğü."""

    c1_kapsama: float
    c1_gecti: bool
    c1_ayrinti: list = field(default_factory=list)

    c2_en_dar: float = float("nan")
    c2_gecti: bool = False
    c2_genislikler: list = field(default_factory=list)

    c3_gecti: bool = False
    c3_ayrinti: dict = field(default_factory=dict)
    c3_kosuldu: bool = False

    @property
    def gecti(self) -> bool:
        """**Üçü de** geçmeden G4-C geçilmez — kısmi geçiş yok."""
        return bool(self.c1_gecti and self.c2_gecti and self.c3_gecti)

    @property
    def ozet(self) -> str:
        d = []
        d.append(f"C1 kapsama {self.c1_kapsama:.0%} "
                 f"{'GECTI' if self.c1_gecti else 'DUSTU'}")
        d.append(f"C2 en dar bant {self.c2_en_dar:.3f} "
                 f"{'GECTI' if self.c2_gecti else 'DUSTU'}")
        if not self.c3_kosuldu:
            d.append("C3 KOSULMADI")
        else:
            d.append(f"C3 {'GECTI' if self.c3_gecti else 'DUSTU'}")
        return " | ".join(d)


def _bant_genislikleri(post) -> np.ndarray:
    return np.asarray(post.width_u, dtype=np.float64)


def recovery_verdict(post, gercek, gurultu_taramasi=None) -> G4C:
    """G4-C yargısı.

    Parameters
    ----------
    post
        Nominal gürültüdeki `GridPosterior`.
    gercek
        Gerçek parametre değerleri (doğal birimde), `space.names` sırasında.
    gurultu_taramasi
        `[(gürültü_çarpanı, GridPosterior), ...]` — **artan** çarpan
        sırasında. Verilmezse C3 **koşulmamış** sayılır ve yargı
        **geçemez** (sessizce atlanmaz).
    """
    space = post.space
    gercek = np.asarray(gercek, dtype=np.float64).ravel()
    if len(gercek) != space.ndim:
        raise ValueError(
            f"{len(gercek)} gerçek değer ama {space.ndim} parametre")

    # --- C1: her parametrenin %68 bandi gercegi iceriyor mu
    ayrinti = []
    icerenler = 0
    for j, ad in enumerate(space.names):
        lo, hi = post.hdi(j)
        var = bool(lo <= gercek[j] <= hi)
        icerenler += int(var)
        ayrinti.append({"ad": ad, "gercek": float(gercek[j]),
                        "bant": [float(lo), float(hi)], "iceriyor": var})
    kapsama = icerenler / space.ndim
    c1 = bool(kapsama >= C1_KAPSAMA)

    # --- C2: en az biri BILGILENDIRICI mi
    gen = _bant_genislikleri(post)
    onsel = space.prior_width()
    oran = gen / onsel
    c2 = bool(np.min(oran) < C2_DARALMA)

    # --- C3: gurultu artinca bant GENISLEMELI
    c3_kosuldu = gurultu_taramasi is not None and len(gurultu_taramasi) >= 2
    c3 = False
    c3_ayrinti: dict = {}
    if c3_kosuldu:
        carpanlar = [float(c) for c, _ in gurultu_taramasi]
        if list(carpanlar) != sorted(carpanlar):
            raise ValueError("gürültü taraması ARTAN çarpan sırasında olmalı")
        genislikler = np.array([_bant_genislikleri(p)
                                for _, p in gurultu_taramasi])
        # En bilgilendirici eksende (en dar bant) bakilir: bilgi tasimayan
        # bir eksende bant zaten onsel genisligindedir ve GENISLEYEMEZ --
        # orada monotonluk aramak olcutu bos birakirdi.
        j = int(np.argmin(oran))
        seri = genislikler[:, j]
        adimlar = np.diff(seri)
        # Genislemeli: her adim >= -tolerans*ilk_genislik
        tol = C3_MONOTONLUK * max(float(seri[0]), 1e-300)
        monoton = bool(np.all(adimlar >= -tol))
        # Ve TOPLAMDA gercekten genislemeli -- duz bir seri "monoton"dur
        # ama tepkisizdir.
        buyudu = bool(seri[-1] > seri[0] * (1.0 + C3_MONOTONLUK))
        c3 = bool(monoton and buyudu)
        c3_ayrinti = {"eksen": space.names[j], "carpanlar": carpanlar,
                      "genislikler": [float(v) for v in seri],
                      "monoton": monoton, "toplamda_buyudu": buyudu,
                      "buyume_orani": float(seri[-1] / max(seri[0], 1e-300))}

    return G4C(c1_kapsama=kapsama, c1_gecti=c1, c1_ayrinti=ayrinti,
               c2_en_dar=float(np.min(oran)), c2_gecti=c2,
               c2_genislikler=[float(v) for v in oran],
               c3_gecti=c3, c3_ayrinti=c3_ayrinti, c3_kosuldu=c3_kosuldu)
