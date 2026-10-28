"""TANI — SPH **birim bölünmesi** son durumda hâlâ geçerli mi?

SPH'in temel özdeşliği `Σ_j (m_j/ρ_j) W(|p − x_j|, h_j) ≈ 1`: cismin
**içinde** doluluk birdir. Krater operatörü (`krater_yuzey`) yüzeyi
`φ = 0,5` eş-yüzeyi olarak tanımlar ve bu tanım yalnız o özdeşlik
ayaktayken anlamlıdır.

## Niçin soruluyor

ADR-0061 → ADR-0063 zinciri krater okunamayan noktaları önce `nan`'dan
redde, sonra 46'dan 66'ya çıkardı; ama 13 nokta hâlâ savunulamayan
değer veriyordu (KAYIT-091 §7: idx 87'de `+36,49 m`). Eksende doluluk
profili basılınca sebep görüldü — ölçülen (2026-10-29, `10 m` adımla,
merkezden dışa):

| idx | `Y₀` (Pa) | son durumda `φ` |
|---:|---:|---|
| 1 | 58 708 | `0,94 0,98 1,05 0,90 1,14 1,17 0,34 0,00` |
| 2 | 1 266 | `0,94 0,98 1,04 0,89 1,18 1,14 0,36 0,01` |
| 6 | 5,76 | `0,86 0,67 0,65 **0,46 0,48** 0,77 0,74 0,59` |
| 87 | 1,35 | `0,82 0,72 0,60 **0,29** 1,33 **3,13** 1,80 1,00` |

Yani zayıf matriste `φ` cismin **içinde** `0,29`'a düşüyor ve `3,13`'e
çıkıyor. Orada bulunacak bir `φ = 0,5` yüzeyi **yok** — hangi yönden
tarandığından bağımsız olarak. Tarama yönü (ADR-0063) ya da
bağlantılılık ölçütü bu kusuru çözemez; ikisi de `φ`'nin anlamlı
olduğunu varsayar.

## Bu betik ne ölçer

Her noktada, **çarpma ekseni boyunca cismin içinde** `φ` örneklenir ve
referans durumla karşılaştırılır. Referans durum **denetimdir**:
çarpılmamış cisimde özdeşlik ayakta olmalı; olmazsa kusur operatörde
değil bu tanıda demektir.

İç bölge eşiksiz tanımlanır: referans durumda `φ`'nin eşiği kestiği
yarıçap bulunur, iç bölge onun **altındaki** örneklerdir.

Kullanım (sıfır GPU):

    python scripts/tani_doluluk_birim_bolunmesi.py \\
        --kampanya <dizin> --cikti tani_doluluk.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dartrift.cpu_reference.sph_ref import kernel_w  # noqa: E402
from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402

N_NOKTA, TOHUM = 96, 20260906
I_Y0 = 1
#: Gercek yogunluk (ADR-0022: gerilmesiz baslangic `2700/alpha0`).
RHO0_KATI = 2700.0
#: Eksen boyunca ornekleme adimi (m) -- cozunurlukten (h ~ 0,7) kucuk.
ADIM = 0.5


def _phi(X, V, h, c0, eksen, zq):
    d = X - c0[None, :]
    z = d @ eksen
    yan = d - z[:, None] * eksen[None, :]
    yan2 = np.einsum("ij,ij->i", yan, yan)
    sec = yan2 < (2.0 * h) ** 2
    if not np.any(sec):
        return np.full(len(zq), np.nan)
    zs, y2, Vs, hs = z[sec], yan2[sec], V[sec], h[sec]
    dz = zq[:, None] - zs[None, :]
    q = np.sqrt(dz * dz + y2[None, :]) / hs[None, :]
    return kernel_w(q, hs[None, :], 3) @ Vs


def _ic_sinir(zq, f_ref, esik=0.5):
    """Referans durumda `φ`'nin eşiği kestiği ilk yarıçap (içten dışa)."""
    alt = np.nonzero(f_ref < esik)[0]
    return float(zq[alt[0]]) if len(alt) else float(zq[-1])


