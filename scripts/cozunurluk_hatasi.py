"""Çözünürlük hatası modeli — posteriorun gürültüsüne eklenecek terim (Protokol D).

M (24 ms) ve Mt (0,1 s) kampanyaları aynı 6 θ × 2 tohumu kaba/orta/ince
merdivende koşuyor. Üretim merdiveni `L` için, ince merdivene göre fark

    Δ_k(θ) = ȳ_L(θ) − ȳ_ince(θ)        (dönüşümlü birimde, `p_kalibrasyon_raporu.DONUSUMLER`)

eksen başına ölçülür. Kilitli kural (PROTOKOL-D §3):

- `σ_çöz = RMS_θ(Δ)` — sapma (`ortalama Δ`) **dahil**; ince merdiven de
  yakınsamamış olabileceği için bu bir alt sınırdır ve öyle yazılır.
- `kayma_orani = std_θ(Δ) / |ortalama_θ(Δ)|`: `< 0,5` ise kayma büyük
  ölçüde θ'dan bağımsızdır ("sabit kayma") — kontrast yorumunu destekler.

Kullanim:
    python scripts/cozunurluk_hatasi.py --kok kampanya --onek Mt --uretim orta \\
        --json kampanya/S_cozunurluk_Mt_orta.json
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

GOZLEMLER_C = ("beta_eksi_1", "V_krater", "M_ejekta", "R_krater", "dV_sikisma", "mu_ejekta")
MERDIVENLER = ("kaba", "orta", "ince")
N_TETA = 6
SABIT_KAYMA_ESIGI = 0.5


def topla(kok: Path, onek: str) -> dict:
    """`{(k, merdiven): {gözlem: [tohum değerleri (dönüşümlü)]}}`."""
    import p_kalibrasyon_raporu as pr

    # Onbellek (scripts/gozlem_onbellek.py): anahtar kod ozeti + npz boyut/mtime;
    # degerler bit-ayni, ayni npz her raporda yeniden hesaplanmaz.
    from gozlem_onbellek import gozlem

    veri = {}
    for k in range(N_TETA):
        for m in MERDIVENLER:
            d = {g: [] for g in GOZLEMLER_C}
            for f in sorted(glob.glob(str(kok / f"{onek}_{m}_t{k}_sahne*.durumlar"
                                          / "nokta_*.npz"))):
                gv = dict(gozlem(f))
                gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
                for g in GOZLEMLER_C:
                    d[g].append(pr.donustur(g, float(gv[g])))
            veri[(k, m)] = d
    return veri


def hata_modeli(veri: dict, uretim: str = "orta", referans: str = "ince") -> dict:
    out = {}
    for g in GOZLEMLER_C:
        farklar = []
        for k in range(N_TETA):
            a = [v for v in veri.get((k, uretim), {}).get(g, []) if np.isfinite(v)]
            b = [v for v in veri.get((k, referans), {}).get(g, []) if np.isfinite(v)]
            if a and b:
                farklar.append(float(np.mean(a) - np.mean(b)))
        d = np.asarray(farklar, float)
        if len(d) < 2:
            out[g] = {"n_theta": int(len(d)), "sigma_coz": float("nan"), "karar": "OKUNMAZ"}
            continue
        ort = float(d.mean())
        sap = float(d.std(ddof=1))
        oran = sap / abs(ort) if ort != 0 else float("inf")
        out[g] = {"n_theta": int(len(d)), "farklar": farklar,
                  "ortalama_kayma": ort, "kayma_sapmasi": sap,
                  "sigma_coz": float(np.sqrt(np.mean(d ** 2))),
                  "kayma_orani": float(oran),
                  "karar": "SABIT KAYMA" if oran < SABIT_KAYMA_ESIGI else "THETA'YA BAGLI KAYMA"}
    return {"uretim": uretim, "referans": referans, "gozlem": out,
            **kapsam_denetle(veri, uretim, referans),
            "not": "sigma_coz ince merdivene gore; ince de yakinsamamissa ALT SINIR"}


def kapsam_denetle(veri: dict, uretim: str = "orta", referans: str = "ince",
                   n_tohum: int = 2) -> dict:
    """Beklenen `N_TETA θ × n_tohum × {üretim, referans}` durum dosyası var mı.

    2026-09-15 öz denetim: Mt kampanyası kısmen koşunca (14 Eylül iptali)
    `σ_çöz` eksik θ/tohumdan hesaplanıyor ve D/HT bunu tam havuz gibi
    kaydediyordu (A84 türü sessiz eksik). Hesap değişmez; eksik YAZILIR.
    """
    eksik = []
    for k in range(N_TETA):
        for m in (uretim, referans):
            n = len(veri.get((k, m), {}).get("beta_eksi_1", []))
            if n < n_tohum:
                eksik.append(f"t{k}:{m}:{n}/{n_tohum}")
    return {"tam": not eksik, "eksik": eksik}


def oku(yol, gozlemler) -> dict:
    """Çözünürlük JSON'u → `{"sigma": {gözlem: σ_çöz}, "tam", "not"}` (D ve HT ortak).

    Kilitli kural değişmez: sonlu `σ_çöz` kullanılır, yoksa terim `0` ve
    "COZUNURLUK TERIMI YOK". Havuz eksikse not "EKSIK HAVUZ" der; kapsam
    alanı olmayan eski JSON'da `tam = None` ve not bunu söyler.
    """
    yol = Path(yol) if yol else None
    if yol is None or not yol.exists():
        return {"sigma": {}, "tam": None, "not": "COZUNURLUK TERIMI YOK"}
    j = json.loads(yol.read_text(encoding="utf-8"))
    cj = j.get("gozlem", {})
    sig = {g: float(cj[g]["sigma_coz"]) for g in gozlemler
           if g in cj and np.isfinite(cj[g].get("sigma_coz", float("nan")))}
    if not sig:
        return {"sigma": {}, "tam": j.get("tam"), "not": "COZUNURLUK TERIMI YOK (OKUNMAZ)"}
    notu = f"cozunurluk: {yol.name}"
    if j.get("tam") is False:
        ek = j.get("eksik", [])
        notu += f" -- EKSIK HAVUZ ({len(ek)} eksik: {', '.join(ek[:6])})"
    elif "tam" not in j:
        notu += " -- kapsam denetimi yok (eski JSON)"
    return {"sigma": sig, "tam": j.get("tam"), "not": notu}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--onek", default="Mt")
    ap.add_argument("--uretim", choices=("kaba", "orta"), default="orta")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = hata_modeli(topla(a.kok, a.onek), a.uretim)
    out["onek"] = a.onek
    print("=" * 72)
    print(f"COZUNURLUK HATASI -- {a.onek}: {a.uretim} - ince (donusumlu birim)")
    print("=" * 72)
    print("  havuz: TAM" if out["tam"] else
          f"  havuz: EKSIK ({len(out['eksik'])}): {', '.join(out['eksik'])}")
    for g, d in out["gozlem"].items():
        if d["karar"] == "OKUNMAZ":
            print(f"  {g:>12}: OKUNMAZ (n={d['n_theta']})")
            continue
        print(f"  {g:>12}: sigma_coz {d['sigma_coz']:.4g}  ort kayma {d['ortalama_kayma']:+.4g}  "
              f"sapma {d['kayma_sapmasi']:.4g}  oran {d['kayma_orani']:.2f} -> {d['karar']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
