"""TANI — üretim havuzunda ejekta üssü `μ` **uydurulabiliyor mu**?

## Niçin

`README.md` S6 *"GEÇTİ: `μ = 0,463 ± 0,016`; H&H `0,40 – 0,55`"* diyor.
Ama o sayı **mekanizma çalışmasından** geliyor (`SONUC-E-F-MEKANIZMA`
§ "sekiz uydurma bandı"), üretim havuzundan değil. Aynı belge o dönemin
üretim kolu için şunu da yazıyor: *"Üretim kolunda dağılım **yok** —
`12` eşikte `3` farklı kütle değeri (basamak fonksiyonu)."*

Bugünkü üretim `--matris-cekme-yok` kullanıyor, yani çekmesi kırpılmış
kolun **ailesinden**; dolayısıyla o eski cümle bugünkü havuza
uygulanmayabilir. **Ama kimse bakmadı.**

Bu önemli, çünkü literatür karşılaştırması (`LITERATUR...` §11.4) bizim
`0,463`'ümüzü L1'in `0,36 – 0,39`'uyla yan yana koyuyor. İkisi aynı
yapılandırmadan gelmiyorsa o karşılaştırma **yanıltıcıdır**.

## Ne ölçülür

Her havuz noktasında, hedef malzemesinin dışa hareket eden kısmı için
`M(>v)` kümülatif kütle–hız dağılımı kurulur (kutulama yok,
`ejecta_catalog.cumulative_mass_velocity`) ve `SONUC-E-F`'in **aynı
sekiz bandında** `log M = a + b·log v` uydurulur; `μ = −b/3`.

İki ayrı şey raporlanır ve **karıştırılmaz**:

1. **Uydurulabilirlik:** banttaki farklı kütle değeri sayısı ve `R²`.
   `SONUC-E-F`'in basamak-fonksiyonu uyarısı tam bu sayıyla ölçülür.
2. **Değer:** uydurulabilen noktalarda `μ` dağılımı.

## Kapı — koşudan ÖNCE

- **Uydurulabilirlik eşiği:** bir bant ancak `≥ 8` farklı kütle değeri
  **ve** `R² ≥ 0,99` ile uydurulmuş sayılır (`SONUC-E-F` her bantta
  `R² > 0,993` bildirmişti; `12` eşikte `3` değer *basamak* sayılmıştı).
- **Yargı:** havuzun **yarısından azında** hiçbir bant uydurulamıyorsa
  *"üretim havuzunda `μ` ölçülemez"* yazılır ve S6'nın sayısının
  **üretimi temsil etmediği** kaydedilir.

Bu bir **keşiftir**; S6'nın kilitli tablosuna dokunulmaz.

Kullanım (sıfır GPU):

    python scripts/tani_mu_havuz.py --kampanya <dizin> --cikti mu.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.observables.ejecta_catalog import (  # noqa: E402
    cumulative_mass_velocity,
)

N_NOKTA, TOHUM = 96, 20260906
#: `SONUC-E-F-MEKANIZMA` ile AYNI sekiz bant (m/s).
BANTLAR = ((1.0, 100.0), (1.0, 50.0), (2.0, 100.0), (1.0, 200.0),
           (0.5, 100.0), (2.0, 50.0), (5.0, 100.0), (1.0, 20.0))
#: Uydurulabilirlik kapisi -- docstring'de, kosudan once.
EN_AZ_FARKLI = 8
EN_AZ_R2 = 0.99


def _mu_bant(vb, mc, lo, hi) -> dict:
    s = (vb >= lo) & (vb <= hi) & (mc > 0.0)
    n_farkli = int(np.unique(mc[s]).size)
    if int(s.sum()) < 3 or n_farkli < 2:
        return {"n_farkli": n_farkli, "mu": None, "r2": None}
    x, y = np.log(vb[s]), np.log(mc[s])
    b, a = np.polyfit(x, y, 1)
    yy = a + b * x
    ss_res = float(np.sum((y - yy) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"n_farkli": n_farkli, "mu": float(-b / 3.0), "r2": float(r2)}


def olc(yol, tasarim) -> dict:
    d = np.load(yol, allow_pickle=True)
    th = np.asarray(d["theta"], dtype=np.float64).ravel()
    uz = np.max(np.abs(tasarim - th) / np.maximum(np.abs(tasarim), 1e-30),
                axis=1)
    k = int(np.argmin(uz))
    if uz[k] > 1e-9:
        raise SystemExit(f"{os.path.basename(yol)}: theta eslesmedi")

    hedef = np.asarray(d["mermi_kesri"]) < 0.5
    x = np.asarray(d["x"])[hedef]
    v = np.asarray(d["v"])[hedef]
    m = np.asarray(d["m"])[hedef]
    x0 = np.asarray(d["x_referans"])[hedef]
    c0 = (m @ x0) / m.sum()
    dr = x - c0[None, :]
    r = np.linalg.norm(dr, axis=1)
    # DISA hareket eden madde (SONUC-E-F'in tanimi: radyal hiz > 0).
    vr = np.einsum("ij,ij->i", v, dr / np.maximum(r[:, None], 1e-30))
    disa = vr > 0.0
    if int(disa.sum()) < 10:
        return {"kuresel": k, "Y0": float(th[1]), "n_disa": int(disa.sum()),
                "bantlar": {}, "uydurulan": 0}
    vb, mc = cumulative_mass_velocity(vr[disa], m[disa])
    bant = {f"{lo}-{hi}": _mu_bant(vb, mc, lo, hi) for lo, hi in BANTLAR}
    uyan = [b["mu"] for b in bant.values()
            if b["mu"] is not None and b["n_farkli"] >= EN_AZ_FARKLI
            and b["r2"] is not None and b["r2"] >= EN_AZ_R2]
    return {"kuresel": k, "Y0": float(th[1]), "n_disa": int(disa.sum()),
            "bantlar": bant, "uydurulan": len(uyan),
            "mu_ortanca": float(np.median(uyan)) if uyan else None}


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
    satir, gorulen = [], set()
    for dizin in dizinler:
        for yol in sorted(glob.glob(os.path.join(dizin, "nokta_*.npz"))):
            s = olc(yol, tasarim)
            if s["kuresel"] in gorulen:
                raise SystemExit(f"tekrar eden nokta: {s['kuresel']}")
            gorulen.add(s["kuresel"])
            satir.append(s)
    if len(satir) != a.beklenen:
        raise SystemExit(f"KURAL 8: {a.beklenen} BEKLENIYORDU, "
                         f"{len(satir)} okundu")
    satir.sort(key=lambda s: s["kuresel"])

    uyan_n = np.array([s["uydurulan"] for s in satir])
    mus = [s["mu_ortanca"] for s in satir if s["mu_ortanca"] is not None]
    farkli = np.array([max((b["n_farkli"] for b in s["bantlar"].values()),
                           default=0) for s in satir])
    oran = float((uyan_n > 0).mean())
    olculebilir = oran >= 0.5

    ozet = {
        "n": len(satir),
        "uydurulabilen_nokta": int((uyan_n > 0).sum()),
        "uydurulabilen_oran": oran,
        "bant_basina_uyan_ortanca": float(np.median(uyan_n)),
        "en_cok_farkli_kutle_degeri": {
            "ortanca": float(np.median(farkli)),
            "min": int(farkli.min()), "maks": int(farkli.max()),
        },
        "mu": ({"ortanca": float(np.median(mus)), "min": float(min(mus)),
                "maks": float(max(mus)), "n": len(mus)} if mus else None),
        "kapi": {"en_az_farkli": EN_AZ_FARKLI, "en_az_r2": EN_AZ_R2},
        "YARGI": ("URETIM HAVUZUNDA mu OLCULEBILIR" if olculebilir else
                  "URETIM HAVUZUNDA mu OLCULEMEZ -- S6'nin sayisi "
                  "uretimi TEMSIL ETMIYOR"),
        "NOT": ("KESIF. S6'nin kilitli tablosuna ve SONUC-E-F'in "
                "mekanizma olcumune DOKUNULMADI."),
    }
    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump({"ozet": ozet, "noktalar": satir}, f, indent=2,
                  ensure_ascii=False)

    print("=" * 68)
    print("EJEKTA USSU mu -- URETIM HAVUZU  (KESIF)")
    print("=" * 68)
    print(f"okunan: {len(satir)} / {a.beklenen}")
    print(f"uydurulabilen nokta: {ozet['uydurulabilen_nokta']}/{len(satir)}"
          f"  (oran {oran:.3f})")
    f2 = ozet["en_cok_farkli_kutle_degeri"]
    print(f"bant basina en cok FARKLI kutle degeri: ortanca "
          f"{f2['ortanca']:.1f}  ({f2['min']} .. {f2['maks']})")
    print(f"  kapi: >= {EN_AZ_FARKLI} farkli deger VE R2 >= {EN_AZ_R2}")
    if ozet["mu"]:
        mm = ozet["mu"]
        print(f"mu (uydurulabilen {mm['n']} noktada): ortanca "
              f"{mm['ortanca']:.4f}   {mm['min']:.4f} .. {mm['maks']:.4f}")
        print("  karsilastirma: S6 (mekanizma kolu) 0,463 +- 0,016; "
              "L1 (Raducan & Jutzi 2022) 0,36 - 0,39; H&H 0,40 - 0,55")
    else:
        print("mu: hicbir noktada uydurulamadi")
    print()
    print(f"YARGI: {ozet['YARGI']}")
    print(f"NOT  : {ozet['NOT']}")
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
