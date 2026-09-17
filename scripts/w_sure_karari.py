"""Protokol W §3.2 — `t_end` seçimi, **ölçülen hızdan** (kilitli kural).

W0 zamanlama koşusu bilimsel sonuç değildir; yalnız hız verir. `t_end`
buradaki kuralla seçilir ve seçim **koşu sonucuna değil süreye** bakar:

    maliyet(T) ≈ c_adim · [ n_gecis + (T − t_gecis) / dt_gec ]

    c_adim  = duvar_saniye / n_adim          (adım başına ortalama)
    dt_gec  = (t_end0 − t_gecis) / (n_adim − n_gecis)   (geçiş sonrası adım)

- `maliyet(600 s) ≤ 8 GPU-saat`  → `t_end = 600`
- değilse `maliyet(60 s) ≤ 8`    → `t_end = 60`
- değilse                        → `t_end = 10` **ve "süre yetersiz" damgası**

Kullanim:
    python scripts/w_sure_karari.py --npz .../W0_zamanlama.durumlar/nokta_*.npz \\
        --duvar-saniye 3600 [--json kampanya/S_W0.json]
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

#: Koşu başına kabul edilen üst maliyet (GPU-saat) — PROTOKOL-W §3.2.
BUTCE_GPU_SAAT = 8.0
#: Sırayla denenecek `t_end` adayları [s].
ADAYLAR = (600.0, 60.0)
#: Hiçbiri sığmazsa kullanılacak süre [s] ("süre yetersiz" damgasıyla).
TABAN_T_END = 10.0


def maliyet_saat(T: float, *, c_adim: float, n_gecis: int, t_gecis: float,
                 dt_gec: float) -> float:
    """`T` saniyelik koşunun tahmini maliyeti [GPU-saat]."""
    if dt_gec <= 0.0:
        raise ValueError(f"dt_gec pozitif olmali, {dt_gec} geldi")
    if T < t_gecis:
        raise ValueError(f"T ({T}) t_gecis'ten ({t_gecis}) kucuk olamaz")
    n = float(n_gecis) + (float(T) - float(t_gecis)) / float(dt_gec)
    return float(c_adim) * n / 3600.0


def karar(*, duvar_saniye: float, n_adim: int, n_gecis: int, t_gecis: float,
          t_end0: float, butce: float = BUTCE_GPU_SAAT) -> dict:
    """PROTOKOL-W §3.2 kuralını uygula."""
    if duvar_saniye <= 0.0 or n_adim <= 0:
        raise ValueError("duvar_saniye ve n_adim pozitif olmali")
    if not (0 < n_gecis < n_adim):
        raise ValueError(f"n_gecis (0, n_adim) icinde olmali: {n_gecis}/{n_adim}")
    if not (0.0 < t_gecis < t_end0):
        raise ValueError(f"t_gecis (0, t_end0) icinde olmali: {t_gecis}/{t_end0}")
    c_adim = float(duvar_saniye) / float(n_adim)
    dt_gec = (float(t_end0) - float(t_gecis)) / float(n_adim - n_gecis)
    dt_once = float(t_gecis) / float(n_gecis)
    tahmin = {}
    secim, damga = TABAN_T_END, "SURE YETERSIZ"
    for T in ADAYLAR:
        m = maliyet_saat(T, c_adim=c_adim, n_gecis=n_gecis, t_gecis=t_gecis,
                         dt_gec=dt_gec)
        tahmin[f"{T:g}"] = m
        if m <= butce and damga == "SURE YETERSIZ":
            secim, damga = T, "TAMAM"
    tahmin[f"{TABAN_T_END:g}"] = maliyet_saat(
        TABAN_T_END, c_adim=c_adim, n_gecis=n_gecis, t_gecis=t_gecis,
        dt_gec=dt_gec)
    return {
        "t_end": float(secim), "damga": damga, "butce_gpu_saat": float(butce),
        "c_adim_s": c_adim, "dt_gecis_oncesi_s": dt_once, "dt_gecis_sonrasi_s": dt_gec,
        "dt_buyume_orani": dt_gec / dt_once if dt_once > 0 else float("nan"),
        "n_adim": int(n_adim), "n_gecis": int(n_gecis),
        "t_gecis": float(t_gecis), "t_end0": float(t_end0),
        "maliyet_tahmini_gpu_saat": tahmin,
        "toplam_6_kosu_gpu_saat": 6.0 * tahmin[f"{secim:g}"],
    }


def npz_oku(desen: str) -> dict:
    dosyalar = sorted(glob.glob(desen))
    if not dosyalar:
        raise SystemExit(f"npz bulunamadi: {desen}")
    z = np.load(dosyalar[-1])
    ft = json.loads(str(z["fizik_tani"]))
    g = ft.get("gec_evre") or {}
    if not g:
        raise SystemExit("bu kosuda gec evre gecisi YOK -- W0 degil")
    return {"n_adim": int(z["n_adim"]), "n_gecis": int(g["adim_gecis"]),
            "t_gecis": float(g["t_gecis"]), "t_end0": float(z["t"]),
            "beta_hedef": float(ft["beta_hedef"]), "dosya": dosyalar[-1]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True, help="W0 durum npz deseni")
    ap.add_argument("--duvar-saniye", type=float, required=True,
                    help="isin gercek duvar suresi (sacct Elapsed)")
    ap.add_argument("--butce", type=float, default=BUTCE_GPU_SAAT)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    v = npz_oku(a.npz)
    k = karar(duvar_saniye=a.duvar_saniye, n_adim=v["n_adim"],
              n_gecis=v["n_gecis"], t_gecis=v["t_gecis"], t_end0=v["t_end0"],
              butce=a.butce)
    print("=" * 78)
    print("PROTOKOL W S3.2 -- t_end karari (W0 zamanlama kosusundan)")
    print("=" * 78)
    print(f"  kosu        : {v['dosya']}")
    print(f"  adim        : {k['n_adim']}  (gecise kadar {k['n_gecis']})")
    print(f"  dt          : gecis oncesi {k['dt_gecis_oncesi_s']:.3e} s  ->  "
          f"sonrasi {k['dt_gecis_sonrasi_s']:.3e} s  "
          f"({k['dt_buyume_orani']:.0f}x)")
    print(f"  adim maliyeti: {k['c_adim_s']:.4f} s/adim")
    for T, m in k["maliyet_tahmini_gpu_saat"].items():
        print(f"  t_end = {T:>4} s  ->  {m:8.2f} GPU-saat/kosu")
    print(f"\nSECIM: t_end = {k['t_end']:g} s   ({k['damga']})   "
          f"6 kosu toplam ~{k['toplam_6_kosu_gpu_saat']:.1f} GPU-saat")
    print(f"  (W0 beta_hedef = {v['beta_hedef']:.4f} -- BILIMSEL SONUC DEGIL, "
          "yalniz kayit)")
    if a.json:
        a.json.write_text(json.dumps({**k, **v}, indent=1, default=float),
                          encoding="utf-8")
        print(f"yazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
