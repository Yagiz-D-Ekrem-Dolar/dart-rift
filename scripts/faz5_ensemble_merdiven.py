"""FAZ 5 — **merdivenli** ensemble sürücüsü.

## Neden yeni bir sürücü

Önceki ensemble (`faz46_g4c_hazir_ensemble.py`) şokun hiç oluşmadığı
bir rejimde koştu. Ölçüldü (rapor A19): `G4-C`'nin `q2 = 0,907`'lik
korelasyonu **taban artığından** geliyordu; gerçek sinyalin `q2`'si
**`-0,33`**. Yani vekil eğitildi ama anlamsız bir gözlenebilir
üzerine.

Bu sürücü üç şeyi düzeltiyor:

| | eski | **yeni** |
|---|---|---|
| çözünürlük | tek basamak, şok yok | **merdiven** (`%45,18` sıkışma) |
| şok denetimi | yok | **ADR-0049 kapısı** — geçmeyen nokta `nan` |
| krater ölçüsü | mutlak yarıçap (taban artıklı) | Lagrange'cı yer değiştirme |

## Kaldığı yerden devam

`ensemble_kos` JSONL'i satır satır yazıyor ve tamamlanmış noktaları
atlıyor. Bir SLURM işi kesilse bile ilerleme **kaybolmaz**; iş
yeniden gönderilir ve kaldığı yerden sürer.

## Maliyet

Ölçüldü (`2026-08-31`): merdiven `N ≈ 76 700`, `t_end = 0,2 s` için
`27 429` adım -> H100'de **`~4,3 saat/nokta`**. `40` nokta seri
`~7 gün`, `20` GPU paralel **`~9 saat`**.
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
sys.path.insert(0, str(REPO / "scripts"))

from faz48_iki_asama import SAHNE, _mat  # noqa: E402

from dartrift.inference.design import (  # noqa: E402
    DART_UZAYI,
    factorial_design,
    lhs_design,
)
from dartrift.inference.ensemble import ensemble_kos  # noqa: E402
from dartrift.inference.forward import (  # noqa: E402
    GOZLENEBILIRLER,
    ileri_kosu_merdiven,
)

#: A25/A26 ile dogrulanmis merdiven -- METRE cinsinden, DISTAN ICE.
MERDIVEN = ("48:2.8", "24:1.4", "12:0.7", "6:0.35", "3:0.175")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-lhs", type=int, default=32,
                    help="Latin hiperkup nokta sayisi (kenarlar ayrica)")
    ap.add_argument("--kenarlar", action="store_true",
                    help="tam carpanli kenar noktalarini da ekle")
    ap.add_argument("--t-end", type=float, default=0.2)
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--root-seed", type=int, default=None)
    ap.add_argument("--sok-kapisi-kapali", action="store_true",
                    help="TANI AMACLI: ADR-0049 kapisini kapat")
    ap.add_argument("--out", required=True, help="JSONL yolu")
    a = ap.parse_args()

    kok = int(SAHNE["root_seed"]) if a.root_seed is None else a.root_seed
    tasarim = lhs_design(DART_UZAYI, a.n_lhs, root_seed=kok)
    if a.kenarlar:
        tasarim = np.vstack([factorial_design(DART_UZAYI, levels=2), tasarim])

    print("=" * 78, flush=True)
    print("FAZ 5 — MERDIVENLI ENSEMBLE", flush=True)
    print("=" * 78, flush=True)
    print(f"  uzay        : {DART_UZAYI.names}", flush=True)
    print(f"  nokta       : {len(tasarim)}  (lhs {a.n_lhs}"
          f"{' + kenarlar' if a.kenarlar else ''})", flush=True)
    print(f"  merdiven    : {' '.join(MERDIVEN)}  (metre)", flush=True)
    print(f"  t_end       : {a.t_end} s", flush=True)
    print(f"  sok kapisi  : {'KAPALI (TANI)' if a.sok_kapisi_kapali else 'ACIK'}",
          flush=True)
    print(f"  gozlenebilir: {GOZLENEBILIRLER}", flush=True)
    print(f"  root_seed   : {kok}", flush=True)

    t0 = time.perf_counter()

    def _ilerleme(i, n, mesaj):
        print(f"    [{i + 1:>3}/{n}] {mesaj}  "
              f"({time.perf_counter() - t0:.0f} s)", flush=True)

    def _ileri(theta):
        y = ileri_kosu_merdiven(
            np.atleast_2d(theta), material=_mat(), device=a.device,
            t_end=a.t_end, kademeler=MERDIVEN, spacing=a.spacing,
            sahne_taban=None, sok_yargisi=not a.sok_kapisi_kapali)[0]
        if not np.all(np.isfinite(y)):
            raise RuntimeError(f"nokta okunamadi: {y}")
        return y

    durum = ensemble_kos(tasarim, _ileri, Path(a.out), root_seed=kok,
                         ilerleme=_ilerleme)
    print(f"\n  tamamlanan : {durum.n_tamam}/{len(tasarim)}", flush=True)
    print(f"  dusen      : {durum.n_dusen}", flush=True)
    print(f"  duvar      : {time.perf_counter() - t0:.0f} s", flush=True)
    ozet = Path(a.out).with_suffix(".ozet.json")
    ozet.write_text(json.dumps({
        "n_nokta": int(durum.toplam), "n_tamam": int(durum.tamamlanan),
        "n_dusen": int(durum.dusen), "n_atlanan": int(durum.atlanan),
        "n_bozuk_satir": int(durum.bozuk_satir),
        "merdiven": list(MERDIVEN),
        "t_end": a.t_end, "spacing": a.spacing, "root_seed": kok,
        "sok_kapisi": not a.sok_kapisi_kapali,
        "gozlenebilirler": list(GOZLENEBILIRLER),
        "duvar_s": time.perf_counter() - t0,
    }, indent=2))
    print(f"\nyazildi: {a.out}  ve  {ozet}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
