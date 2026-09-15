"""GPU-saat sayımı — `sacct` çıktısından iş adı başına harcanan GPU-saati.

Projenin şimdiye kadar kaç GPU-saat harcadığı hiçbir yerde toplu kayıtlı
değildi (2026-09-15). TRUBA'da `sacct` çıktısı alınıp burada toplanır.

Dikkat (sessiz iki kat sayım): Slurm `AllocTRES` aynı GPU'yu hem türsüz
(`gres/gpu=1`) hem türlü (`gres/gpu:h100=1`) yazabilir. Türsüz varsa o
alınır; yoksa türlüler toplanır. İş adımları (`123.batch`) atlanır — süreleri
ana işin içinde. İptal edilen ama koşmuş işler de sayılır (GPU tuttular).

Kullanim (TRUBA):
    sacct -X -P -n -S 2026-07-01 -o JobID,JobName,Elapsed,AllocTRES,State > sacct.txt
Kullanim (yerel):
    python scripts/gpu_saat.py sacct.txt
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_TURSUZ = re.compile(r"(?:^|,)gres/gpu=(\d+)")
_TURLU = re.compile(r"(?:^|,)gres/gpu:[A-Za-z0-9_.-]+=(\d+)")


def sure_saat(elapsed: str) -> float:
    """Slurm `Elapsed`: `[G-]SS:DD:ss` ya da `DD:ss` → saat."""
    s, gun = elapsed.strip(), 0
    if "-" in s:
        g, s = s.split("-", 1)
        gun = int(g)
    p = [float(x) for x in s.split(":")]
    if len(p) == 3:
        sa, dk, sn = p
    elif len(p) == 2:
        sa, (dk, sn) = 0.0, p
    else:
        raise ValueError(f"tanimsiz Elapsed: {elapsed!r}")
    return gun * 24 + sa + dk / 60 + sn / 3600


def gpu_sayisi(tres: str) -> int:
    t = _TURSUZ.findall(tres or "")
    if t:
        return sum(int(x) for x in t)
    return sum(int(x) for x in _TURLU.findall(tres or ""))


def topla(satirlar) -> dict:
    ad_basina: dict[str, float] = {}
    n_is = 0
    for s in satirlar:
        p = s.rstrip("\n").split("|")
        if len(p) < 5 or not p[0] or "." in p[0]:
            continue
        ad, elapsed, tres = p[1], p[2], p[3]
        gs = gpu_sayisi(tres) * sure_saat(elapsed)
        ad_basina[ad] = ad_basina.get(ad, 0.0) + gs
        n_is += 1
    return {"toplam": sum(ad_basina.values()), "n_is": n_is,
            "ad_basina": dict(sorted(ad_basina.items(), key=lambda x: -x[1]))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sacct", type=Path, help="sacct -X -P -n ... ciktisi")
    a = ap.parse_args(argv)
    r = topla(a.sacct.read_text(encoding="utf-8", errors="replace").splitlines())
    for ad, gs in r["ad_basina"].items():
        if gs > 0:
            print(f"  {ad:<16} {gs:10.1f} GPU-sa")
    print(f"TOPLAM: {r['toplam']:.1f} GPU-saat ({r['n_is']} is)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
