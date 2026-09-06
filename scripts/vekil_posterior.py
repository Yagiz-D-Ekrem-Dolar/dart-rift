"""Vekil model + posterior — krater derinliğinden matris kohezyonu.

`G1` ölçtü (Protokol G, kilitli ölçüt): krater derinliği `θ`'yı ayırt
ediyor, `F = 1006`, `matris_Y0` ile `ρ = −0,9417` (`p < 0,0001`).
Diğer iki eksen anlamlı değil.

Bu betik zincirin son halkasını kuruyor:

    theta -> ileri model -> krater derinligi -> VEKIL -> POSTERIOR

## Neden sigmoid

Ölçülen ilişki **düz değil**; mukavemet rejimi geçişi gösteriyor:

    Y0 = 1,3e3 - 1e5 Pa   ->  d ~ 0,35 m   (PLATO, bilgi yok)
    Y0 = 3e5 - 9,3e6 Pa   ->  d 0,30 -> 0,081 m  (dik dusus)

Doğrusal uydurma `R² = 0,789`; ikinci derece `0,928`. Fiziksel biçim
bir **eşik**: kohezyon belirli bir değerin altındayken kazıyı
sınırlamıyor, üstünde sınırlıyor. Sigmoid o biçimi taşıyor ve
parametreleri **yorumlanabilir** (`x₀` = geçiş, `w` = keskinlik).

## Posteriorun okunması

Plato bölgesinde gözlenebilir `Y₀` hakkında **bilgi taşımıyor**;
orada posterior önselin kendisidir ve sınır **tek yanlıdır**
(`Y₀ < eşik`). Bu bir kusur değil, ölçülen fiziğin sonucu — ve
raporda öyle bildiriliyor.

Kullanim:
    python scripts/vekil_posterior.py --durumlar A.durumlar B.durumlar \\
        --gozlem 0.25 --gozlem-sigma 0.02
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

#: `θ₁` (matris `Y₀`) önseli — ADR-0044 S3 uzayının sınırları.
#: Posterior bu aralıkta tanımlı; dışına taşan olasılık YOK.
ONSEL_LOG10_ALT = 3.0
ONSEL_LOG10_UST = 7.0

#: Posterior "tek yanlı" sayılır: kütlenin bu kesri üst (ya da alt)
#: sınıra dayanıyorsa iki yanlı güven aralığı bildirilmez.
TEK_YANLI_ESIGI = 0.10


def sigmoid_model(x, d_alt, d_ust, x0, w):
    """`d(x) = d_alt + (d_ust − d_alt) / (1 + exp((x − x0)/w))`.

    `x = log10(Y0)`. `w > 0` iken azalan: yüksek `Y₀` → sığ krater.
    """
    return d_alt + (d_ust - d_alt) / (1.0 + np.exp((x - x0) / w))


def _kal(p, x, d):
    return sigmoid_model(x, *p) - d


def uydur(x, d, *, tohum: int = 0) -> dict:
    """Sigmoid uydurma — scipy'siz, Levenberg-Marquardt yerine ızgara + inis."""
    x = np.asarray(x, float)
    d = np.asarray(d, float)
    rng = np.random.default_rng(tohum)

    # Kaba izgara: fiziksel olarak makul baslangiclar
    en_iyi, en_iyi_p = np.inf, None
    for d_alt in np.linspace(d.min() - 0.05, d.min() + 0.05, 5):
        for d_ust in np.linspace(d.max() - 0.05, d.max() + 0.05, 5):
            for x0 in np.linspace(x.min(), x.max(), 15):
                for w in (0.1, 0.2, 0.4, 0.8, 1.5):
                    p = np.array([d_alt, d_ust, x0, w])
                    s = float((_kal(p, x, d) ** 2).sum())
                    if s < en_iyi:
                        en_iyi, en_iyi_p = s, p

    # Nelder-Mead benzeri basit inis (bagimsizlik icin elle)
    p = en_iyi_p.copy()
    adim = np.array([0.02, 0.02, 0.2, 0.1])
    for _ in range(4000):
        gelisti = False
        for j in range(4):
            for isaret in (+1.0, -1.0):
                q = p.copy()
                q[j] += isaret * adim[j]
                if q[3] <= 1e-3:
                    continue
                s = float((_kal(q, x, d) ** 2).sum())
                if s < en_iyi:
                    en_iyi, p, gelisti = s, q, True
        if not gelisti:
            adim *= 0.5
            if adim.max() < 1e-6:
                break
    kal = _kal(p, x, d)
    R2 = 1.0 - float((kal ** 2).sum()) / float(((d - d.mean()) ** 2).sum())
    return {
        "p": p.tolist(),
        "d_alt": float(p[0]), "d_ust": float(p[1]),
        "x0": float(p[2]), "w": float(p[3]),
        "artik_sigma": float(kal.std(ddof=4)) if len(x) > 4 else float("nan"),
        "R2": float(R2),
    }