def olc(yol, tasarim):
    d = np.load(yol, allow_pickle=True)
    th = np.asarray(d["theta"], dtype=np.float64).ravel()
    uz = np.max(np.abs(tasarim - th) / np.maximum(np.abs(tasarim), 1e-30),
                axis=1)
    k = int(np.argmin(uz))
    if uz[k] > 1e-9:
        raise SystemExit(f"{os.path.basename(yol)}: theta eslesmedi")

    hedef = np.asarray(d["mermi_kesri"]) < 0.5
    m = np.asarray(d["m"])[hedef]
    h = np.asarray(d["h"])[hedef]
    rho = np.asarray(d["rho"])[hedef]
    a0 = np.asarray(d["alpha0"])[hedef]
    x0 = np.asarray(d["x_referans"])[hedef]
    x = np.asarray(d["x"])[hedef]
    e = np.asarray(d["ehat"], dtype=np.float64)
    eksen = -e / np.linalg.norm(e)
    c0 = (m @ x0) / m.sum()
    R = float(np.max(np.linalg.norm(x0 - c0[None, :], axis=1)))
    zq = np.arange(0.0, R + ADIM, ADIM)

    f_ref = _phi(x0, m / (RHO0_KATI / a0), h, c0, eksen, zq)
    f_son = _phi(x, m / rho, h, c0, eksen, zq)
    sinir = _ic_sinir(zq, f_ref)
    ic = zq < sinir
    if int(ic.sum()) < 10:
        raise SystemExit(f"idx {k}: ic bolge {int(ic.sum())} ornek < 10")

    def ozet(f):
        g = f[ic]
        g = g[np.isfinite(g)]
        return {"n": int(g.size), "min": float(g.min()),
                "ortanca": float(np.median(g)), "maks": float(g.max()),
                "sapma": float(np.max(np.abs(g - 1.0)))}

    return {"kuresel": k, "Y0": float(th[I_Y0]),
            "theta": [float(q) for q in th],
            "ic_sinir_m": sinir, "R_m": R,
            "REF": ozet(f_ref), "SON": ozet(f_son)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kampanya", required=True)
    p.add_argument("--cikti", required=True)
    p.add_argument("--beklenen", type=int, default=N_NOKTA)
    a = p.parse_args()

    tasarim = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA, root_seed=TOHUM),
                         dtype=np.float64)
    desen = os.path.join(a.kampanya, "HAVUZ_g1p0.dilim*_24.durumlar")
    dizinler = sorted(glob.glob(desen))
    if not dizinler:
        raise SystemExit(f"BOSLUK: {desen} hicbir dizine uymadi")
    satirlar, gorulen = [], set()
    for dizin in dizinler:
        for yol in sorted(glob.glob(os.path.join(dizin, "nokta_*.npz"))):
            s = olc(yol, tasarim)
            if s["kuresel"] in gorulen:
                raise SystemExit(f"tekrar eden nokta: {s['kuresel']}")
            gorulen.add(s["kuresel"])
            satirlar.append(s)
    if len(satirlar) != a.beklenen:
        raise SystemExit(f"KURAL 8: {a.beklenen} BEKLENIYORDU, "
                         f"{len(satirlar)} okundu")
    satirlar.sort(key=lambda s: s["kuresel"])

    ref_sapma = np.array([s["REF"]["sapma"] for s in satirlar])
    son_sapma = np.array([s["SON"]["sapma"] for s in satirlar])
    y0 = np.array([s["Y0"] for s in satirlar])
    r = float(np.corrcoef(np.log10(y0), son_sapma)[0, 1])
    ozet = {
        "n": len(satirlar),
        "REF_sapma": {"ortanca": float(np.median(ref_sapma)),
                      "maks": float(ref_sapma.max())},
        "SON_sapma": {"ortanca": float(np.median(son_sapma)),
                      "maks": float(son_sapma.max())},
        "korelasyon_log10Y0_SON_sapma": r,
        "SON_min_phi": {"en_kucuk": float(min(s["SON"]["min"]
                                              for s in satirlar))},
        "SON_maks_phi": {"en_buyuk": float(max(s["SON"]["maks"]
                                               for s in satirlar))},
    }
    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump({"ozet": ozet, "noktalar": satirlar}, f, indent=2,
                  ensure_ascii=False)

    print(f"okunan: {len(satirlar)} / {a.beklenen}")
    print(f"REFERANS (denetim) |phi-1| sapmasi: ortanca "
          f"{ozet['REF_sapma']['ortanca']:.3f}, en buyuk "
          f"{ozet['REF_sapma']['maks']:.3f}")
    print(f"SON durum          |phi-1| sapmasi: ortanca "
          f"{ozet['SON_sapma']['ortanca']:.3f}, en buyuk "
          f"{ozet['SON_sapma']['maks']:.3f}")
    print(f"SON phi araligi: {ozet['SON_min_phi']['en_kucuk']:.3f} .. "
          f"{ozet['SON_maks_phi']['en_buyuk']:.3f}")
    print(f"r(log10 Y0, SON sapma) = {r:+.3f}")
    print()
    print("  idx   Y0(Pa)   REF sapma   SON sapma   SON phi min..maks")
    for s in sorted(satirlar, key=lambda q: q["Y0"])[:12]:
        print(f"  {s['kuresel']:3d} {s['Y0']:9.2f}   "
              f"{s['REF']['sapma']:9.3f}   {s['SON']['sapma']:9.3f}   "
              f"{s['SON']['min']:.3f} .. {s['SON']['maks']:.3f}")
    print("  ...")
    for s in sorted(satirlar, key=lambda q: q["Y0"])[-6:]:
        print(f"  {s['kuresel']:3d} {s['Y0']:9.2f}   "
              f"{s['REF']['sapma']:9.3f}   {s['SON']['sapma']:9.3f}   "
              f"{s['SON']['min']:.3f} .. {s['SON']['maks']:.3f}")
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
