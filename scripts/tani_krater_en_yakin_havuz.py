"""TANI — `tarama="en_yakin"` üretim havuzunda (ADR-0064).

Üç tanım yan yana: `distan` (kilitli varsayılan), `icten` (ADR-0063),
`en_yakin` (ADR-0064). Sıfır GPU — yalnız kayıtlı `npz` okunur.

## ADR-0064 §3.3'ün KİLİTLİ ÖNGÖRÜSÜ

ADR-0064 (commit `7493db8`, **bu betikten önce**) `13` tek tanılı
noktanın her biri için sonucu `tani_krater_kesisim_sayisi.py`'nin
ölçtüğü kesişim yerlerinden **önceden** söylüyor. Burada o tablo
`ONGORU` sözlüğüne aynen alınıyor ve operatörün gerçek çıktısıyla
karşılaştırılıyor. Yani bu betik bir keşif değil, **ADR'nin sınavı**.

`REDDEDILIR` = ADR-0062'nin var olan kapısı yakalar (yüzey referansın
`2h` üzerinde) · `OLCULUR` = fiziksel olarak makul derinlik ·
`KACIYOR` = ADR-0064 §3.4, eşik konmadığı için hâlâ sayı veriyor.

## KAPILAR — koşudan önce kondu

1. **GERİ ALMA (ADR-0064 §5).** `distan`'ın ölçtüğü her noktada
   `en_yakin` aynı sayıyı `1e-9` bağıl farktan fazla değiştirmemeli.
   Değiştirirse kip **geri alınır** ve sebep KAYIT'a yazılır.
2. **KAYIP YOK.** `en_yakin`'in `OLCULDU` sayısı `distan`'ınkinin
   altına düşmemeli.
3. **ÖNGÖRÜ.** `13` noktanın tahmin tablosuyla uyumu yazılır. `13`'te
   en az `10` tutmazsa ADR-0064 §3.3 **çürütülmüş** sayılır.

> **MÜHÜRLÜ `uretim66` DEĞİŞTİRİLMEZ.** Bu betiğin sayıları yeni
> etiketle (`enyakin7x`) yayımlanır; `ONKAYIT_HERA_KRATER_uretim66`
> olduğu gibi kalır (ADR-0064 başlığındaki uyarı).

Kullanım:

    python scripts/tani_krater_en_yakin_havuz.py \\
        --kampanya <dizin> --tarama-csv <csv> --cikti <json>
"""
from __future__ import annotations

import argparse
import csv
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

