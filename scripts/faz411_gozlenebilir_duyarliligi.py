"""FAZ 4.11 — gözlenebilirler parametrelere **duyarlı mı**?

FAZ 4.6'nın yaşam sorusu. Bir gözlenebilir `θ` değişince değişmiyorsa
çıkarıma sıfır bilgi taşır; üçü birden değişmiyorsa FAZ 4.6 hiç
koşmamalı.

## Neden şimdi sorulabiliyor

`β` iki bağımsız koşuda **bit düzeyinde aynı** çıktı:

| kaynak | `t` | `β` |
|---|---|---|
| KAYIT-045 üç seviyeli | 0,2 s | `1.4112162721355217` |
| uzun koşu (41 örnek) | 0,127 → 5,0 s | `1.4112162721355217` |

`β`, `t = 0,2`'de ne ise `5,0`'da da o. Yani ensemble `t_end = 0,2`'de
koşabilir — **25 kat ucuz** — ve bu deney saatler değil dakikalar sürer.

## Ölçüt — **veriye bakmadan** yazıldı

Her gözlenebilir için tasarım noktaları üzerindeki yayılım:

    bagil = (max - min) / |ortalama|

| bağıl yayılım | yargı |
|---|---|
| tam `0` (özdeş) | **ÖLÜ** — çıkarıma giremez |
| `< 1%` | **ZAYIF** — bayrakla geç |
| `>= 1%` | **KULLANILABILIR** |

> `%1` bir **çalışma eşiği**, fizikten türetilmedi. Doğrusu gözlem
> belirsizliğidir (Hera'nın çap/`β` hatası) ve o sayı ADR-0045'in
> 3. eksik ölçümü — **girilmedi**. Eşik o girilince değişmeli; şimdi
> değiştirmek veriye uydurmak olur.

## Bu betik `ileri_kosu_ikiasama`'yı **ilk kez** koşturuyor

O fonksiyonun GPU yolu bugüne kadar hiçbir koşuda çalışmadı. Düşen
nokta `nan` döner ve **atlanmaz**; kaç nokta düştüğü raporlanır.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402
from dartrift.inference.forward import (GOZLENEBILIRLER,  # noqa: E402
                                        ileri_kosu_ikiasama)

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402
from faz48_iki_asama import T1_OLCULEN  # noqa: E402

#: Önceden yazılmış eşik; gerekçesi modül belgesinde.
ZAYIF_ESIGI = 0.01


def koseler(uzay, kac: int) -> np.ndarray:
    """`kac` tasarım noktası: köşeler + merkez.

    Köşeler seçilir çünkü duyarlılık **en büyük** oradadır: köşelerde
    fark yoksa içeride hiç yoktur.
    """
    lo = np.asarray(uzay.lo, dtype=np.float64)
    hi = np.asarray(uzay.hi, dtype=np.float64)
    n = len(lo)
    tum = []
    for k in range(2 ** n):
        bit = [(k >> j) & 1 for j in range(n)]
        tum.append([hi[j] if bit[j] else lo[j] for j in range(n)])
    merkez = [(np.sqrt(lo[j] * hi[j]) if uzay.log[j]
               else 0.5 * (lo[j] + hi[j])) for j in range(n)]
    hepsi = np.array(tum + [merkez], dtype=np.float64)
    return hepsi[:kac] if kac < len(hepsi) else hepsi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--t-end", type=float, default=0.2)
    ap.add_argument("--nokta", type=int, default=9)
    ap.add_argument("--out", default=str(Path.home() / "faz411.json"))
    a = ap.parse_args()

    uzay = DART_UZAYI_S3
    X = koseler(uzay, a.nokta)
    print("=" * 78, flush=True)
    print(f"FAZ 4.11 — GOZLENEBILIR DUYARLILIGI  ({len(X)} nokta, "
          f"t_end={a.t_end})", flush=True)
    print(f"uzay: {uzay.names}", flush=True)
    print("=" * 78, flush=True)
    for i, th in enumerate(X):
        print(f"  {i}: " + "  ".join(f"{ad}={v:.4g}"
                                     for ad, v in zip(uzay.names, th)),
              flush=True)

    t0 = time.perf_counter()

    def ilerleme(i, n, mesaj):
        print(f"  [{i + 1}/{n}] {mesaj}  "
              f"({time.perf_counter() - t0:.0f} s)", flush=True)

    Y = ileri_kosu_ikiasama(
        X, material=_malzeme(), device=a.device, t1=T1_OLCULEN,
        t_end=a.t_end, r1=3.0, lam1=19.0, r2=25.0, lam2=2.0,
        spacing=7.0, sahne_taban=SAHNE, ilerleme=ilerleme)

    dusen = int(np.count_nonzero(~np.isfinite(Y).all(axis=1)))
    print(f"\n{'=' * 78}", flush=True)
    print(f"SONUC  ({time.perf_counter() - t0:.0f} s duvar, "
          f"{dusen}/{len(X)} nokta DUSTU)", flush=True)
    print("=" * 78, flush=True)

    yargilar = {}
    print(f"\n{'gozlenebilir':>20} {'min':>14} {'max':>14} "
          f"{'bagil yayilim':>14} {'yargi':>16}", flush=True)
    print("-" * 84, flush=True)
    for j, ad in enumerate(GOZLENEBILIRLER):
        s = Y[:, j][np.isfinite(Y[:, j])]
        if len(s) < 2:
            yargilar[ad] = "olculemedi"
            print(f"{ad:>20} {'--':>14} {'--':>14} {'--':>14} "
                  f"{'OLCULEMEDI':>16}", flush=True)
            continue
        ort = float(np.mean(s))
        bagil = float((s.max() - s.min()) / max(abs(ort), 1e-300))
        if s.max() == s.min():
            y = "OLU"
        elif bagil < ZAYIF_ESIGI:
            y = "ZAYIF"
        else:
            y = "KULLANILABILIR"
        yargilar[ad] = y
        print(f"{ad:>20} {s.min():14.6g} {s.max():14.6g} "
              f"{bagil:14.3e} {y:>16}", flush=True)

    olu = [k for k, v in yargilar.items() if v in ("OLU", "olculemedi")]
    print(f"\n{'=' * 78}", flush=True)
    if len(olu) == len(GOZLENEBILIRLER):
        print("SONUC: UC GOZLENEBILIR DE OLU -> FAZ 4.6 KOSULMAMALI.",
              flush=True)
    elif olu:
        print(f"SONUC: {olu} olu; kalanla devam edilebilir ama C1 "
              f"(3/3 kapsama) DUSER.", flush=True)
    else:
        print("SONUC: ucu de degisiyor -> FAZ 4.6 kosulabilir.", flush=True)

    Path(a.out).write_text(json.dumps(
        {"uzay": list(uzay.names), "t_end": a.t_end,
         "X": X.tolist(), "Y": Y.tolist(),
         "gozlenebilirler": list(GOZLENEBILIRLER),
         "yargilar": yargilar, "dusen": dusen,
         "zayif_esigi": ZAYIF_ESIGI,
         "duvar_s": time.perf_counter() - t0}, indent=2), encoding="utf-8")
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