def posterior(vekil: dict, d_gozlem: float, sigma: float, *,
              n: int = 4001) -> dict:
    """`p(log10 Y₀ | d)` — düz önsel, Gauss olabilirlik."""
    x = np.linspace(ONSEL_LOG10_ALT, ONSEL_LOG10_UST, n)
    mu = sigmoid_model(x, *vekil["p"])
    # Toplam belirsizlik: gozlem + vekil artigi (bagimsiz varsayimi)
    s2 = sigma ** 2 + (vekil["artik_sigma"] ** 2
                       if np.isfinite(vekil["artik_sigma"]) else 0.0)
    logL = -0.5 * (d_gozlem - mu) ** 2 / s2
    p = np.exp(logL - logL.max())
    p /= np.trapezoid(p, x) if hasattr(np, "trapezoid") else np.trapz(p, x)
    kum = np.concatenate([[0.0], np.cumsum(0.5 * (p[1:] + p[:-1]) * np.diff(x))])
    kum /= kum[-1]

    def q(u):
        return float(np.interp(u, kum, x))

    ust_pay = float(1.0 - kum[np.searchsorted(x, ONSEL_LOG10_UST - 0.05)])
    alt_pay = float(kum[np.searchsorted(x, ONSEL_LOG10_ALT + 0.05)])
    q16, q84 = q(0.16), q(0.84)

    # TEK YANLI olcusu: posteriorun %68 araliginin BIR UCU onsel
    # sinirina DAYANIYOR mu.
    #
    # Ilk yazdigim olcu "siniri asan olasilik kutlesi" idi ve YANLISTI:
    # platoda posterior sinira YIGILMIYOR, genis bir bolgeye YAYILIYOR
    # (model orada duz oldugu icin olabilirlik de duz). Sinavla
    # yakalandi -- `test_platoda_TEK_YANLI_diyor` dustu.
    onsel_genislik = ONSEL_LOG10_UST - ONSEL_LOG10_ALT
    alt_dayali = (q16 - ONSEL_LOG10_ALT) < TEK_YANLI_ESIGI * onsel_genislik
    ust_dayali = (ONSEL_LOG10_UST - q84) < TEK_YANLI_ESIGI * onsel_genislik
    return {
        "MAP": float(x[int(np.argmax(p))]),
        "medyan": q(0.5),
        "q16": q16, "q84": q84,
        "q025": q(0.025), "q975": q(0.975),
        "ust_sinira_yigilma": ust_pay,
        "alt_sinira_yigilma": alt_pay,
        # Posteriorun onsele gore ne kadar daraldigini soyler.
        # 1'e yakinsa gozlem BILGI TASIMIYOR demektir.
        "bilgi_orani": float((q84 - q16) / (0.68 * onsel_genislik)),
        "alt_sinira_dayali": bool(alt_dayali),
        "ust_sinira_dayali": bool(ust_dayali),
        "tek_yanli": bool(alt_dayali or ust_dayali),
        "toplam_sigma": float(np.sqrt(s2)),
    }


def birak_bir_dogrula(x, d, *, tohum: int = 0) -> dict:
    """Birini dışarıda bırak — vekil gerçekten öngörüyor mu."""
    hata, z = [], []
    for i in range(len(x)):
        k = np.ones(len(x), bool)
        k[i] = False
        v = uydur(x[k], d[k], tohum=tohum)
        tahmin = float(sigmoid_model(x[i], *v["p"]))
        hata.append(tahmin - d[i])
        s = v["artik_sigma"]
        if np.isfinite(s) and s > 0:
            z.append((tahmin - d[i]) / s)
    hata = np.asarray(hata)
    z = np.asarray(z)
    return {
        "n": len(hata),
        "RMSE": float(np.sqrt((hata ** 2).mean())),
        "yanlilik": float(hata.mean()),
        "z_sapma": float(z.std(ddof=1)) if len(z) > 1 else float("nan"),
        "kapsama_1sigma": float((np.abs(z) < 1.0).mean()) if len(z) else float("nan"),
    }


def _tohum_ayikla(ad: str) -> str:
    """Dizin adından sahne tohumunu çıkar: `...sahne99991111.dilim1_3...`.

    Dizin sayısı **gerçeklem sayısı değildir**: `3` dilim × `2` tohum
    = `6` dizin ama `2` gerçeklem. Dilimler AYRI `θ` alt kümeleri
    taşıdığı için hepsini kesiştirmek BOŞ küme veriyordu.
    """
    import re

    m = re.search(r"sahne(\d+)", ad)
    return m.group(1) if m else ad


