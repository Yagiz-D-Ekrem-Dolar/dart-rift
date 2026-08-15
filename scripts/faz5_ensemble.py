"""FAZ 5 — üretim ensemble'ı, **kaldığı yerden devam eden**.

`ileri_kosu_ikiasama`'yı `ensemble_kos` sürücüsüne bağlar. İkisi de
vardı ama **birbirine bağlı değildi**: sürücü `faz46`'nın **tek
aşamalı** modeline takılıydı ve o model KAYIT-045'e göre başka bir
problemi çözüyor (`n_ejekta = 803`, mermi tamamen sekiyor).

## Kesinti bir olasılık değil, **zorunluluk**

Ölçülen maliyet (H100, iki aşamalı, nokta başına):

| `t_end` | nokta | 300 nokta |
|---|---|---|
| 0,2 s | `33 s` | **2,75 saat** |
| 200 s | `~4 saat` | **~50 GPU-günü** |

`kolyoz-cuda`'nın duvar sınırı `3` gün. `t_end` uzunsa ensemble
**tek işe sığmaz** ve devam edebilmek şart. Sürücü tamamlanmış
noktaları `JSONL`'den okuyup atlıyor.

## Düşen nokta **tekrar denenmez**

Varsayılan `yeniden_dene_dusenleri = False`: aynı parametre aynı
şekilde düşer ve GPU boşa gider. Düşme nedeni düzeltildikten **sonra**
`--yeniden-dene` ile açılır.

## Her noktanın durumu **diske yazılır**

Bu turda üç kez kaydedilmiş duruma ihtiyaç duyuldu ve elde yalnızca
özet vardı. Yeni bir gözlenebilir sorusu **koşu gerektirmemeli**.
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

from dartrift.inference.design import (DART_UZAYI_S3,  # noqa: E402
                                       factorial_design, lhs_design)
from dartrift.inference.ensemble import ensemble_kos  # noqa: E402
from dartrift.inference.forward import (GOZLENEBILIRLER,  # noqa: E402
                                        ileri_kosu_ikiasama)

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402
from faz48_iki_asama import T1_OLCULEN  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--t-end", type=float, required=True,
                    help="FAZ 5 ON KOSULU'nun sonucundan secilir")
    ap.add_argument("--n-lhs", type=int, default=273,
                    help="27 kose + bu kadar LHS (varsayilan 300 nokta)")
    ap.add_argument("--root-seed", type=int, default=20260811)
    ap.add_argument("--jsonl", default=str(Path.home() / "faz5_ensemble.jsonl"))
    ap.add_argument("--durum-dizin", default=str(Path.home() / "faz5_durumlar"))
    ap.add_argument("--yeniden-dene", action="store_true")
    ap.add_argument("--azami-adim", type=int, default=2500000)
    a = ap.parse_args()

    uzay = DART_UZAYI_S3
    X = np.vstack([factorial_design(uzay, 3),
                   lhs_design(uzay, a.n_lhs, root_seed=a.root_seed)])
    dz = Path(a.durum_dizin); dz.mkdir(parents=True, exist_ok=True)

    print("=" * 78, flush=True)
    print(f"FAZ 5 ENSEMBLE — {len(X)} nokta, t_end={a.t_end} s", flush=True)
    print(f"uzay: {uzay.names}", flush=True)
    print(f"gozlenebilirler: {GOZLENEBILIRLER}", flush=True)
    print(f"iz: {a.jsonl}", flush=True)
    print("=" * 78, flush=True)

    t0 = time.perf_counter()

    def ileri(th: np.ndarray) -> np.ndarray:
        """Tek nokta; düşerse **hata atar** (sürücü onu `null` yazar)."""
        Y = ileri_kosu_ikiasama(
            np.asarray(th, dtype=np.float64)[None, :],
            material=_malzeme(), device=a.device, t1=T1_OLCULEN,
            t_end=a.t_end, r1=3.0, lam1=19.0, r2=25.0, lam2=2.0,
            spacing=7.0, sahne_taban=SAHNE, azami_adim=a.azami_adim,
            durum_kaydi=_kaydet)
        y = np.asarray(Y)[0]
        if not np.all(np.isfinite(y)):
            # Surucu `null` yazsin diye HATA atiliyor: sessizce `nan`
            # dondurmek noktayi "tamamlandi" gosterirdi.
            raise RuntimeError(f"nokta dustu, y = {y}")
        return y

    sayac = {"i": 0}

    def _kaydet(_j, th, st, sahne, x_ref, a1):
        yol = dz / f"nokta_{sayac['i']:04d}.npz"
        np.savez_compressed(
            yol, x=st["x"], v=st["v"], m=st["m"], x_referans=x_ref,
            hedef=~np.asarray(sahne.is_impactor, dtype=bool),
            theta=np.asarray(th), R=float(a1.target_radius),
            M=float(a1.target_mass),
            p_imp=np.asarray(a1.impactor_momentum),
            d_imp=np.asarray(a1.impact_direction), t_end=a.t_end)

    def ilerleme(i, n, mesaj):
        sayac["i"] = i
        gecen = time.perf_counter() - t0
        print(f"  [{i + 1}/{n}] {mesaj}  ({gecen:.0f} s)", flush=True)

    d = ensemble_kos(X, ileri, a.jsonl, root_seed=a.root_seed,
                     ilerleme=ilerleme,
                     yeniden_dene_dusenleri=a.yeniden_dene)

    print(f"\n{'=' * 78}", flush=True)
    print(f"tamamlanan={d.tamamlanan}  dusen={d.dusen}  "
          f"atlanan={d.atlanan}  duvar={time.perf_counter() - t0:.0f} s",
          flush=True)
    ozet = Path(a.jsonl).with_suffix(".ozet.json")
    ozet.write_text(json.dumps({
        "uzay": list(uzay.names), "gozlenebilirler": list(GOZLENEBILIRLER),
        "t_end": a.t_end, "n_nokta": int(len(X)),
        "root_seed": a.root_seed,
        "tamamlanan": int(d.tamamlanan), "dusen": int(d.dusen),
        "atlanan": int(d.atlanan),
        "duvar_s": time.perf_counter() - t0,
        "durum_dizin": str(dz),
    }, indent=2, default=float), encoding="utf-8")
    print(f"yazildi: {ozet}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
