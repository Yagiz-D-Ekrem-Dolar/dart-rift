"""Gözeneklilik kazıyı yutuyor mu? — **ölçüt önceden yazılı**.

İki kol, aynı `t_end`, aynı tohum, tek fark P-α:

```
A  gözenekli   (alpha0 sahneden)
B  gözeneksiz  (P-α kapalı VE alpha0 = 1 — bkz. rapor A14)
```

## Neden `n_bekleyen`, `n_hedef_ejekta` değil

`n_hedef_ejekta` maddenin `r > R`'yi **geçmesini** bekler. Kazı başlamış
ama madde hâlâ yoldaysa iki kol da `28` gösterir ve deney hiçbir şey
söylemez. `n_bekleyen` (içeride, dışarı doğru, `v_r > v_kaçış`) kazının
**başladığını** geçişi beklemeden görür.

## Ölçüt — veriye BAKMADAN yazıldı

| gözlenen | sonuç |
|---|---|
| `B` ≫ `A` (`≥ 3×` **ve** `≥ 50` parçacık fark) | gözeneklilik kazıyı **yutuyor** |
| ikisi de `≈ 0` | gözeneklilik **sebep değil**; başka yere bak |
| `A` ≳ `B` | hipotez **ters** çıktı — kaydet, açıklama arama |

## Deneyi GEÇERSİZ kılan durumlar

`B` kolu `alpha0 = 1` ile daha yoğun (`2700` vs `2077 kg/m³`) bir hedef
demek; kol **tek değişkenli değil** (A14). Ayrıca:

* `B`'de `β` çılgınlaşırsa (`|β| > 10`) ya da `n_bekleyen` toplam
  parçacığın `%50`'sini geçerse cisim **dağılıyordur**, kazı değil.
* İki kolun `t_end`'i eşit değilse karşılaştırma yapılmaz.

Bu kontroller **otomatik**; geçmezse betik *"KARSILASTIRILAMAZ"* der ve
bir sonuç **uydurmaz**.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

#: Ölçüt eşikleri — **veriye bakmadan** seçildi.
KAT_ESIGI = 3.0
MUTLAK_ESIGI = 50
BETA_CILGIN = 10.0
DAGILMA_ORANI = 0.50


def _oku(yol: str) -> list[dict]:
    sat = [json.loads(l) for l in Path(yol).read_text(
        encoding="utf-8").splitlines() if l.strip()]
    if not sat:
        raise SystemExit(f"{yol}: bos iz — kayit bulunamadi")
    if "n_bekleyen" not in sat[-1]:
        raise SystemExit(
            f"{yol}: iz `n_bekleyen` TASIMIYOR (tanidan onceki surumle "
            f"yazilmis). Karsilastirma yapilamaz.")
    return sat


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gozenekli", required=True)
    ap.add_argument("--gozeneksiz", required=True)
    ap.add_argument("--n-toplam", type=int, default=0,
                    help="asama-2 parcacik sayisi (dagilma denetimi icin)")
    a = ap.parse_args()

    A, B = _oku(a.gozenekli), _oku(a.gozeneksiz)
    tA, tB = A[-1]["t"], B[-1]["t"]

    print("=" * 74, flush=True)
    print("GOZENEKLILIK KARSILASTIRMASI — olcut onceden yazildi", flush=True)
    print("=" * 74, flush=True)
    print(f"  A gozenekli   t_son = {tA:.4e}  ({len(A)} ornek)", flush=True)
    print(f"  B gozeneksiz  t_son = {tB:.4e}  ({len(B)} ornek)", flush=True)

    # --- gecerlilik denetimleri
    if abs(tA - tB) > 1e-3 * max(abs(tA), abs(tB), 1e-30):
        print("\nKARSILASTIRILAMAZ: iki kolun t_end'i esit degil.", flush=True)
        return 1
    for ad, z in (("A", A[-1]), ("B", B[-1])):
        if abs(z["beta_bal"]) > BETA_CILGIN:
            print(f"\nKARSILASTIRILAMAZ: {ad} kolunda beta = "
                  f"{z['beta_bal']:.4g} — cisim dagiliyor, kazi degil.",
                  flush=True)
            return 1
        if a.n_toplam and z["n_bekleyen"] > DAGILMA_ORANI * a.n_toplam:
            print(f"\nKARSILASTIRILAMAZ: {ad} kolunda parcaciklarin "
                  f"%{100 * z['n_bekleyen'] / a.n_toplam:.0f}'i disari "
                  f"gidiyor — cisim dagiliyor.", flush=True)
            return 1

    nA, nB = A[-1]["n_bekleyen"], B[-1]["n_bekleyen"]
    eA, eB = A[-1]["n_hedef_ejekta"], B[-1]["n_hedef_ejekta"]
    print(f"\n{'':14} {'n_bekleyen':>11} {'n_hedef_ejekta':>15} {'beta':>9}")
    print("-" * 54, flush=True)
    print(f"{'A gozenekli':14} {nA:11d} {eA:15d} "
          f"{A[-1]['beta_bal']:9.5f}", flush=True)
    print(f"{'B gozeneksiz':14} {nB:11d} {eB:15d} "
          f"{B[-1]['beta_bal']:9.5f}", flush=True)

    # --- onceden yazilmis olcut
    print(f"\nOLCUT: B >= {KAT_ESIGI:.0f} x A  VE  B - A >= {MUTLAK_ESIGI}",
          flush=True)
    kat = nB / nA if nA > 0 else float("inf") if nB > 0 else 1.0
    print(f"  kat = {kat:.2f}   fark = {nB - nA}", flush=True)

    print(f"\n{'=' * 74}", flush=True)
    if nB >= KAT_ESIGI * max(nA, 1) and (nB - nA) >= MUTLAK_ESIGI:
        print("SONUC: GOZENEKLILIK KAZIYI YUTUYOR.", flush=True)
        print("  -> beta'nin merminin sekmesi olmasi SAYISAL degil FIZIKSEL.",
              flush=True)
    elif nA == 0 and nB == 0:
        print("SONUC: GOZENEKLILIK SEBEP DEGIL — iki kolda da kazi YOK.",
              flush=True)
        print("  -> sorun baska yerde; aramaya devam.", flush=True)
    elif nA > nB:
        print("SONUC: HIPOTEZ TERS CIKTI (gozenekli kol DAHA cok kaziyor).",
              flush=True)
        print("  -> kaydet, aciklama UYDURMA; ayri bir olcum gerekiyor.",
              flush=True)
    else:
        print("SONUC: FARK VAR AMA OLCUTU GECMIYOR — belirsiz.", flush=True)
        print(f"  -> {nA} vs {nB}. Esigi SONRADAN dusurmek yasak (o zaman "
              f"olcut veriye uydurulmus olur).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