def _veri(dizinler) -> tuple:
    """`durumlar` dizinlerinden `(log10 Y0, krater, gerceklem_sapmasi)`.

    Dizinler **sahne tohumuna göre gruplanır**; her grup bir
    gerçeklemdir. Gruplar içinde dilimler birleştirilir, gruplar
    arasında `θ` kesiştirilir.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ayirt_raporu import _krater, _oku

    gruplar: dict[str, dict] = {}
    for dz in dizinler:
        t = _tohum_ayikla(str(dz))
        hedef = gruplar.setdefault(t, {})
        for k, z in _oku(Path(dz)):
            hedef[tuple(np.round(k["theta"], 12))] = _krater(z)
    if not gruplar:
        raise SystemExit("durumlar bos")
    kollar = [gruplar[t] for t in sorted(gruplar)]
    ortak = sorted(set(kollar[0]).intersection(*[set(k) for k in kollar[1:]]))
    if not ortak:
        raise SystemExit(
            f"gerceklemler arasinda ORTAK theta yok "
            f"({len(gruplar)} tohum: {sorted(gruplar)})")
    th = np.array(ortak)
    D = np.array([[k[t] for t in ortak] for k in kollar])
    sapma = (D.std(axis=0, ddof=1) if len(D) > 1
             else np.zeros(len(ortak)))
    return np.log10(th[:, 1]), D.mean(axis=0), sapma


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--durumlar", nargs="+", required=True)
    ap.add_argument("--gozlem", type=float, default=None,
                    help="olculen krater derinligi (m)")
    ap.add_argument("--gozlem-sigma", type=float, default=0.02)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    x, d, gur = _veri(a.durumlar)
    print("=" * 70)
    n_toh = len({_tohum_ayikla(str(z)) for z in a.durumlar})
    print(f"VEKIL MODEL  ({len(x)} nokta, {n_toh} gerceklem, "
          f"{len(a.durumlar)} dizin)")
    print("=" * 70)
    print(f"  log10 Y0 : {x.min():.3f} .. {x.max():.3f}")
    print(f"  krater   : {d.min():.4f} .. {d.max():.4f} m")
    print(f"  gerceklem gurultusu (medyan) : {np.median(gur):.5f} m")

    v = uydur(x, d)
    print(f"\n  d(x) = d_alt + (d_ust - d_alt) / (1 + exp((x - x0)/w))")
    print(f"    d_alt = {v['d_alt']:.4f} m    (yuksek Y0 siniri)")
    print(f"    d_ust = {v['d_ust']:.4f} m    (dusuk Y0 PLATOSU)")
    print(f"    x0    = {v['x0']:.3f}         (gecis: Y0 = {10**v['x0']:.3g} Pa)")
    print(f"    w     = {v['w']:.3f}          (keskinlik, dekad)")
    print(f"    R^2   = {v['R2']:.4f}   artik sigma = {v['artik_sigma']:.5f} m")

    lo = birak_bir_dogrula(x, d)
    print(f"\n  BIRINI DISARIDA BIRAK ({lo['n']} kat)")
    print(f"    RMSE       = {lo['RMSE']:.5f} m")
    print(f"    yanlilik   = {lo['yanlilik']:+.5f} m")
    print(f"    z sapmasi  = {lo['z_sapma']:.3f}   (1,0 beklenir)")
    print(f"    1-sigma kapsama = {lo['kapsama_1sigma']:.3f}  (0,68 beklenir)")

    cikti = {"vekil": v, "birak_bir": lo,
             "n": int(len(x)), "gerceklem": n_toh,
             "dizin": len(a.durumlar)}

    if a.gozlem is not None:
        po = posterior(v, a.gozlem, a.gozlem_sigma)
        cikti["posterior"] = po
        cikti["gozlem"] = {"d": a.gozlem, "sigma": a.gozlem_sigma}
        print("\n" + "=" * 70)
        print(f"POSTERIOR   d_gozlem = {a.gozlem:.4f} +/- {a.gozlem_sigma:.4f} m")
        print("=" * 70)
        print(f"  toplam sigma (gozlem + vekil) : {po['toplam_sigma']:.5f} m")
        print(f"  MAP     log10 Y0 = {po['MAP']:.3f}   (Y0 = {10**po['MAP']:.3g} Pa)")
        print(f"  medyan  log10 Y0 = {po['medyan']:.3f}")
        print(f"  %68 : [{po['q16']:.3f}, {po['q84']:.3f}]  "
              f"-> Y0 = [{10**po['q16']:.3g}, {10**po['q84']:.3g}] Pa")
        print(f"  %95 : [{po['q025']:.3f}, {po['q975']:.3f}]")
        print(f"  sinira yigilma: alt {po['alt_sinira_yigilma']:.3f}  "
              f"ust {po['ust_sinira_yigilma']:.3f}")
        if po["tek_yanli"]:
            print("\n  >> TEK YANLI: gozlem PLATO bolgesinde; gozlenebilir")
            print("     Y0 hakkinda yalniz TEK YANLI sinir veriyor.")
            print("     Iki yanli guven araligi bildirilmemeli.")
        else:
            print("\n  >> IKI YANLI sinir gecerli.")

    if a.json:
        a.json.write_text(json.dumps(cikti, indent=2), encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
