"""TANI (keşif): `tarama = "distan"` vs `"icten"` — üretim havuzunda.

**Kilitli varsayılanı DEĞİŞTİRMEZ.** `krater_yuzey`'in varsayılanı
`"distan"` olarak kalır; burada iki tanım 96 nokta üzerinde yan yana
*ölçülür* ve ADR-0063'ün gerekçesi sayıya bağlanır.

## Sınanan iddia

`"icten"` bir ayar değil bir tanımsa, iki şey birden tutmalı:

1. **Örtüsüz noktalarda eski ölçümü yeniden üretmeli.** Yani
   `distan`'ın `OLCULDU` dediği 46 noktada `d_merkez` değişmemeli.
   Sentetikte `%0`'a kadar tuttu (`+0,9216` ↔ `+0,9216`).
2. **Örtülü noktalarda sayı vermeli** — çünkü üstteki yığını yapısal
   olarak ıskalar.

İkisinden biri tutmazsa çıktı bunu ayrı ayrı yazar; "iyi sonuç"
seçilmez.

## Kapılar

- `distan`'da `OLCULDU` olan nokta `icten`'de kaybolursa → uyarı.
- `distan`'da `OLCULDU` olan noktanın `d_merkez`'i `> %1` oynarsa →
  uyarı (sayıyla).

Kullanım (sıfır GPU):

    python scripts/tani_krater_tarama_yonu.py \\
        --kampanya <dizin> --cikti tani_yon.json
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
from dartrift.observables.crater_shape import (  # noqa: E402
    krater_yuzey_durumdan,
)

N_NOKTA = 96
TOHUM = 20260906
I_Y0 = 1
YONLER = ("distan", "icten")


def _sinif(sebep: str) -> str:
    if sebep == "TAMAM":
        return "OLCULDU"
    if "ORTULU KRATER" in sebep:
        return "ORTULU"
    if "bulunamadi" in sebep:
        return "YUZEY_YOK"
    return "BASKA"


def _olc(d, yon: str) -> dict:
    try:
        k = krater_yuzey_durumdan(d, tarama=yon)
    except (KeyError, ValueError) as e:
        return {"sinif": _sinif(f"{type(e).__name__}: {e}"),
                "d_merkez": float("nan"), "d_max": float("nan"),
                "V_krater": float("nan"), "R_krater": float("nan"),
                "sebep": f"{type(e).__name__}: {e}"}
    return {"sinif": "OLCULDU", "d_merkez": float(k.derinlik_merkez),
            "d_max": float(k.derinlik), "V_krater": float(k.hacim),
            "R_krater": float(k.yaricap), "sebep": "TAMAM"}


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

    satirlar: list[dict] = []
    gorulen: set[int] = set()
    for dizin in dizinler:
        for yol in sorted(glob.glob(os.path.join(dizin, "nokta_*.npz"))):
            d = np.load(yol, allow_pickle=True)
            th = np.asarray(d["theta"], dtype=np.float64).ravel()
            uz = np.max(np.abs(tasarim - th) / np.maximum(np.abs(tasarim),
                                                          1e-30), axis=1)
            k = int(np.argmin(uz))
            if uz[k] > 1e-9 or k in gorulen:
                raise SystemExit(f"{os.path.basename(yol)}: theta eslesmedi "
                                 f"ya da tekrar ({k})")
            gorulen.add(k)
            satirlar.append({"kuresel": k, "Y0": float(th[I_Y0]),
                             "theta": [float(q) for q in th],
                             **{y: _olc(d, y) for y in YONLER}})
    if len(satirlar) != a.beklenen:
        raise SystemExit(f"KURAL 8: {a.beklenen} BEKLENIYORDU, "
                         f"{len(satirlar)} okundu")
    satirlar.sort(key=lambda s: s["kuresel"])

    ozet: dict = {"sayim": {}, "gecisler": {}, "uyarilar": [],
                  "kurtarilan": [], "fark": {}}
    for y in YONLER:
        c: dict[str, int] = {}
        for s in satirlar:
            c[s[y]["sinif"]] = c.get(s[y]["sinif"], 0) + 1
        ozet["sayim"][y] = dict(sorted(c.items()))
    gec: dict[str, int] = {}
    for s in satirlar:
        anahtar = f"{s['distan']['sinif']}->{s['icten']['sinif']}"
        gec[anahtar] = gec.get(anahtar, 0) + 1
    ozet["gecisler"] = dict(sorted(gec.items()))

    # 1. KAPI: distan'da olculen noktalar korunuyor mu, degeri ayni mi?
    farklar = []
    for s in satirlar:
        e, i = s["distan"], s["icten"]
        if e["sinif"] != "OLCULDU":
            continue
        if i["sinif"] != "OLCULDU":
            ozet["uyarilar"].append(
                f"nokta {s['kuresel']}: distan OLCULDU, icten "
                f"{i['sinif']} ({i['sebep'][:70]})")
            continue
        payda = max(abs(e["d_merkez"]), 1e-9)
        bagil = abs(i["d_merkez"] - e["d_merkez"]) / payda
        farklar.append(bagil)
        if bagil > 0.01:
            ozet["uyarilar"].append(
                f"nokta {s['kuresel']}: d_merkez {e['d_merkez']:.6f} -> "
                f"{i['d_merkez']:.6f} (bagil {bagil:.3%})")
    if farklar:
        ozet["fark"] = {"n": len(farklar), "ortanca": float(np.median(farklar)),
                        "en_buyuk": float(np.max(farklar))}
    # 2. distan'da REDDEDILEN kac nokta icten'de okunuyor?
    for s in satirlar:
        if s["distan"]["sinif"] != "OLCULDU" and s["icten"]["sinif"] == "OLCULDU":
            ozet["kurtarilan"].append(
                {"kuresel": s["kuresel"], "Y0": s["Y0"],
                 "distan": s["distan"]["sinif"],
                 "d_merkez": s["icten"]["d_merkez"],
                 "V_krater": s["icten"]["V_krater"]})

    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump({"ozet": ozet, "noktalar": satirlar}, f, indent=2,
                  ensure_ascii=False)

    print(f"okunan: {len(satirlar)} / {a.beklenen}")
    for y in YONLER:
        print(f"  {y:7s}: " + "  ".join(f"{k}={v}"
                                        for k, v in ozet["sayim"][y].items()))
    print("\ngecisler (distan -> icten):")
    for k, v in ozet["gecisler"].items():
        print(f"  {k:26s} {v:3d}")
    if ozet["fark"]:
        q = ozet["fark"]
        print(f"\ndistan'da OLCULEN {q['n']} noktada bagil fark: "
              f"ortanca {q['ortanca']:.3e}, en buyuk {q['en_buyuk']:.3e}")
    kur = ozet["kurtarilan"]
    print(f"\nicten'de KURTARILAN nokta: {len(kur)}")
    if kur:
        dm = [q["d_merkez"] for q in kur]
        print(f"  d_merkez: {min(dm):+.4f} .. {max(dm):+.4f} m, "
              f"negatif {sum(1 for q in dm if q < 0)}")
        y0 = [q["Y0"] for q in kur]
        print(f"  Y0      : {min(y0):.2f} .. {max(y0):.2f} Pa")
    if ozet["uyarilar"]:
        print("\nUYARILAR:")
        for u in ozet["uyarilar"][:20]:
            print("  -", u)
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
