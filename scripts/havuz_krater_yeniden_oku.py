"""Üretim havuzunun 96 noktasında krater gözlemlisini **yeniden oku**.

ADR-0061 (pencere durum başına) + ADR-0062 (örtülü krater reddi)
sonrası ölçüm. Sıfır GPU: yalnız kayıtlı `npz` durum dosyaları okunur.

## Niçin

KAYIT-088 havuzda **30/96** noktanın `nan` döndüğünü ve sebebinin
ortak pencere olduğunu ölçtü. KAYIT-089 düzeltmenin tek başına
yetmediğini ölçtü: `nan` kalkıyor ama yerine örtünün tepesi geliyor.
Bu betik, iki ADR birlikte uygulandıktan sonra havuzun **gerçekte** ne
verdiğini sayar.

## Kural 8 — beklediğini sayar

Betik `--beklenen` (varsayılan `96`) noktayı bekler. Eksik nokta
sessiz geçmez: tasarımla birebir eşleşme kurulamazsa **durur**.

## Geri alma koşulu (ADR-0061 §5, ADR-0062 §5)

`--onceki` ile eski bir çıktı verilirse, daha önce **pozitif** derinlik
okunan hiçbir noktanın `d_merkez`'i `%1`'den fazla değişmemeli ve
`nan` sayısı artmamalı. İhlal varsa betik **durur**.

Kullanım (TRUBA giriş düğümü, sıfır GPU):

    python scripts/havuz_krater_yeniden_oku.py \\
        --kampanya /arf/scratch/.../kampanya --cikti havuz_krater.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from gozlem_vektoru import gozlem_vektoru  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402

#: Havuz tasarımı — PROTOKOL-HAVUZ §3 ile aynı çağrı.
N_NOKTA = 96
TOHUM = 20260906
#: `θ = (α_b, Y₀, f)`; `Y₀` ikinci bileşen.
I_Y0 = 1


def _kuresel_indeks(th: np.ndarray, tasarim: np.ndarray, yol: str) -> int:
    """Küresel indeks dosya adından DEĞİL `theta`'dan gelir.

    Havuz her dilimdeki dört dosyayı da `nokta_0000_<hash>.npz` diye
    adlandırıyor; addaki sayı ayırt edici değil.
    """
    uz = np.max(np.abs(tasarim - th) / np.maximum(np.abs(tasarim), 1e-30),
                axis=1)
    k = int(np.argmin(uz))
    if uz[k] > 1e-9:
        raise SystemExit(
            f"{os.path.basename(yol)}: theta {th} kilitli tasarimda yok "
            f"(en yakin {k}, bagil {uz[k]:.3e})")
    return k


def havuzu_oku(kampanya: str, beklenen: int) -> list[dict]:
    tasarim = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA, root_seed=TOHUM),
                         dtype=np.float64)
    kullanilan: dict[int, str] = {}
    satirlar: list[dict] = []
    desen = os.path.join(kampanya, "HAVUZ_g1p0.dilim*_24.durumlar")
    dizinler = sorted(glob.glob(desen))
    if not dizinler:
        raise SystemExit(f"BOSLUK: {desen} hicbir dizine uymadi")
    for dizin in dizinler:
        if not re.search(r"dilim(\d+)_24", dizin):
            raise ValueError(f"dilim numarasi okunamadi: {dizin}")
        for yol in sorted(glob.glob(os.path.join(dizin, "nokta_*.npz"))):
            d = np.load(yol, allow_pickle=True)
            th = np.asarray(d["theta"], dtype=np.float64).ravel()
            k = _kuresel_indeks(th, tasarim, yol)
            if k in kullanilan:
                raise SystemExit(
                    f"AYNI tasarim noktasi iki dosyada: {k} -> "
                    f"{kullanilan[k]} ve {os.path.basename(yol)}")
            kullanilan[k] = os.path.basename(yol)

            sebepler: dict[str, str] = {}
            g = gozlem_vektoru(d, sebepler=sebepler)
            sebep = sebepler.get("krater", "YAZILMADI")
            satirlar.append({
                "kuresel": k, "dosya": os.path.basename(yol),
                "dilim": int(re.search(r"dilim(\d+)_24", dizin).group(1)),
                "theta": [float(q) for q in th],
                "Y0": float(th[I_Y0]),
                "krater_sebep": sebep,
                "sinif": _sinifla(sebep),
                "ortu_m": _ortu_metre(sebep),
                **{ad: float(g[ad]) for ad in
                   ("d_merkez", "d_max", "V_krater", "R_krater",
                    "dV_sikisma", "beta_hedef", "M_ejekta")},
            })
    if len(satirlar) != beklenen:
        raise SystemExit(
            f"KURAL 8: {beklenen} nokta BEKLENIYORDU, {len(satirlar)} "
            f"okundu. Eksik: {sorted(set(range(beklenen)) - set(kullanilan))}")
    satirlar.sort(key=lambda s: s["kuresel"])
    return satirlar


def _sinifla(sebep: str) -> str:
    if sebep == "TAMAM":
        return "OLCULDU"
    if "ORTULU KRATER" in sebep:
        return "ORTULU"
    if "bulunamadi" in sebep:
        return "YUZEY_YOK"
    return "BASKA"


def _ortu_metre(sebep: str) -> float:
    """`ORTULU KRATER` mesajından örtünün yüksekliğini çeker (m)."""
    m = re.search(r"son yuzey ([-\d.]+) m YUKARIDA", sebep)
    return float(m.group(1)) if m else float("nan")


def ozet(satirlar: list[dict]) -> dict:
    sinif: dict[str, list[int]] = {}
    for s in satirlar:
        sinif.setdefault(s["sinif"], []).append(s["kuresel"])
    o: dict = {"n": len(satirlar),
               "siniflar": {k: len(v) for k, v in sorted(sinif.items())},
               "indeksler": {k: sorted(v) for k, v in sorted(sinif.items())}}
    for ad in sinif:
        y = np.array([s["Y0"] for s in satirlar if s["sinif"] == ad])
        o.setdefault("Y0_araligi", {})[ad] = [float(y.min()), float(y.max())]
    olc = [s["d_merkez"] for s in satirlar if s["sinif"] == "OLCULDU"]
    if olc:
        o["d_merkez_OLCULDU"] = {
            "min": float(np.min(olc)), "max": float(np.max(olc)),
            "negatif": int(sum(1 for q in olc if q < 0.0))}
    ort = [s["ortu_m"] for s in satirlar if s["sinif"] == "ORTULU"]
    if ort:
        o["ortu_m"] = {"min": float(np.min(ort)), "max": float(np.max(ort)),
                       "ortanca": float(np.median(ort))}
    return o


def geri_alma_kapisi(satirlar: list[dict], onceki_yol: str) -> list[str]:
    """ADR-0061 §5 / ADR-0062 §5: eski pozitif okumalar korunmalı."""
    with open(onceki_yol, encoding="utf-8") as f:
        eski = {s["kuresel"]: s for s in json.load(f)["noktalar"]}
    yeni = {s["kuresel"]: s for s in satirlar}
    ihlal: list[str] = []
    eski_nan = sum(1 for s in eski.values() if s["sinif"] != "OLCULDU")
    yeni_nan = sum(1 for s in yeni.values() if s["sinif"] != "OLCULDU")
    if yeni_nan > eski_nan:
        ihlal.append(f"olculemeyen nokta ARTTI: {eski_nan} -> {yeni_nan}")
    for k, e in eski.items():
        if e["sinif"] != "OLCULDU" or not (e["d_merkez"] > 0.0):
            continue
        y = yeni.get(k)
        if y is None or y["sinif"] != "OLCULDU":
            ihlal.append(f"nokta {k}: pozitif okuma KAYBOLDU ({y and y['sinif']})")
            continue
        bagil = abs(y["d_merkez"] - e["d_merkez"]) / abs(e["d_merkez"])
        if bagil > 0.01:
            ihlal.append(
                f"nokta {k}: d_merkez {e['d_merkez']:.6f} -> "
                f"{y['d_merkez']:.6f} (bagil {bagil:.3%} > %1)")
    return ihlal


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kampanya", required=True)
    p.add_argument("--cikti", required=True)
    p.add_argument("--beklenen", type=int, default=N_NOKTA)
    p.add_argument("--onceki", default=None,
                   help="onceki cikti JSON'u; geri alma kapisini kosar")
    a = p.parse_args()

    satirlar = havuzu_oku(a.kampanya, a.beklenen)
    o = ozet(satirlar)

    ihlal: list[str] = []
    if a.onceki:
        ihlal = geri_alma_kapisi(satirlar, a.onceki)

    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump({"beklenen": a.beklenen, "ozet": o,
                   "geri_alma_ihlalleri": ihlal,
                   "noktalar": satirlar}, f, indent=2, ensure_ascii=False)

    print(f"okunan: {o['n']} / {a.beklenen}")
    for ad, n in o["siniflar"].items():
        ar = o["Y0_araligi"][ad]
        print(f"  {ad:10s} {n:3d}   Y0 {ar[0]:10.2f} .. {ar[1]:10.2f} Pa")
    if "d_merkez_OLCULDU" in o:
        q = o["d_merkez_OLCULDU"]
        print(f"  olculen d_merkez: {q['min']:+.4f} .. {q['max']:+.4f} m, "
              f"negatif {q['negatif']}")
    if "ortu_m" in o:
        q = o["ortu_m"]
        print(f"  ortu yuksekligi : {q['min']:.3f} .. {q['max']:.3f} m "
              f"(ortanca {q['ortanca']:.3f})")
    if ihlal:
        print("\nGERI ALMA KAPISI IHLAL EDILDI:")
        for s in ihlal:
            print("  -", s)
        raise SystemExit(1)
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
