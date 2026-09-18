"""Protokol W — yayımlanmış SPH sonucuyla kıyas sınaması (KİLİTLİ).

Kural `docs/truba/PROTOKOL-W-KIYAS.md` §5'te, **koşudan önce** yazıldı:

    oran(Y0) = (beta_biz - 1) / (beta_L1 - 1)

- nicel:     `0,5 <= oran <= 2,0`  (faktor 2)
- egilim:    `beta(1 Pa) > beta(10 Pa) > beta(50 Pa)`
- saglamlik: `|beta(t_gecis=1,0) - beta(t_gecis=0,2)| / (beta(0,2) - 1) <= 0,20`

GENEL: uc `Y0` da bandda + egilim + saglamlik -> **KIYAS TUTTU**;
egilim var ve en fazla bir `Y0` band disinda -> **KISMI**; aksi -> **TUTMADI**.

Kaynak tablo (L1 = Raducan & Jutzi 2022, PSJ 3, 128, Tablo 2; kure, f = 0,6).

Kullanim:
    python scripts/w_kiyas_raporu.py --kok kampanya --json kampanya/S_W.json
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

#: L1 Tablo 2 (kure, dikey carpma, f = 0,6). `Y0 = 0` KOSULMUYOR (bkz. §2).
L1_BETA = {50.0: 3.63, 10.0: 4.18, 1.0: 4.66}
#: Kilitli tasarim: uc Y0 x iki gecis ani, tek tohum.
T_GECIS = (0.2, 1.0)
ORAN_ALT, ORAN_UST = 0.5, 2.0
SAGLAMLIK_ESIGI = 0.20
#: Dosya adi deseni: `W_Y50_g0p2.durumlar` (is betiginin urettigi ad).
#: A91 (2026-09-18): eski desen `[0-9p.]+` idi ve gercek addaki `.durumlar`
#: noktasini da sayiya katiyordu (`0p2.` -> `0.2.` -> ValueError). Sinavlar
#: adin sonunda `_kaba_...` olan sahte adlarla yazildigi icin gormedi; rapor
#: HICBIR beta okunmadan coktu, kilitli KURAL degismedi.
DESEN = re.compile(r"W_Y(?P<y0>[0-9]+(?:p[0-9]+)?)_g(?P<gecis>[0-9]+(?:p[0-9]+)?)")


def desen(onek: str = "W") -> re.Pattern:
    """`onek` (W, W2, ...) icin ad deseni -- kampanyalar birbirine karismasin."""
    if not re.fullmatch(r"W[0-9]*", onek):
        raise ValueError(f"onek 'W' ya da 'W<sayi>' olmali, {onek!r} geldi")
    return re.compile(rf"^{onek}_Y(?P<y0>[0-9]+(?:p[0-9]+)?)"
                      rf"_g(?P<gecis>[0-9]+(?:p[0-9]+)?)")


def _sayi(s: str) -> float:
    return float(s.replace("p", "."))


def topla(kok: Path, onek: str = "W") -> dict:
    """`{(Y0, t_gecis): kayit}` — her koşudan `β`, geçerlilik ve tanılar.

    `onek`: kampanya öneki (`W`, tekrar koşusu `W2`). Kural aynıdır; önek
    yalnız çıktıların karışmamasını sağlar.
    """
    out: dict = {}
    ds = desen(onek)
    for dz in sorted(glob.glob(str(kok / f"{onek}_*.durumlar"))):
        m = ds.search(Path(dz).name)
        if not m:
            continue
        anahtar = (_sayi(m.group("y0")), _sayi(m.group("gecis")))
        for f in sorted(glob.glob(dz + "/nokta_*.npz")):
            z = np.load(f)
            ft = json.loads(str(z["fizik_tani"]))
            gc = json.loads(str(z["gecerlilik"]))
            b2 = ft.get("beta_iki_yontem") or {}
            g = ft.get("gec_evre") or {}
            out[anahtar] = {
                "beta": float(ft["beta_hedef"]),
                "beta_eksi_1": float(ft["beta_hedef"]) - 1.0,
                "gecerli": bool(gc.get("gecerli", False)),
                "t_son": float(gc.get("degerler", {}).get("t", float("nan"))),
                "e_sapma": float(gc.get("degerler", {})
                                 .get("e_tot_bagil_sapma", float("nan"))),
                "M_ejekta": float(ft.get("M_ejekta", float("nan"))),
                "beta_km": float(b2.get("beta_km", float("nan"))),
                "mermi_bagsiz_kesri": float(
                    b2.get("mermi_bagsiz_kesri", float("nan"))),
                "koni_tam_acisi_derece": float(
                    b2.get("koni_tam_acisi_derece", float("nan"))),
                "dondurulmus": int(ft.get("dondurulmus", 0)),
                "gecis_adimi": int(g.get("adim_gecis", -1)),
                "A_gec": float(g.get("A_gec", float("nan"))),
                "dosya": f,
            }
    return out


def kapsam(veri: dict) -> dict:
    """Beklenen `3 × 2` koşu var mı ve geçerli mi (kural 8: beklediğini say)."""
    eksik, gecersiz = [], []
    for y0 in sorted(L1_BETA, reverse=True):
        for tg in T_GECIS:
            k = veri.get((y0, tg))
            if k is None:
                eksik.append(f"Y{y0:g}:g{tg:g}")
            elif not k["gecerli"]:
                gecersiz.append(f"Y{y0:g}:g{tg:g}")
    return {"tam": not eksik and not gecersiz, "eksik": eksik,
            "gecersiz": gecersiz}


def yargi(veri: dict) -> dict:
    """PROTOKOL-W §5 — kilitli karar."""
    satirlar: dict = {}
    for y0, b_l1 in sorted(L1_BETA.items(), reverse=True):
        esas = veri.get((y0, T_GECIS[0]))
        alt = veri.get((y0, T_GECIS[1]))
        s: dict = {"Y0_Pa": y0, "beta_L1": b_l1, "beta_eksi_1_L1": b_l1 - 1.0}
        if esas is None or not esas["gecerli"]:
            s["karar"] = "OKUNMAZ"
            satirlar[f"Y{y0:g}"] = s
            continue
        oran = esas["beta_eksi_1"] / (b_l1 - 1.0)
        s.update(beta=esas["beta"], beta_eksi_1=esas["beta_eksi_1"],
                 oran=float(oran),
                 karar=("BANDDA" if ORAN_ALT <= oran <= ORAN_UST else
                        "DUSUK" if oran < ORAN_ALT else "YUKSEK"),
                 beta_km=esas["beta_km"],
                 koni_tam_acisi_derece=esas["koni_tam_acisi_derece"],
                 M_ejekta=esas["M_ejekta"], e_sapma=esas["e_sapma"],
                 t_son=esas["t_son"], dondurulmus=esas["dondurulmus"])
        if alt is not None and alt["gecerli"] and esas["beta_eksi_1"] != 0.0:
            fark = abs(alt["beta_eksi_1"] - esas["beta_eksi_1"]) / abs(
                esas["beta_eksi_1"])
            s["saglamlik_farki"] = float(fark)
            s["saglam"] = bool(fark <= SAGLAMLIK_ESIGI)
        satirlar[f"Y{y0:g}"] = s

    okunur = {k: s for k, s in satirlar.items() if s.get("karar") != "OKUNMAZ"}
    # EGILIM: kohezyon azalinca beta artmali (1 Pa > 10 Pa > 50 Pa)
    sirali = [satirlar.get(f"Y{y:g}", {}).get("beta_eksi_1")
              for y in (1.0, 10.0, 50.0)]
    egilim = (all(t is not None and np.isfinite(t) for t in sirali)
              and sirali[0] > sirali[1] > sirali[2])
    band_disi = [k for k, s in okunur.items() if s["karar"] != "BANDDA"]
    saglam = [s.get("saglam") for s in okunur.values() if "saglam" in s]
    saglamlik = bool(saglam) and all(saglam)
    if len(okunur) < len(L1_BETA):
        genel = "OKUNMAZ (eksik ya da gecersiz kosu)"
    elif egilim and not band_disi and saglamlik:
        genel = "KIYAS TUTTU"
    elif egilim and len(band_disi) <= 1:
        genel = f"KISMI ({', '.join(band_disi) or 'saglamlik yok'})"
    else:
        genel = ("TUTMADI: " + ("egilim yok" if not egilim
                                else f"band disi {', '.join(band_disi)}"))
    return {"satirlar": satirlar, "egilim": bool(egilim),
            "saglamlik": saglamlik, "band_disi": band_disi, "genel": genel,
            "olcut": {"oran_alt": ORAN_ALT, "oran_ust": ORAN_UST,
                      "saglamlik_esigi": SAGLAMLIK_ESIGI,
                      "t_gecis": list(T_GECIS)}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--onek", default="W",
                    help="kampanya oneki (W; A92 sonrasi tekrar W2). Kural ayni.")
    a = ap.parse_args(argv)
    v = topla(a.kok, a.onek)
    out = yargi(v)
    out.update(kapsam(v))
    out["onek"] = a.onek
    print("=" * 78)
    print(f"PROTOKOL {a.onek} -- kiyas sinamasi ({len(v)} kosu; L1 Tablo 2)")
    print("=" * 78)
    for k, s in out["satirlar"].items():
        if s.get("karar") == "OKUNMAZ":
            print(f"  {k:>6}: OKUNMAZ")
            continue
        print(f"  {k:>6}  beta {s['beta']:.3f}  (L1 {s['beta_L1']:.2f})  "
              f"oran {s['oran']:.2f} -> {s['karar']}"
              + (f"  saglamlik {s['saglamlik_farki']:.2f}"
                 if "saglamlik_farki" in s else "  saglamlik YOK"))
    print(f"\nEGILIM: {'VAR' if out['egilim'] else 'YOK'}   "
          f"SAGLAMLIK: {'VAR' if out['saglamlik'] else 'YOK'}")
    print(f"GENEL: {out['genel']}")
    if out["eksik"] or out["gecersiz"]:
        print(f"KAPSAM: EKSIK {out['eksik']}  GECERSIZ {out['gecersiz']}")
    else:
        print("KAPSAM: TAM")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
