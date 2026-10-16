"""PROTOKOL-HAVUZ §6 — **SBC kapısı**: posterior yayımlanabilir mi?

Kapının kuralı 2026-10-08'den önce kilitli ve burada **tanımlanmıyor**:

| SBC sonucu (her eksen) | karar |
|---|---|
| hepsi `KALIBRE` / `DUZGUN` | posterior **yayımlanır** |
| bir eksen `ASIRI TEMKINLI` | yayımlanır, o eksen "muhafazakâr" etiketiyle |
| bir eksen **`YANLI`** | **YAYIMLANMAZ** → (a) sırta `+24` nokta, ya da (b) eleme |
| `DUZGUN DEGIL` | yayımlanmaz, sebep aranır |

Protokol `n_sbc ≥ 200`, **havuzun gerçek vekili**, aynı `R`, aynı `σ`
diyor. Üçü de buradan geliyor: vekil/`R`/`σ` `up_onsel_ve_tarih._ortak`
ile, yani `uretim_posterior` ile **birebir aynı** yoldan.

**Paydayı büyütüp geçmek yasak** (A115 (c)3: yanlılık bir kaymadır,
paydayı büyütmek onu gizler). Bu betik σ'ya dokunmaz.

### Hız notu

Izgaradaki vekil öngörüsü (`ort`, `varyans`) **veriden bağımsız**;
bir kez hesaplanıp 200 tekrarda yeniden kullanılıyor. Tekrar başına
yalnız olabilirlik yeniden değerlendiriliyor.

Kullanım:

    python scripts/up_sbc_kapisi.py <havuz.csv> --n-sbc 200 --json <cikti>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "src"))

from up_onsel_ve_tarih import _ortak  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S4  # noqa: E402
from dartrift.inference.kalibrasyon import sbc_calistir  # noqa: E402
from dartrift.inference.posterior import grid_posterior_hetero  # noqa: E402

#: PROTOKOL-HAVUZ §6 asgarisi.
ASGARI_SBC = 200

#: Belirlenimci tekrar (ADR-0004) — ongoru uretilmeden once secildi.
TOHUM_SBC = 20261016


def _en_yakin_dugum(U: np.ndarray, u: np.ndarray) -> int:
    return int(np.argmin(np.sum((U - u[None, :]) ** 2, axis=1)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("havuz", type=Path)
    ap.add_argument("--n-grid", type=int, default=60)
    ap.add_argument("--n-sbc", type=int, default=ASGARI_SBC)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    if a.n_sbc < ASGARI_SBC:
        raise SystemExit(f"PROTOKOL-HAVUZ §6: n_sbc >= {ASGARI_SBC} olmali, "
                         f"{a.n_sbc} verildi")

    o = _ortak(a.havuz, a.n_grid)
    rapor = o["rapor"]
    rapor["n_grid"] = a.n_grid
    rapor["n_sbc"] = a.n_sbc
    rapor["tohum_sbc"] = TOHUM_SBC

    ort, varyans, R = o["ort"], o["varyans"], o["R"]
    eksen = o["eksen"]
    U = np.column_stack([g.ravel() for g in
                         np.meshgrid(*([eksen] * 3), indexing="ij")])

    # Gurultu: S(theta) = D(theta)^(1/2) R D(theta)^(1/2) -- cikarimla AYNI.
    L_R = np.linalg.cholesky(np.asarray(R, dtype=np.float64))

    def uret(x, rng):
        """Dogal birimde gercek `x` -> gurultulu veri (cikarimla ayni model)."""
        u = DART_UZAYI_S4.to_unit(np.atleast_2d(np.asarray(x, float)))[0]
        k = _en_yakin_dugum(U, np.clip(u, 0.0, 1.0))
        sd = np.sqrt(varyans[k])
        return ort[k] + sd * (L_R @ rng.standard_normal(ort.shape[1]))

    def cikarim(veri):
        return grid_posterior_hetero(DART_UZAYI_S4, ort, varyans,
                                     np.asarray(veri, float), R,
                                     n_grid=a.n_grid)

    sonuc = sbc_calistir(DART_UZAYI_S4, uret, cikarim, a.n_sbc,
                         tohum=TOHUM_SBC)

    tanilar = [d["tani"] for d in sonuc.tanilar]
    rapor["sbc"] = {
        "adlar": list(sonuc.adlar),
        "tanilar": [{k: v for k, v in d.items() if k != "kapsama"}
                    for d in sonuc.tanilar],
        "kapsama68": [next(k["deneysel"] for k in d["kapsama"]
                           if k["nominal"] == 0.68) for d in sonuc.tanilar],
        "genel": sonuc.genel,
    }

    # --- PROTOKOL-HAVUZ §6 karari -----------------------------------
    if any(t.startswith("DUZGUN DEGIL") for t in tanilar):
        karar = "YAYIMLANMAZ -- DUZGUN DEGIL, sebep aranir"
    elif any("YANLI" in t for t in tanilar):
        karar = ("YAYIMLANMAZ -- YANLI eksen var. (a) sirta +24 nokta ve "
                 "SBC yeniden, ya da (b) tarih_esleme ile ELEME raporlanir.")
    elif any("ASIRI GUVENLI" in t for t in tanilar):
        karar = ("YAYIMLANMAZ -- ASIRI GUVENLI, §6 tablosunda yok; "
                 "DUZGUN DEGIL gibi islenir, sebep aranir.")
    elif any("ASIRI TEMKINLI" in t for t in tanilar):
        karar = ("YAYIMLANIR -- ilgili eksen(ler) 'muhafazakar' etiketiyle "
                 "(iddia kuculur, yanlis olmaz).")
    else:
        karar = "YAYIMLANIR -- butun eksenler KALIBRE."
    rapor["sbc"]["karar"] = karar

    print("=" * 70)
    print(f"PROTOKOL-HAVUZ §6 — SBC KAPISI  (n_sbc = {a.n_sbc}, "
          f"tohum {TOHUM_SBC})")
    print("=" * 70)
    for ad in ("vekil_beta", "vekil_M_ejekta"):
        v = rapor[ad]
        print(f"{ad:15s} q2={v['q2']:+.4f} Bachoc={v['varyans_carpani']:.3f}")
    print(f"R olculmus     rho_kuculmus={rapor['R']['rho_kuculmus']:+.4f}")
    print()
    for ad, d, k68 in zip(sonuc.adlar, sonuc.tanilar,
                          rapor["sbc"]["kapsama68"], strict=True):
        print(f"  {ad:14s} {d['tani']:28s} "
              f"PIT ort={d['pit_ortalama']:.4f} (se {d['pit_ortalama_se']:.4f}) "
              f"KS p={d['ks_p']:.4f}  kapsama68={k68:.3f}")
    print()
    print(f"  GENEL : {sonuc.genel}")
    print(f"  KARAR : {karar}")
    print("=" * 70)

    if a.json:
        a.json.write_text(json.dumps(rapor, indent=1, ensure_ascii=False,
                                     default=float), encoding="utf-8")
        print(f"yazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
