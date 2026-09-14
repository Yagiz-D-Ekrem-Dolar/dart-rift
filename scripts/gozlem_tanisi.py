"""Gözlenebilir tanısı — hangi durum dosyası hangi gözlenebilirde `nan`, NEDEN (A86).

`gozlem_vektoru` krater operatörünün `KeyError`/`ValueError`'ını yakalayıp
gözlenebilirleri **sebepsiz** `nan` yapıyor (A86: M2 ince `99991111`'de
merkez ışında `φ = 0,5` kesilmiyordu; sebep ancak elle çağırınca görüldü).
Bu betik aynı operatörü doğrudan çağırır ve istisna metnini kaydeder.
Kilitli gözlenebilirleri **değiştirmez**; yalnız tanı üretir.

Kullanim:
    python scripts/gozlem_tanisi.py --kok kampanya \\
        --desen "Ni_matris_sahne*.durumlar+N2i_matris_sahne*.durumlar" --json kampanya/S_tani_i.json
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))


def _krater_fn():
    from dartrift.observables.crater_shape import krater_yuzey_durumdan

    return krater_yuzey_durumdan


def tani(d, krater_fn=None) -> dict:
    """Tek durum: krater operatörü sonucu ya da istisna metni + geçerlilik."""
    krater_fn = krater_fn or _krater_fn()
    alan = set(getattr(d, "files", None) or d.keys())
    out = {"t": float(d["t"]) if "t" in alan else float("nan")}
    try:
        ky = krater_fn(d)
        out.update(krater="TAMAM", d_merkez=float(ky.derinlik_merkez),
                   V_krater=float(ky.hacim), R_krater=float(ky.yaricap))
    except (KeyError, ValueError) as e:
        out["krater"] = f"{type(e).__name__}: {e}"
    if "gecerlilik" in alan:
        try:
            out["gecerli"] = bool(json.loads(str(d["gecerlilik"]))["gecerli"])
        except (ValueError, KeyError, TypeError):
            out["gecerli"] = None
    return out


def hata_turu(metin: str) -> str:
    """İstisna metnini sayısal ayrıntılardan arındır: `(pencere: ...)` gibi kısımlar düşer."""
    return metin.split("(")[0].strip() if metin != "TAMAM" else "TAMAM"


def tara(kok: Path, desen: str, krater_fn=None) -> dict:
    kayitlar = []
    for ds in desen.replace("+", ",").split(","):
        for dz in sorted(glob.glob(str(kok / ds.strip()))):
            for f in sorted(glob.glob(dz + "/nokta_*.npz")):
                r = tani(np.load(f), krater_fn)
                r["dizin"] = Path(dz).name
                kayitlar.append(r)
    turler = Counter(hata_turu(r["krater"]) for r in kayitlar)
    return {"n": len(kayitlar), "n_krater_hata": sum(r["krater"] != "TAMAM" for r in kayitlar),
            "hata_turleri": dict(turler),
            "hatalilar": [r for r in kayitlar if r["krater"] != "TAMAM"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--desen", required=True, help="'+' ile ayrilmis (A84)")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = tara(a.kok, a.desen)
    print(f"GOZLEM TANISI: {out['n']} durum, krater hatasi {out['n_krater_hata']}")
    for t, n in sorted(out["hata_turleri"].items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {t}")
    for r in out["hatalilar"][:20]:
        print(f"  - {r['dizin']}: {r['krater']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
