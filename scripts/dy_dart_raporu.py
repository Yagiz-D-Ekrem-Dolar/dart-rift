"""Protokol DY — DART sahnesinin geç evre modeliyle ilk koşusu (KİLİTLİ; §4).

    I = |beta_model - 3,12| / sqrt(sigma_gozlem^2 + sigma_model^2)

- MODEL GOZLEME ULASIYOR : I < 3  ve  beta >= 3,12 - 0,34
- MODEL ASIYOR           : I >= 3 ve  beta > 3,12
- MODEL ULASMIYOR        : I >= 3 ve  beta < 3,12
- OKUNMAZ                : kosu gecersiz ya da 600 s'ye ulasmamis (beta yazilmaz)

sigma_model, `beta - 1` uzerinden OLCULMUS terimlerden kurulur
(tarih_esleme.model_eksikligi_kaynakli): gerceklem_beta, cozunurluk_uzak,
plato, carpma_yeri.

Kullanim:
    python scripts/dy_dart_raporu.py --kok kampanya --json kampanya/S_DY.json
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

AD = "DY_dart_g1p0"          # varsayilan kol (ilk kosu; A112 yuzunden OKUNMAZ)
AD_DY2 = "DY2_dart_g1p0"     # PROTOKOL-DY S6.2 tekrari (elipsoit, duzeltilmis)
AD_DK = "DK_kure_g1p0"       # PROTOKOL-DY S6.3 hacim-esdeger kure kolu
AD_DM = "DM_tekkure_g1p0"    # PROTOKOL-DY S7 tek kure mermi kolu
AD_DT = "DT_tohum2_g1p0"     # PROTOKOL-DY S7 ikinci sahne tohumu
T_END = 600.0
BETA_GOZLEM = 3.12            # PROTOKOL-U §1 (kilitli hedef)
SIGMA_GOZLEM = 0.34
KESME = 3.0
TERIMLER = ("gerceklem_beta", "cozunurluk_uzak", "plato", "carpma_yeri")


def oku(kok: Path, ad: str = AD) -> dict | None:
    d = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
    if not d:
        return None
    z = np.load(d[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    e = np.asarray(ft.get("impuls_egrisi") or [], dtype=np.float64)
    t_son = float(e[-1, 0]) if e.ndim == 2 and len(e) else float("nan")
    b2 = ft.get("beta_iki_yontem") or {}
    return {"beta": float(ft["beta_hedef"]), "t_son": t_son,
            "gecerli": bool(gc.get("gecerli", False)),
            "ulasti": bool(t_son >= T_END * 0.999),
            "n": int(len(z["m"])), "M_ejekta": float(ft.get("M_ejekta", float("nan"))),
            "beta_km": float(b2.get("beta_km", float("nan"))),
            "egri": ft.get("impuls_egrisi") or [], "dosya": d[-1]}


def yargi(v: dict | None) -> dict:
    from dartrift.inference.tarih_esleme import model_eksikligi_kaynakli
    out: dict = {"gozlem": {"beta": BETA_GOZLEM, "sigma": SIGMA_GOZLEM},
                 "kesme": KESME, "terimler": list(TERIMLER)}
    if v is None or not (v["gecerli"] and v["ulasti"]):
        out["genel"] = "OKUNMAZ (kosu yok, gecersiz ya da 600 s'ye ulasmamis)"
        out["kol"] = None if v is None else {k: v[k] for k in
                                             ("gecerli", "ulasti", "t_son", "n")}
        return out
    beta = v["beta"]
    sm = model_eksikligi_kaynakli(beta - 1.0, TERIMLER)
    payda = float(np.hypot(SIGMA_GOZLEM, sm["sigma"]))
    uygunsuzluk = abs(beta - BETA_GOZLEM) / payda
    if uygunsuzluk < KESME and beta >= BETA_GOZLEM - SIGMA_GOZLEM:
        genel = "MODEL GOZLEME ULASIYOR"
    elif beta > BETA_GOZLEM:
        genel = "MODEL ASIYOR"
    else:
        genel = "MODEL ULASMIYOR"
    out.update(beta=beta, beta_km=v["beta_km"], M_ejekta=v["M_ejekta"], n=v["n"],
               sigma_model=sm["sigma"], sigma_model_terimleri=sm["terimler"],
               payda=payda, I=uygunsuzluk, genel=genel, dosya=v["dosya"])
    if v["egri"]:
        from dartrift.observables.impuls_sekli import impuls_sekli
        out["sekil"] = impuls_sekli(v["egri"], t_ref=T_END)
    return out


def sigma_sekil(elips: dict | None, kure: dict | None) -> dict:
    """PROTOKOL-DY §6.3 (KİLİTLİ): `σ_şekil = |b_elipsoit − b_küre| / b_elipsoit`.

    `b = β − 1` (600 s). Bu **ölçülmüş** terim, `MODEL_EKSIKLIGI_KAYNAKLI`'daki
    literatürden ödünç `hedef_sekli = 0,20` yerine geçer (eski satır yerinde
    kalır). Bir kol geçersizse ya da 600 s'ye ulaşmadıysa **OKUNMAZ**.
    """
    for k in (elips, kure):
        if k is None or not (k["gecerli"] and k["ulasti"]):
            return {"genel": "OKUNMAZ (elipsoit ya da kure kolu gecersiz)",
                    "sigma_sekil": None}
    be, bk = elips["beta"] - 1.0, kure["beta"] - 1.0
    s = abs(be - bk) / abs(be)
    return {"sigma_sekil": s, "beta_elipsoit": elips["beta"],
            "beta_kure": kure["beta"], "b_elipsoit": be, "b_kure": bk,
            "eski_literatur_terimi": 0.20,
            "yorum": ("sekil terimi KUCUK (< 0,05): kuresel sahne savunulabilir"
                      if s < 0.05 else
                      "sekil terimi BUYUK (> 0,15): gercek sekil modeline (obj) "
                      "gecmek gerekir" if s > 0.15 else
                      "sekil terimi ORTA: olculmus deger butceye girer"),
            "genel": "OLCULDU"}


def _b(k) -> float | None:
    if k is None or not (k["gecerli"] and k["ulasti"]):
        return None
    return k["beta"] - 1.0


def sigma_mermi(dy2: dict | None, dm: dict | None) -> dict:
    """PROTOKOL-DY §7.3 (KİLİTLİ): `σ_mermi = |b_DY2 − b_DM| / b_DY2`.

    `mermi_geometrisi` teriminin (L9'dan ödünç `0,15`, doğrulaması `0`)
    bizim kodumuzdaki ölçülmüş karşılığı.
    """
    a, b = _b(dy2), _b(dm)
    if a is None or b is None or a == 0.0:
        return {"genel": "OKUNMAZ (uc kure ya da tek kure kolu gecersiz)",
                "sigma_mermi": None}
    return {"sigma_mermi": abs(a - b) / abs(a), "beta_uc_kure": 1.0 + a,
            "beta_tek_kure": 1.0 + b, "eski_literatur_terimi": 0.15,
            "genel": "OLCULDU"}


def sigma_gerceklem(dy2: dict | None, dt: dict | None) -> dict:
    """PROTOKOL-DY §7.3 (KİLİTLİ): iki tohumdan gerçeklem saçılması.

    `σ = |b₁ − b₂| / ortalama(b) / √2` — KAYIT-070 §1 ile **aynı** formül,
    ama bu kez **geç evre modelinde ve DART sahnesinde** (eskisi `0,1–0,2 s`
    eski modeldendi).
    """
    a, b = _b(dy2), _b(dt)
    if a is None or b is None or (a + b) == 0.0:
        return {"genel": "OKUNMAZ (tohum kollarindan biri gecersiz)",
                "sigma_gerceklem": None}
    ort = 0.5 * (a + b)
    return {"sigma_gerceklem": abs(a - b) / ort / (2 ** 0.5),
            "bagil_fark": abs(a - b) / ort, "beta_tohum1": 1.0 + a,
            "beta_tohum2": 1.0 + b, "eski_eski_model_terimi": 0.033,
            "genel": "OLCULDU"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--ad", default=AD, help=f"kol adi (varsayilan {AD})")
    ap.add_argument("--kure-kol", default=None,
                    help=f"verilirse sigma_sekil de olculur (ornek: {AD_DK})")
    ap.add_argument("--mermi-kol", default=None,
                    help=f"verilirse sigma_mermi olculur (ornek: {AD_DM})")
    ap.add_argument("--tohum-kol", default=None,
                    help=f"verilirse sigma_gerceklem olculur (ornek: {AD_DT})")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    elips = oku(a.kok, a.ad)
    out = yargi(elips)
    out["kol_adi"] = a.ad
    if a.kure_kol:
        out["sekil_olcumu"] = sigma_sekil(elips, oku(a.kok, a.kure_kol))
    if a.mermi_kol:
        out["mermi_olcumu"] = sigma_mermi(elips, oku(a.kok, a.mermi_kol))
    if a.tohum_kol:
        out["gerceklem_olcumu"] = sigma_gerceklem(elips, oku(a.kok, a.tohum_kol))
    print("=" * 72)
    print("PROTOKOL DY -- DART sahnesi, gec evre modeli (ilk kosu)")
    print("=" * 72)
    if "beta" in out:
        print(f"  beta = {out['beta']:.3f}   (beta_km {out['beta_km']:.3f}, N {out['n']})")
        print(f"  gozlem {BETA_GOZLEM} +- {SIGMA_GOZLEM};  sigma_model {out['sigma_model']:.3f}"
              f"  -> payda {out['payda']:.3f}")
        print(f"  I = {out['I']:.2f}  (kesme {KESME})")
        print(f"  M_ejekta {out['M_ejekta']:.3e} kg  (gozlem 1,6 +- 0,3e7)")
    if "sekil_olcumu" in out:
        so = out["sekil_olcumu"]
        if so.get("sigma_sekil") is None:
            print(f"  [sekil] {so['genel']}")
        else:
            print(f"  [sekil] beta elipsoit {so['beta_elipsoit']:.3f} / kure "
                  f"{so['beta_kure']:.3f}  ->  sigma_sekil = {so['sigma_sekil']:.3f} "
                  f"(literaturden odunc olan 0,20 yerine)")
            print(f"          {so['yorum']}")
    for anahtar, etiket, alan in (("mermi_olcumu", "mermi", "sigma_mermi"),
                                  ("gerceklem_olcumu", "gerceklem", "sigma_gerceklem")):
        if anahtar in out:
            o = out[anahtar]
            print(f"  [{etiket}] " + (o["genel"] if o.get(alan) is None else
                  f"{alan} = {o[alan]:.3f}"))
    print(f"GENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
