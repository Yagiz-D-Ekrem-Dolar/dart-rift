"""Protokol HT — kilitli Hera krater tahmini (ön kayıt, Faz 6 iskeleti).

Bitiş 3 posterioru (ya da gözlem önsel dışıysa önsel, **açıkça etiketli**)
üzerinden krater gözlenebilirlerinin **öngörü dağılımı** hesaplanır ve
değiştirilemez bir kayda yazılır:

1. `β` gözlemiyle ağırlıklar: `dart_gozlem_posterior` ile aynı vekil, gürültü
   ve önsel kapsama kuralı. **ÖNSEL İÇİNDE** → posterior ağırlığı;
   **ÖNSEL DIŞI** → düzgün önsel ve kayda `KOSULSUZ (gozlem onsel disi)`.
2. Her krater gözlenebilirı için ikinci derece vekil (dönüşümlü birimde),
   θ-gruplu 4-kat artık sapması `σ_vekil` ve verilirse `σ_çöz`.
3. `N_ORNEK` örnek: ızgara düğümü ağırlığa göre, üstüne `N(0, σ_vekil² + σ_çöz²)`;
   kantiller doğal birime geri dönüştürülür.
4. Kayıt: tahmin + meta (git commit, havuz deseni, koşu sayısı, `t_end`,
   UTC zaman) ve içeriğin SHA-256'sı. **Aynı adla ikinci kez yazılmaz.**

Bu bir **mekanizma**dır: modelin `t_end` anındaki krateri, Hera'nın ölçeceği
son krater değildir (düşük yerçekiminde krater oluşumu çok daha uzun sürer;
model yerçekimsiz). Kayıt bunu `uyari` alanında taşır.

Kullanim:
    python scripts/hera_tahmin.py --kok kampanya \\
        --desen "Nto_matris_sahne*.durumlar+N2to_matris_sahne*.durumlar" \\
        --cozunurluk kampanya/S_cozunurluk_Mt_orta.json --etiket Qo --cikti-dizini kampanya
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402

GOZLEMLER_H = ("R_krater", "V_krater", "M_ejekta")
KANTILLER = (0.05, 0.16, 0.5, 0.84, 0.95)
N_IZGARA = 32
N_ORNEK = 20000
TOHUM = 20260914
UYARI = ("Model krateri t_end anindaki krater; Hera'nin olcecegi SON krater degildir "
         "(dusuk yercekiminde krater olusumu cok daha uzun surer, model yercekimsiz).")


def geri_donustur(gozlem: str, y):
    import p_kalibrasyon_raporu as pr

    kip = pr.DONUSUMLER[gozlem][0]
    y = np.asarray(y, float)
    return 10.0 ** y if kip == "log10" else y


def agirliklar(X, y_beta, grup, gozlem: dict, *, sigma_coz: float = 0.0,
               n_grid: int = N_IZGARA) -> tuple[np.ndarray, str, dict]:
    import dart_gozlem_posterior as dg

    d = dg.uygula(X, y_beta, grup, gozlem, sigma_coz=sigma_coz, n_grid=n_grid)
    if d["kapsama"]["karar"] != "ONSEL ICINDE":
        w = np.full(n_grid ** 3, 1.0 / n_grid ** 3)
        return w, f"KOSULSUZ (gozlem onsel disi: {d['kapsama']['karar']})", d
    import p_kalibrasyon_raporu as pr

    from dartrift.inference.surrogate import fit_surrogate

    v = fit_surrogate(DART_UZAYI_S3, np.asarray(X, float), np.asarray(y_beta, float))
    t = pr._izgara_tasarimi(n_grid) @ v.coef
    s = d["sigma_toplam_log"]
    lp = -0.5 * (t - gozlem["y_log"]) ** 2 / s ** 2
    w = np.exp(lp - lp.max())
    return w / w.sum(), "POSTERIOR (beta gozlemiyle kosullu)", d


def ongoru(X, Y, grup, w, adlar, *, sigma_coz: dict | None = None,
           n_grid: int = N_IZGARA, n_ornek: int = N_ORNEK, tohum: int = TOHUM) -> dict:
    import p_kalibrasyon_raporu as pr

    from dartrift.inference.surrogate import fit_surrogate

    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    rng = np.random.default_rng(tohum)
    A = pr._izgara_tasarimi(n_grid)
    idx = rng.choice(len(w), size=n_ornek, p=w)
    out = {}
    for i, g in enumerate(adlar):
        y = Y[:, i]
        v = fit_surrogate(DART_UZAYI_S3, X, y)
        s_v = float(np.std(pr.kfold_artiklari(X, y, grup), ddof=1))
        s_c = float((sigma_coz or {}).get(g, 0.0))
        s = math.hypot(s_v, s_c)
        orn = (A @ v.coef)[idx] + rng.normal(0.0, s, n_ornek)
        q = np.quantile(orn, KANTILLER)
        out[g] = {"kantiller": dict(zip([f"q{int(k * 100):02d}" for k in KANTILLER],
                                        geri_donustur(g, q).tolist(), strict=True)),
                  "sigma_vekil": s_v, "sigma_coz": s_c, "q2_vekil": v.q2,
                  "donusum": pr.DONUSUMLER[g][0]}
    return out


def kayit_olustur(tahmin: dict, meta: dict) -> dict:
    govde = {"tahmin": tahmin, "meta": meta}
    ham = json.dumps(govde, sort_keys=True, ensure_ascii=False, default=float)
    return {**govde, "sha256": hashlib.sha256(ham.encode("utf-8")).hexdigest()}


def dogrula(kayit: dict) -> bool:
    govde = {"tahmin": kayit["tahmin"], "meta": kayit["meta"]}
    ham = json.dumps(govde, sort_keys=True, ensure_ascii=False, default=float)
    return hashlib.sha256(ham.encode("utf-8")).hexdigest() == kayit["sha256"]


def kaydet(kayit: dict, yol: Path) -> Path:
    if yol.exists():
        raise FileExistsError(f"on kayit UZERINE YAZILMAZ: {yol}")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(kayit, indent=1, ensure_ascii=False, default=float),
                   encoding="utf-8")
    return yol


def _commit() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_BURASI.parent,
                       capture_output=True, text=True, check=False)
    return r.stdout.strip() or "BILINMIYOR"


def main(argv=None) -> int:
    import dart_gozlem_posterior as dg
    import p_kalibrasyon_raporu as pr

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--desen", required=True, help="'+' ile ayrilmis (A84)")
    ap.add_argument("--cozunurluk", type=Path, default=None)
    ap.add_argument("--etiket", required=True)
    ap.add_argument("--cikti-dizini", type=Path, required=True)
    a = ap.parse_args(argv)
    desen = a.desen.replace("+", ",")
    sahne = dg.sahne_buyuklukleri(a.kok, a.desen)
    gozlem = dg.gozlenen_beta(sahne["hedef_kutlesi"], sahne["p_imp"])
    kayit = pr.kayitlari_oku(a.kok, desen)
    adlar = ["beta_eksi_1", *GOZLEMLER_H]
    X, Y = pr._matrisler(kayit, adlar)
    grup = pr._gruplar(X)
    coz = {}
    if a.cozunurluk and a.cozunurluk.exists():
        cj = json.loads(a.cozunurluk.read_text(encoding="utf-8"))["gozlem"]
        coz = {g: float(cj[g]["sigma_coz"]) for g in adlar
               if g in cj and np.isfinite(cj[g].get("sigma_coz", float("nan")))}
    w, kosul, d = agirliklar(X, Y[:, 0], grup, gozlem, sigma_coz=coz.get("beta_eksi_1", 0.0))
    tahmin = ongoru(X, Y[:, 1:], grup, w, list(GOZLEMLER_H), sigma_coz=coz)
    t_end = None
    for ds in desen.split(","):
        f = sorted(glob.glob(str(a.kok / ds.strip() / "nokta_*.npz")))
        if f:
            t_end = float(np.load(f[0])["t"])
            break
    meta = {"etiket": a.etiket, "kosul": kosul, "onsel_kapsama": d["kapsama"]["karar"],
            "gozlem": gozlem, "desen": a.desen, "n_kosu": int(len(X)), "t_end_s": t_end,
            "cozunurluk_terimleri": coz, "kod_commit": _commit(),
            "zaman_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "uyari": UYARI, "protokol": "docs/truba/PROTOKOL-HT-HERA-TAHMIN.md"}
    k = kayit_olustur(tahmin, meta)
    yol = kaydet(k, a.cikti_dizini / f"ONKAYIT_HERA_{a.etiket}.json")
    print("=" * 78)
    print(f"HERA ON KAYDI {a.etiket} -- {kosul}")
    print("=" * 78)
    for g, t in tahmin.items():
        print(f"  {g:>9}: " + "  ".join(f"{q} {v:.4g}" for q, v in t["kantiller"].items()))
    print(f"  t_end {t_end} s, {len(X)} kosu, sha256 {k['sha256'][:16]}...")
    print(f"  UYARI: {UYARI}")
    print(f"yazildi: {yol}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
