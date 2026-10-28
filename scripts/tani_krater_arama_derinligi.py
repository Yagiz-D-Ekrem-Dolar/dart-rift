"""TANI (keşif): `arama_derinligi` havuzda neyi açıyor, neyi açmıyor.

**Bu betik kilitli operatörü DEĞİŞTİRMEZ.** `krater_yuzey`'in varsayılanı
`arama_derinligi = 10 m` olarak kalır; burada yalnızca *ölçülür*:
derinliği büyütmek hangi noktaları okunur hâle getirir, hangilerini
getirmez, ve okunur hâle gelenlerin değeri anlamlı mıdır.

## Niçin sorulması gerekiyor

ADR-0061 + ADR-0062 sonrası havuzda (2026-10-28, 96/96):

| sınıf | n | sebep |
|---|---:|---|
| `OLCULDU` | 46 | — |
| `ORTULU` | 25 | eksende **yoğun** bağlı ejekta (ADR-0062 reddi) |
| `YUZEY_YOK` | 25 | **SON** tarafı; pencere `82–118 m`'de, yüzey yok |

`YUZEY_YOK`'un **tamamı** son taraftan ve pencereleri referans yüzeyin
(`z ≈ 59,5 m`) çok yukarısında. Yani oralarda da bağlı malzeme var ama
`phi` eşiği kesmiyor — **seyrek** bulut. O hâlde bulutun *altındaki*
gerçek taban, pencere aşağı uzatılırsa görünebilir.

ADR-0062 §3 bunu *düzeltme* olarak **reddetti** ("sayı ayarlamak tanımı
düzeltmenin yerine geçmez"). Burada yapılan düzeltme değil **ölçüm**:
bulutun seyrek mi yoğun mu olduğunu ve tabanın erişilebilirliğini
sayıyla göstermek. Çıkan şey bir ADR'ye gerekçe olabilir; operatöre
doğrudan girmez.

## Kapı

Derinlik büyütülünce `ORTULU` sayısı **artmamalı**: yoğun bulut zaten
tepeden okunuyor, pencereyi uzatmak onu değiştirmemeli. Artarsa tarama
yan etki üretiyor demektir ve çıktıda işaretlenir.

Kullanım (sıfır GPU):

    python scripts/tani_krater_arama_derinligi.py \\
        --kampanya <dizin> --cikti tani.json --derinlikler 10 20 40 60
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


def _sinif(sebep: str) -> str:
    if sebep == "TAMAM":
        return "OLCULDU"
    if "ORTULU KRATER" in sebep:
        return "ORTULU"
    if "bulunamadi" in sebep:
        return "YUZEY_YOK"
    return "BASKA"


def _olc(d, derinlik: float) -> tuple[str, float, float]:
    """Döner: `(sınıf, d_merkez, V_krater)`."""
    try:
        k = krater_yuzey_durumdan(d, arama_derinligi=float(derinlik))
    except (KeyError, ValueError) as e:
        return _sinif(f"{type(e).__name__}: {e}"), float("nan"), float("nan")
    return "OLCULDU", float(k.derinlik_merkez), float(k.hacim)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kampanya", required=True)
    p.add_argument("--cikti", required=True)
    p.add_argument("--derinlikler", type=float, nargs="+",
                   default=[10.0, 20.0, 40.0, 60.0])
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
            s = {"kuresel": k, "Y0": float(th[I_Y0]), "olcum": {}}
            for der in a.derinlikler:
                sn, dm, vk = _olc(d, der)
                s["olcum"][f"{der:g}"] = {"sinif": sn, "d_merkez": dm,
                                          "V_krater": vk}
            satirlar.append(s)
    if len(satirlar) != a.beklenen:
        raise SystemExit(f"KURAL 8: {a.beklenen} BEKLENIYORDU, "
                         f"{len(satirlar)} okundu")
    satirlar.sort(key=lambda s: s["kuresel"])

    taban = f"{a.derinlikler[0]:g}"
    ozet: dict = {"derinlikler": [f"{q:g}" for q in a.derinlikler],
                  "sayim": {}, "gecisler": {}, "uyarilar": []}
    for der in ozet["derinlikler"]:
        c: dict[str, int] = {}
        for s in satirlar:
            c[s["olcum"][der]["sinif"]] = c.get(s["olcum"][der]["sinif"], 0) + 1
        ozet["sayim"][der] = c
    n_ortulu0 = ozet["sayim"][taban].get("ORTULU", 0)
    for der in ozet["derinlikler"][1:]:
        if ozet["sayim"][der].get("ORTULU", 0) > n_ortulu0:
            ozet["uyarilar"].append(
                f"derinlik {der}: ORTULU {n_ortulu0} -> "
                f"{ozet['sayim'][der]['ORTULU']} (KAPI: artmamaliydi)")
        gec: dict[str, int] = {}
        for s in satirlar:
            gec[f"{s['olcum'][taban]['sinif']}->{s['olcum'][der]['sinif']}"] = (
                gec.get(f"{s['olcum'][taban]['sinif']}->"
                        f"{s['olcum'][der]['sinif']}", 0) + 1)
        ozet["gecisler"][der] = dict(sorted(gec.items()))
    # Tabanda OLCULDU olan noktalar DEGISMEMELI (pencere yalniz uzuyor).
    for der in ozet["derinlikler"][1:]:
        for s in satirlar:
            e, y = s["olcum"][taban], s["olcum"][der]
            if e["sinif"] != "OLCULDU" or not np.isfinite(e["d_merkez"]):
                continue
            if y["sinif"] != "OLCULDU":
                ozet["uyarilar"].append(
                    f"nokta {s['kuresel']} derinlik {der}: OLCULDU kayboldu")
            elif abs(y["d_merkez"] - e["d_merkez"]) > 1e-9:
                ozet["uyarilar"].append(
                    f"nokta {s['kuresel']} derinlik {der}: d_merkez "
                    f"{e['d_merkez']:.6f} -> {y['d_merkez']:.6f}")

    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump({"ozet": ozet, "noktalar": satirlar}, f, indent=2,
                  ensure_ascii=False)

    print(f"okunan: {len(satirlar)} / {a.beklenen}")
    for der in ozet["derinlikler"]:
        print(f"  arama_derinligi {der:>4s} m : "
              + "  ".join(f"{k}={v}"
                          for k, v in sorted(ozet["sayim"][der].items())))
    print("\ngecisler (tabana gore):")
    for der, g in ozet["gecisler"].items():
        deg = {k: v for k, v in g.items() if k.split("->")[0] != k.split("->")[1]}
        print(f"  {der:>4s} m : {deg if deg else 'degisim YOK'}")
    if ozet["uyarilar"]:
        print("\nUYARILAR:")
        for u in ozet["uyarilar"][:20]:
            print("  -", u)
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
