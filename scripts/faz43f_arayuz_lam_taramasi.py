"""ADR-0043 gereksinim #3: **arayüz yüksek `λ`'da ne yapıyor?**

Boşluk 3 yalnızca `λ = 2` (kütle oranı `8:1`) için kapatıldı. ADR-0043
`λ ≈ 19` (`6478:1`) öneriyor — ölçülmüş her şeyin **çok** ötesinde.
KAYIT-024 ayrıca gürültünün oranla **büyüdüğünü** ölçmüştü.

## `λ = 19` DOĞRUDAN ÖLÇÜLEMİYOR — ve bu bir sonuç değil, bir sınır

`run_solid_interface` üç kol koşuyor ve üçüncüsü **tekdüze ince**
referans: `n_coarse · λ` kenarlı bir kutu.

| `n_coarse` | `λ` | tekdüze ince `N` | |
|---|---|---|---|
| 32 | 2 | `64³` = 262 144 | koştu (KAYIT-037) |
| 32 | 6 | `192³` = 7,1 M | 4 GiB'a **sığmaz** |
| 32 | **19** | **`608³` = 225 M** | **imkânsız** |
| 16 | 6 | `96³` = 884 736 | koşabilir |

> Referans kolu olmadan *"taşma"* ölçülemez — parantezin üst ucu odur.
> Yani `λ = 19` bu sınavda **ölçülemez**; ölçülebilen şey **eğilim**.

## Bu betiğin yaptığı

`n_coarse` sabit, `λ` taranıyor. Soru: taşma `λ` ile **büyüyor mu**?

- Büyümüyorsa: `λ = 19`'un da güvenli olduğuna dair **kanıt** (ispat değil).
- Büyüyorsa: ADR-0043 §7 madde 3 **düşer** ve kilitlenemez.

> Sonuç ne olursa olsun `λ = 19` **ölçülmemiş** kalır. Eğilimi
> *"ölçüldü"* diye yazmak, tam da bu projenin altı kez düştüğü kalıp
> olurdu.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dartrift.validation.solid_interface import (BASALT_SOLID,  # noqa: E402
                                                 run_solid_interface)

#: 4 GiB'lik yerel kartin pratik siniri. Asilirsa kol KOSULMAZ ve
#: `atlandi` yazilir -- OOM ile dusmek yerine.
N_UST_SINIR = 2_500_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--n-coarse", type=int, default=16)
    ap.add_argument("--lam", type=int, nargs="+", default=[2, 3, 4, 6])
    ap.add_argument("--r-ic", type=float, default=0.15)
    ap.add_argument("--t-end", type=float, default=3.0e-5)
    ap.add_argument("--out", default=str(REPO.parent / "faz43f_sonuc.json"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("ADR-0043 #3 — ARAYUZ `lam` TARAMASI (bosluk 3, yuksek oran)",
          flush=True)
    print("=" * 78, flush=True)
    print(f"\nn_coarse = {a.n_coarse}, r_ic = {a.r_ic}, "
          f"t_end = {a.t_end:.3e}", flush=True)
    print(f"tekduze ince referans N = (n_coarse*lam)^3; "
          f"ust sinir {N_UST_SINIR:,}", flush=True)

    sonuclar, atlanan = {}, []
    print(f"\n{'lam':>4} {'kutle_or':>9} {'ref_N':>11} {'yargi':>13} "
          f"{'TASMA%':>9} {'parantez_gen%':>14}", flush=True)
    print("-" * 78, flush=True)

    for lam in a.lam:
        ref_n = (a.n_coarse * lam) ** 3
        if ref_n > N_UST_SINIR:
            print(f"{lam:4d} {lam ** 3:9d} {ref_n:11,d}  ATLANDI — "
                  f"tekduze ince referans siga", flush=True)
            atlanan.append({"lam": lam, "ref_N": ref_n, "neden": "bellek"})
            continue
        try:
            y = run_solid_interface(a.n_coarse, lam, a.r_ic, a.device,
                                    a.t_end, BASALT_SOLID,
                                    per_particle_h=True,
                                    etiket=f"lam{lam}")
        except RuntimeError as e:
            print(f"{lam:4d} {lam ** 3:9d} {ref_n:11,d}  OLCULEMEDI — {e}",
                  flush=True)
            sonuclar[str(lam)] = {"yargi": "olculemedi", "neden": str(e)}
            continue
        y["lam"] = lam
        y["ref_N"] = ref_n
        sonuclar[str(lam)] = y
        gen = y.get("parantez_genisligi_rel", float("nan"))
        print(f"{lam:4d} {lam ** 3:9d} {ref_n:11,d} {y['yargi']:>13} "
              f"{100 * y['tasma_rel']:9.4f} {100 * gen:14.4f}", flush=True)

    print("-" * 78, flush=True)
    olculen = [(int(k), v) for k, v in sonuclar.items()
               if v.get("yargi") not in ("olculemedi", "belirsiz")]
    olculen.sort()
    if len(olculen) < 2:
        print("\nEGILIM OLCULEMEDI — en az iki gecerli kol gerekli. "
              "kayit bulunamadi.", flush=True)
    else:
        ilk, son = olculen[0], olculen[-1]
        d = son[1]["tasma_rel"] - ilk[1]["tasma_rel"]
        print(f"\nEGILIM  lam {ilk[0]} -> {son[0]}: "
              f"tasma {100 * ilk[1]['tasma_rel']:.4f}% -> "
              f"{100 * son[1]['tasma_rel']:.4f}%  "
              f"({'BUYUYOR' if d > 0 else 'BUYUMUYOR'})", flush=True)
        # Cok satirli f-string ifadesi PEP 701 (3.12+) gerektirir; TRUBA'da
        # daha eski bir yorumlayici olabilir. Duz `if` guvenli.
        if d > 0:
            print("  ADR-0043 §7 madde 3 RISKLI", flush=True)
        else:
            print("  lam=19 icin DOLAYLI kanit (ispat DEGIL)", flush=True)

    print(f"\nlam = 19 bu sinavda OLCULEMEZ: tekduze ince referans "
          f"{(a.n_coarse * 19) ** 3:,} parcacik ister.", flush=True)
    print("  Bu bir SONUC degil, olcumun SINIRI. ADR-0043 §7 madde 3 "
          "acik kalir.", flush=True)

    Path(a.out).write_text(json.dumps(
        {"n_coarse": a.n_coarse, "r_ic": a.r_ic, "t_end": a.t_end,
         "lam_19_olculemez": True, "atlanan": atlanan,
         "sonuclar": sonuclar}, indent=2, default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
