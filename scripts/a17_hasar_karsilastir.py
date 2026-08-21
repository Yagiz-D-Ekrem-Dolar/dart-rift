"""A17 — hasar kolu ile kontrol kolunu **kayıtlı ölçütle** karşılaştır.

Ölçüt `docs/A17-HASAR-OLCUTU.md`'de, **koşulardan önce** yazıldı ve
commit'lendi (`ba04d36`). Bu betik onu uygular; eşikler burada
**yeniden yazılmaz**, aşağıdaki sabitler o belgeden gelir.

Girdi iki `*.son_durum.npz` — `faz48_iki_asama.py`'nin yazdığı son
durum. Ölçüm anlık durumdan yapılır; koşuyu tekrarlamaz.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dartrift.inference.forward import KRATER_AYARLARI_DART  # noqa: E402
from dartrift.observables.crater_shape import crater_profile  # noqa: E402
from dartrift.observables.momentum_transfer import (  # noqa: E402
    balistik_beta,
    kacis_bekleyenler,
)

# docs/A17-HASAR-OLCUTU.md — esikler ORADAN gelir.
ESIK_D_MAX = 0.999
# Kolun kayitli referansi. Iki asamali kol 1,4112; tek asamali kol
# 1,6175832 (docs/olcumler/faz48_tek_asama.json). Sabit birakmak
# ilk kullanimda yanlis kola karsi olcup 'TUTMADI' yazdirdi.
ESIK_BETA_KONTROL = 1.4112
ESIK_BETA_TOL = 0.01
ESIK_ORAN_DOGRULAR = 3.0
ESIK_ORAN_ELER = 1.2


def oku(yol: Path) -> dict:
    z = np.load(yol)
    x, v, m = z["x"], z["v"], z["m"]
    hedef = z["hedef"].astype(bool)
    R, v_esc = float(z["R"]), float(z["v_esc"])
    ehat, p_imp = z["ehat"], float(z["p_imp"])
    D = z["D"] if "D" in z.files else np.zeros(len(m))

    r = np.linalg.norm(x, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        v_r = np.einsum("ij,ij->i", v, x) / np.maximum(r, 1e-30)
    disari = hedef & (r > R) & (v_r > v_esc)

    d = balistik_beta(x, v, m, hedef=hedef, R=R, v_esc=v_esc,
                      ehat=ehat, p_imp=p_imp)
    kb = kacis_bekleyenler(x, v, m, hedef=hedef, R=R, v_esc=v_esc)
    try:
        kr = crater_profile(x[hedef], center=np.zeros(3),
                            impact_direction=ehat, reference_radius=R,
                            x_reference=z["x_referans"][hedef],
                            **KRATER_AYARLARI_DART)
        derinlik = float(kr.depth)
    except Exception as e:                                  # noqa: BLE001
        derinlik = float("nan")
        print(f"  (krater olculemedi: {str(e)[:60]})", flush=True)

    return {
        "yol": str(yol),
        "t": float(z["t"]),
        "n_disari": int(np.count_nonzero(disari)),
        "kutle_disari_kg": float(m[disari].sum()),
        "p_eksen_hedef": float(np.sum(m[disari] * (v[disari] @ ehat))),
        "beta_bal": float(d["beta_bal"]),
        "n_hedef_ejekta": int(d["n_hedef_ejekta"]),
        "n_bekleyen": int(kb["n_bekleyen"]),
        "krater_derinlik": derinlik,
        "D_max": float(np.max(D)),
        "D_ort_hedef": float(np.mean(D[hedef])),
        "n_tam_kirik": int(np.count_nonzero(D >= ESIK_D_MAX)),
    }


def _oran(h: float, k: float) -> float:
    if k == 0.0:
        return float("inf") if h != 0.0 else 1.0
    return abs(h) / abs(k)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kontrol", type=Path, required=True)
    ap.add_argument("--hasarli", type=Path, required=True)
    ap.add_argument("--beta-kontrol", type=float, default=None,
                    help="kontrol kolunun JSON'undaki beta (olcut 0b)")
    ap.add_argument("--beta-referans", type=float, default=ESIK_BETA_KONTROL,
                    help="kolun KAYITLI referansi (iki asamali 1.4112, "
                         "tek asamali 1.6175832)")
    ap.add_argument("--cikti", type=Path, default=None)
    a = ap.parse_args()

    K = oku(a.kontrol)
    H = oku(a.hasarli)

    print("=" * 70, flush=True)
    print("A17 — HASAR KOLU vs KONTROL  (olcut: docs/A17-HASAR-OLCUTU.md)",
          flush=True)
    print("=" * 70, flush=True)
    ad = ("t", "n_disari", "kutle_disari_kg", "p_eksen_hedef", "beta_bal",
          "n_hedef_ejekta", "n_bekleyen", "krater_derinlik", "D_max",
          "D_ort_hedef", "n_tam_kirik")
    print(f"  {'buyukluk':<20} {'KONTROL':>16} {'HASARLI':>16}", flush=True)
    for k in ad:
        print(f"  {k:<20} {K[k]:>16.6g} {H[k]:>16.6g}", flush=True)

    # --- 0. tesisat
    tesisat = H["D_max"] >= ESIK_D_MAX and H["n_tam_kirik"] > 0
    print(f"\n  [0]  tesisat: D_max = {H['D_max']:.4f}, tam kirik = "
          f"{H['n_tam_kirik']}  -> "
          f"{'HASAR KOSUYOR' if tesisat else 'GECERSIZ (hasar kosmuyor)'}",
          flush=True)

    # --- 0b. kontrol referansi
    ref = None
    if a.beta_kontrol is not None:
        sapma = abs(a.beta_kontrol - a.beta_referans) / a.beta_referans
        ref = sapma <= ESIK_BETA_TOL
        print(f"  [0b] kontrol beta = {a.beta_kontrol:.6f}  sapma "
              f"{100 * sapma:.3f}%  -> {'TUTTU' if ref else 'TUTMADI'}",
              flush=True)

    # --- 1. birincil
    oran = _oran(H["p_eksen_hedef"], K["p_eksen_hedef"])
    if oran >= ESIK_ORAN_DOGRULAR:
        yargi = "hasar_birinci_mertebe"
    elif oran < ESIK_ORAN_ELER:
        yargi = "hasar_sebep_degil"
    else:
        yargi = "kismi"
    print(f"\n  [1]  |p_eksen_hedef| H/K = {oran:.4g}  -> {yargi}", flush=True)

    # --- 2. ikincil
    print(f"  [2]  krater derinligi {K['krater_derinlik']:.4f} -> "
          f"{H['krater_derinlik']:.4f}   beta_bal {K['beta_bal']:.5f} -> "
          f"{H['beta_bal']:.5f}", flush=True)

    sonuc = {"kontrol": K, "hasarli": H, "oran_p_eksen_hedef": oran,
             "yargi": yargi, "tesisat_gecerli": bool(tesisat),
             "kontrol_referansi_tuttu": ref}
    if not tesisat:
        sonuc["uyari"] = ("hasar modeli kosmadi; [1] ve [2] SONUC DEGIL")
        print("\n  UYARI: tesisat sinavi gecmedi -> yukaridaki yargi "
              "OKUNMAZ.", flush=True)
    if a.cikti:
        a.cikti.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