N_NOKTA, TOHUM, I_Y0 = 96, 20260906, 1
YONLER = ("distan", "icten", "en_yakin")
#: ADR-0064 §3.3 tablosu, AYNEN. Bu betik calismadan once yazildi.
ONGORU = {
    6: "REDDEDILIR", 49: "REDDEDILIR", 24: "REDDEDILIR",
    0: "REDDEDILIR", 84: "REDDEDILIR", 85: "REDDEDILIR",
    52: "OLCULUR", 45: "OLCULUR", 25: "OLCULUR",
    14: "OLCULUR", 16: "OLCULUR", 19: "OLCULUR",
    87: "KACIYOR",
}
#: ONGORU kapisinin gecme esigi (docstring, kapi 3).
ONGORU_EN_AZ = 10
#: Geri alma kapisinin bagil fark esigi (ADR-0064 §5).
GERI_ALMA_ESIGI = 1e-9


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
                "d_merkez": float("nan"), "V_krater": float("nan"),
                "sebep": f"{type(e).__name__}: {e}"}
    return {"sinif": "OLCULDU", "d_merkez": float(k.derinlik_merkez),
            "V_krater": float(k.hacim), "sebep": "TAMAM"}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kampanya", required=True)
    p.add_argument("--tarama-csv", required=True)
    p.add_argument("--cikti", required=True)
    p.add_argument("--beklenen", type=int, default=N_NOKTA)
    a = p.parse_args()

    with open(a.tarama_csv, encoding="utf-8") as fh:
        kume = {int(r["kuresel"]): r["capraz_dogrulandi"]
                for r in csv.DictReader(fh)}
    if len(kume) != a.beklenen:
        raise SystemExit(f"KURAL 8: tarama CSV'de {a.beklenen} "
                         f"BEKLENIYORDU, {len(kume)} var")

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
            uz = np.max(np.abs(tasarim - th)
                        / np.maximum(np.abs(tasarim), 1e-30), axis=1)
            k = int(np.argmin(uz))
            if uz[k] > 1e-9 or k in gorulen:
                raise SystemExit(f"{os.path.basename(yol)}: theta "
                                 f"eslesmedi ya da tekrar ({k})")
            gorulen.add(k)
            satirlar.append({"kuresel": k, "Y0": float(th[I_Y0]),
                             "kume": kume[k],
                             **{y: _olc(d, y) for y in YONLER}})
    if len(satirlar) != a.beklenen:
        raise SystemExit(f"KURAL 8: {a.beklenen} BEKLENIYORDU, "
                         f"{len(satirlar)} okundu")
    satirlar.sort(key=lambda s: s["kuresel"])

    sayim = {}
    for y in YONLER:
        c: dict[str, int] = {}
        for s in satirlar:
            c[s[y]["sinif"]] = c.get(s[y]["sinif"], 0) + 1
        sayim[y] = dict(sorted(c.items()))

    # --- KAPI 1: GERI ALMA (ADR-0064 §5) -------------------------------
    bozan = []
    for s in satirlar:
        e, n = s["distan"], s["en_yakin"]
        if e["sinif"] != "OLCULDU":
            continue
        if n["sinif"] != "OLCULDU":
            bozan.append(f"nokta {s['kuresel']}: distan OLCULDU, "
                         f"en_yakin {n['sinif']}")
            continue
        payda = max(abs(e["d_merkez"]), 1e-9)
        bagil = abs(n["d_merkez"] - e["d_merkez"]) / payda
        if bagil > GERI_ALMA_ESIGI:
            bozan.append(f"nokta {s['kuresel']}: bagil fark {bagil:.3e}")
    geri_alma_gecti = not bozan

    # --- KAPI 2: KAYIP YOK ---------------------------------------------
    n_distan = sayim["distan"].get("OLCULDU", 0)
    n_enyakin = sayim["en_yakin"].get("OLCULDU", 0)
    kayip_yok = n_enyakin >= n_distan

    # --- KAPI 3: ADR-0064 §3.3'un ONGORUSU -----------------------------
    tutan, tutmayan = [], []
    for idx, bekleniyor in sorted(ONGORU.items()):
        s = next(q for q in satirlar if q["kuresel"] == idx)
        n = s["en_yakin"]
        if n["sinif"] != "OLCULDU":
            oldu = "REDDEDILIR"
        elif abs(n["d_merkez"]) > 20.0:
            # Savunulamayan buyukluk: ADR-0064 §3.4'un "KACIYOR" hali.
            oldu = "KACIYOR"
        else:
            oldu = "OLCULUR"
        (tutan if oldu == bekleniyor else tutmayan).append(
            {"idx": idx, "beklenen": bekleniyor, "olan": oldu,
             "d_merkez": n["d_merkez"], "sinif": n["sinif"]})
    ongoru_gecti = len(tutan) >= ONGORU_EN_AZ

    ozet = {
        "n": len(satirlar), "sayim": sayim,
        "KAPI1_geri_alma_gecti": geri_alma_gecti,
        "KAPI1_bozanlar": bozan[:20],
        "KAPI2_kayip_yok": bool(kayip_yok),
        "KAPI2_olculdu": {"distan": n_distan, "en_yakin": n_enyakin},
        "KAPI3_ongoru": f"{len(tutan)}/{len(ONGORU)}",
        "KAPI3_esik": ONGORU_EN_AZ,
        "KAPI3_gecti": bool(ongoru_gecti),
        "KAPI3_tutmayanlar": tutmayan,
        "YARGI": (
            "GERI ALINIR -- ADR-0064 §5 tetiklendi" if not geri_alma_gecti
            else ("KAYIP VAR -- en_yakin distan'dan az olcuyor"
                  if not kayip_yok
                  else ("ADR-0064 §3.3 DOGRULANDI" if ongoru_gecti
                        else "ADR-0064 §3.3 CURUTULDU"))),
        "MUHUR": "ONKAYIT_HERA_KRATER_uretim66 DEGISTIRILMEDI",
    }

    with open(a.cikti, "w", encoding="utf-8") as fh:
        json.dump({"ozet": ozet, "noktalar": satirlar}, fh, indent=2,
                  ensure_ascii=False)

    print(f"okunan: {len(satirlar)} / {a.beklenen}")
    for y in YONLER:
        print(f"  {y:<9} {sayim[y]}")
    print()
    print(f"KAPI1 geri alma (ADR-0064 §5): "
          f"{'GECTI' if geri_alma_gecti else 'DUSTU'}"
          f"{'' if geri_alma_gecti else '  -> ' + '; '.join(bozan[:3])}")
    print(f"KAPI2 kayip yok: {'GECTI' if kayip_yok else 'DUSTU'} "
          f"(distan {n_distan} -> en_yakin {n_enyakin})")
    print(f"KAPI3 ongoru: {len(tutan)}/{len(ONGORU)} tuttu "
          f"(esik {ONGORU_EN_AZ}) -> "
          f"{'GECTI' if ongoru_gecti else 'DUSTU'}")
    if tutmayan:
        print("  TUTMAYANLAR:")
        for t in tutmayan:
            print(f"    idx {t['idx']:>3}  beklenen {t['beklenen']:<11} "
                  f"olan {t['olan']:<11} d={t['d_merkez']:+.3f} "
                  f"({t['sinif']})")
    print()
    print(f"YARGI: {ozet['YARGI']}")
    print(f"MUHUR: {ozet['MUHUR']}")
    print()
    print("  13 TEK TANILI NOKTA -- uc tanim yan yana")
    print(f"  {'idx':>4} {'Y0':>9} {'distan':>14} {'icten':>12} "
          f"{'en_yakin':>12}")
    for s in satirlar:
        if s["kume"] != "HAYIR_tek_tani":
            continue

        def g(q):
            return (f"{q['d_merkez']:+.3f}" if q["sinif"] == "OLCULDU"
                    else q["sinif"])
        print(f"  {s['kuresel']:>4} {s['Y0']:>9.2f} "
              f"{g(s['distan']):>14} {g(s['icten']):>12} "
              f"{g(s['en_yakin']):>12}")
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
