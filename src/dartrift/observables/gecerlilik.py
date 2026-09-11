"""Sayısal geçerlilik ve fizik tanıları — **ayrı** kayıtlar (uzman Soru 11).

Uzman: *"İki ayrı denetim tutun. Sayısal geçerlilikte sonlu durum
değişkenleri, tamamlama, kütle/momentum/enerji, CFL ve kuvvet anındaki
kurucu sınırlar bulunmalı. Fizik tanılarında zirve basıncı/sıkışması,
aktarılmış impuls ve enerji bölüşümü bulunmalı. İkinci grubu ilk gruba
karıştırıp düzeltmenin fiziksel etkisini eleme gerekçesi yapmayın."*

Bu projede o karışıklık bir kez yaşandı (A68): son durumda okunan şok
kapısı, çekme kırpılınca maddenin **doğru** gevşediği kolu reddetti.

- :func:`sayisal_gecerlilik` — "bu koşunun sayıları sayısal olarak
  güvenilir mi". Her kontrolün değeri ve eşiği yazılır.
- :func:`fizik_tanilari` — "bu koşuda ne oldu". Kapı DEĞİL.

> Bu kayıtlar mevcut kilitli protokollerin yargısını değiştirmez;
> yeni kampanyalar hangi kontrolü kapı yapacağını protokolünde kilitler.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sayisal_gecerlilik", "fizik_tanilari", "kutle_agirlikli_yuzdelik",
           "ENERJI_BAYRAK_ESIGI", "AKMA_TAVANI"]

#: Toplam enerji sapması bayrağı. A77 ölçtü: `cfl = 0,25`'te 1 ms'de
#: `−%2,2`, 24 ms'de benzer; `%5` bu ölçülen düzeyin üstünde bir alarm.
ENERJI_BAYRAK_ESIGI = 0.05
#: Kuvvet anı `q/Y(P)` tavanı (Protokol J/L ile aynı).
AKMA_TAVANI = 1.0 + 1.0e-9


def kutle_agirlikli_yuzdelik(deger, kutle, yuzde: float) -> float:
    """Kütle ağırlıklı yüzdelik: kümülatif kütle `yuzde/100`'ü ilk aştığı değer."""
    d = np.asarray(deger, dtype=np.float64).ravel()
    w = np.asarray(kutle, dtype=np.float64).ravel()
    if len(d) == 0 or w.sum() <= 0.0:
        return float("nan")
    o = np.argsort(d, kind="stable")
    kum = np.cumsum(w[o]) / w.sum()
    return float(d[o][np.searchsorted(kum, yuzde / 100.0, side="left")])


def sayisal_gecerlilik(*, st: dict, t: float, t_end: float, enerji: dict,
                       akma_tani: dict, akma_kipi: str, defter: dict,
                       enerji_esigi: float = ENERJI_BAYRAK_ESIGI) -> dict:
    """Sayısal geçerlilik kaydı — kontroller, değerler, eşikler."""
    from .momentum_defteri import ARTIK_ESIGI

    sonlu = all(bool(np.all(np.isfinite(np.asarray(st[k]))))
                for k in ("x", "v", "u", "rho", "P", "S") if k in st)
    rho_min = float(np.min(np.asarray(st["rho"])))
    de = float(enerji.get("e_tot_bagil_sapma", float("nan")))
    oran = float(akma_tani.get("oran_max", float("nan"))) if akma_tani else float("nan")
    k = {
        "sonlu": sonlu,
        "tamamlandi": bool(t >= t_end * (1.0 - 1.0e-12)),
        "rho_pozitif": bool(rho_min > 0.0),
        "momentum_defteri": bool(defter.get("artik_bagil", np.inf) <= ARTIK_ESIGI),
        "enerji": bool(np.isfinite(de) and abs(de) <= enerji_esigi),
        # Kurucu sinir: `son` kipinde KUVVET ANINDA asim tasarim geregi var
        # (A72); kayit bunu DURUSTCE `False` yazar.
        "kurucu_sinir": bool(np.isfinite(oran) and oran <= AKMA_TAVANI)
        if akma_tani else True,
    }
    return {
        "gecerli": bool(all(k.values())),
        "kontroller": k,
        "degerler": {"t": float(t), "t_end": float(t_end), "rho_min": rho_min,
                     "momentum_artik_bagil": float(defter.get("artik_bagil", np.nan)),
                     "e_tot_bagil_sapma": de, "q_bolu_Y_max": oran,
                     "akma_kipi": str(akma_kipi)},
        "esikler": {"momentum": float(ARTIK_ESIGI), "enerji": float(enerji_esigi),
                    "akma": AKMA_TAVANI},
    }


def fizik_tanilari(*, rho_zirve, alpha0_hedef, m_hedef, defter: dict,
                   enerji: dict, impuls_egrisi: list | None = None,
                   rho0_kati: float = 2700.0) -> dict:
    """Fizik tanıları — KAPI DEĞİL.

    Tek parçacık maksimumuna ek olarak kütle ağırlıklı `p99` (uzman:
    *"Tek parçacık maksimumuna ek olarak ilgili hedef bölgesinde kütle
    ağırlıklı yüksek yüzdelik ve impuls zaman eğrisi izleyin."*).
    """
    sik = 100.0 * (np.asarray(rho_zirve, float) * np.asarray(alpha0_hedef, float)
                   / rho0_kati - 1.0)
    son = enerji.get("son", {})
    bas = enerji.get("bas", {})
    e0 = float(bas.get("e_tot", np.nan))
    return {
        "zirve_sikisma_max_yuzde": float(np.max(sik)) if len(sik) else float("nan"),
        "zirve_sikisma_p99_kutle_yuzde": kutle_agirlikli_yuzdelik(sik, m_hedef, 99.0),
        "zirve_sikisma_p90_kutle_yuzde": kutle_agirlikli_yuzdelik(sik, m_hedef, 90.0),
        "beta_hedef": float(defter.get("beta_hedef", np.nan)),
        "M_ejekta": float(defter.get("M_ejekta", np.nan)),
        "enerji_bolusumu": {"kinetik_kesri": float(son.get("e_kin", np.nan)) / e0,
                            "ic_kesri": float(son.get("e_int", np.nan)) / e0},
        "impuls_egrisi": impuls_egrisi or [],
    }
