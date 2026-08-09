"""FAZ 4.8 uzun koşusunun izini **oku ve yargıla**.

Koşu bitince elle bakmak yerine, sorulacak üç soru **önceden** yazılı:

1. **Ejekta başladı mı?** `n_hedef_ejekta > n_aktarilan` ise evet.
   Altında kaldığı sürece sayılan hâlâ merminin kırıntısı.
2. **`β_bal` duruldu mu?** `settling_time` ile — FAZ 4.5'inkiyle **aynı**
   ölçüt.
3. **Krater var mı?** Ölçülen derinlik **gürültü tabanının** üstünde mi?

## Gürültü tabanı **ölçüldü**, varsayılmadı

Kratersiz bir küreye gürültü ve küresel kayma verilince aynı çıkarıcı
`0,02–0,17 m` okuyor (`tests/test_inference_forward.py`). Bu bandın
içinde kalan bir *"derinlik"* krater **değildir**.

> Uyarı: bu koşu krater sütununu **varsayılan** kutulamayla ölçtü
> (`outer = 60°`, `n_bins = 20`). O ayarlar `D < 20 m` krateri
> **göremiyor** — sonradan ölçülüp `KRATER_AYARLARI_DART` yazıldı.
> Yani buradaki derinlik sütunu *"küçük krater yok"* diyemez; yalnızca
> *"büyük krater yok"* der.
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

from dartrift.validation.settling_time import settling_time  # noqa: E402

#: `tests/test_inference_forward.py`de ölçüldü.
GURULTU_TABANI_M = 0.17


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iz", required=True, help=".izler.jsonl yolu")
    ap.add_argument("--n-aktarilan", type=int, default=32,
                    help="aktarilan cekirdek parcacik sayisi (esik)")
    a = ap.parse_args()

    sat = [json.loads(l) for l in Path(a.iz).read_text(
        encoding="utf-8").splitlines() if l.strip()]
    if len(sat) < 2:
        print(f"yalnizca {len(sat)} ornek — yargi verilemez. "
              f"kayit bulunamadi.", flush=True)
        return 1

    t = np.array([z["t"] for z in sat])
    b = np.array([z["beta_bal"] for z in sat])
    ne = np.array([z["n_hedef_ejekta"] for z in sat])
    dz = np.array([z.get("krater_derinlik", np.nan) for z in sat])
    adim = np.array([z["adim"] for z in sat])

    print("=" * 74, flush=True)
    print(f"FAZ 4.8 IZ ANALIZI — {len(sat)} ornek, "
          f"t = {t[0]:.4e} .. {t[-1]:.4e} s", flush=True)
    print("=" * 74, flush=True)

    # --- 1) EJEKTA BASLADI MI
    basladi = ne > a.n_aktarilan
    print(f"\n[1] EJEKTA BASLADI MI  (esik: n > {a.n_aktarilan})", flush=True)
    print(f"    n_hedef_ejekta: min {ne.min()}  max {ne.max()}", flush=True)
    if basladi.any():
        i = int(np.argmax(basladi))
        print(f"    EVET — ilk t = {t[i]:.4e} s (adim {adim[i]})", flush=True)
    else:
        print(f"    HAYIR — {t[-1]:.4e} s'ye kadar sayilan hala merminin "
              f"kirintisi", flush=True)

    # --- 1b) BEKLEYEN MADDE VAR MI  (yeni izlerde; eskilerde yok)
    print(f"\n[1b] ICERIDE DISARI GIDEN MADDE (kacis_bekleyenler)", flush=True)
    if "n_bekleyen" not in sat[-1]:
        print(f"    bu iz bu tanidan ONCE yazildi — kayit bulunamadi.",
              flush=True)
        print(f"    (yeni kosular `n_bekleyen` / `t_gecis_medyan` tasiyor)",
              flush=True)
    else:
        nb = np.array([z["n_bekleyen"] for z in sat])
        tg = np.array([z.get("t_gecis_medyan", np.nan) for z in sat])
        print(f"    n_bekleyen: ilk {nb[0]}  son {nb[-1]}  max {nb.max()}",
              flush=True)
        if nb[-1] == 0:
            print(f"    BEKLEYEN YOK -> daha uzun kosmak EJEKTA GETIRMEZ.",
                  flush=True)
            print(f"    Kazi olmuyor; sorun sure degil, TASARIM.", flush=True)
        else:
            print(f"    t_gecis medyan (son) = {tg[-1]:.3f} s "
                  f"— serbest ucus kestirimi, KESIN DEGIL", flush=True)
            print(f"    -> {t[-1] + tg[-1]:.3f} s civari ejekta beklenir",
                  flush=True)

    # --- 2) BETA DURULDU MU
    d = settling_time(t, b, adim=adim)
    print(f"\n[2] beta_bal DURULMASI", flush=True)
    print(f"    ilk / son  = {b[0]:.6f} / {b[-1]:.6f}", flush=True)
    print(f"    yayilim    = {(b.max() - b.min()) / max(abs(b[-1]), 1e-300):.3e}",
          flush=True)
    print(f"    SABIT MI   = {d.get('sabit')}", flush=True)
    print(f"    DURULDU MU = {d['durulmus']}"
          f"{'' if d['durulmus'] else '  -- ' + d.get('neden', '')}", flush=True)
    if d.get("sabit"):
        print(f"    -> SABIT seri: 'durulma zamani' bir sey OLCMUYOR "
              f"(rapor A9/A12)", flush=True)

    # --- 3) KRATER
    print(f"\n[3] KRATER (VARSAYILAN kutulama — D < 20 m goremez)", flush=True)
    ok = np.isfinite(dz)
    if not ok.any():
        print(f"    derinlik hic olculemedi", flush=True)
    else:
        print(f"    derinlik: min {np.nanmin(dz):.4f}  max {np.nanmax(dz):.4f} m",
              flush=True)
        print(f"    gurultu tabani (olculdu) = {GURULTU_TABANI_M} m", flush=True)
        if np.nanmax(dz) > GURULTU_TABANI_M:
            print(f"    TABANIN USTUNDE — krater olabilir", flush=True)
        else:
            print(f"    TABANIN ALTINDA — buyuk krater YOK "
                  f"(kucugu bu ayarla zaten gorunmez)", flush=True)

    # --- OZET
    print(f"\n{'=' * 74}", flush=True)
    if basladi.any():
        print("SONUC: ejekta basladi -> FAZ 4.6 icin t_end buradan secilebilir",
              flush=True)
    else:
        print("SONUC: EJEKTA BASLAMADI. FAZ 4.6'nin gozlenebilirleri bu",
              flush=True)
        print("       surede olu; ya daha uzun kosu ya gozlenebilir degisikligi",
              flush=True)
        print("       gerekiyor (ADR karari).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
