"""FAZ 4.12 — `Y0` **derinlikte** görünüyor mu, ve durumları **kaydet**.

FAZ 4.11 ölçtü: `Y0` dört mertebe (`10³ → 10⁷ Pa`) değişirken `β`
`0,001` oynuyor ve hedef ejektası `0,1 kg` bile değişmiyor. Yani `Y0`
`β`'ya **yazılmıyor**.

Bir ihtimal kaldı: **krater derinliği**. Mukavemet krater kazısının
**geç** evresinde belirleyici olur; `β` ise çarpma anının eşlenmesinde
belirlenip donuyor (`t ≤ 0,127 s`'de bit düzeyinde sabit). Derinlik
`β`'nın göremediğini görebilir.

> Cevap **iki yönde de** karar veriyor:
> `Y0` derinlikte görünüyorsa → çıkarım uzayı olduğu gibi kalır.
> Görünmüyorsa → `Y0` uzaydan çıkarılmalı ya da daha uzun koşulmalı;
> ikisi de ADR gerektirir.

## Her nokta **diske yazılıyor**

Bu turda **üç kez** kaydedilmiş bir duruma ihtiyaç duydum ve elimde
yalnızca özet vardı; her seferinde saatlerce yeniden koştum. Diziler
`~1 MB`, koşu saatler. Bundan sonra yeni bir gözlenebilir sorusu
**koşu gerektirmeyecek**.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402
from dartrift.inference.forward import (  # noqa: E402
    GOZLENEBILIRLER,
    KRATER_AYARLARI_DART,
    ileri_kosu_ikiasama,
)
from dartrift.observables.crater_shape import crater_profile  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402
from faz48_iki_asama import T1_OLCULEN  # noqa: E402
from faz411_gozlenebilir_duyarliligi import ZAYIF_ESIGI, koseler  # noqa: E402


def _krater_ayarlari(n_bins: int | None) -> dict:
    """`KRATER_AYARLARI_DART`in kopyasi; istenirse `n_bins` ezilir.

    Uretim ayarlari **degistirilmiyor**: varsayilan `None` geldiginde
    sozluk birebir ayni. A11 icin `lam2 = 4` ile `n_bins = 16`
    denenebilsin diye bir kol acildi.
    """
    ayar = dict(KRATER_AYARLARI_DART)
    if n_bins is not None:
        if n_bins < 4:
            raise ValueError(f"n_bins en az 4 olmali, {n_bins} geldi")
        ayar["n_bins"] = int(n_bins)
    return ayar


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--t-end", type=float, default=0.2)
    ap.add_argument("--nokta", type=int, default=9)
    ap.add_argument("--n-lhs", type=int, default=0,
                    help="koselerin USTUNE bu kadar LHS noktasi ekle "
                         "(FAZ 4.6'nin egitim kumesi icin)")
    ap.add_argument("--root-seed", type=int, default=20260810)
    # A11: `krater_capi` OLU (40 durumun hepsinde 6,69 m, sifir yayilim).
    # Kok neden nicemleme: `lam2 = 2`de yalnizca `n_bins = 8` calisiyor,
    # o da +-1,5 derece -> capta +-4,3 m. `lam2 = 4`te `n_bins = 16`
    # aciliyor (+-0,75 derece -> +-2,1 m). Bu iki bayrak o olcumu
    # kosulabilir yapiyor; varsayilanlar URETIM degerleri, degismedi.
    ap.add_argument("--lam2", type=float, default=2.0,
                    help="asama-2 inceltmesi (uretim 2; A11 icin 4)")
    ap.add_argument("--n-bins", type=int, default=None,
                    help="krater acisal kutu sayisi (uretim 8; "
                         "lam2=4 ile 16 denenebilir)")
    ap.add_argument("--durum-dizin", default=str(Path.home() / "faz412_durumlar"))
    ap.add_argument("--out", default=str(Path.home() / "faz412.json"))
    a = ap.parse_args()

    uzay = DART_UZAYI_S3
    X = koseler(uzay, a.nokta)
    if a.n_lhs > 0:
        # Koseler duyarliligi, LHS ic yapiyi verir. Vekil ikisine de
        # ihtiyac duyar: kose olmadan ucdegerler, LHS olmadan egrilik
        # ogrenilemez.
        from dartrift.inference.design import lhs_design
        X = np.vstack([X, lhs_design(uzay, a.n_lhs, root_seed=a.root_seed)])
    dz = Path(a.durum_dizin)
    dz.mkdir(parents=True, exist_ok=True)
    print("=" * 78, flush=True)
    print(f"FAZ 4.12 — Y0 DERINLIKTE GORUNUYOR MU  ({len(X)} nokta, "
          f"t_end={a.t_end})", flush=True)
    print(f"durumlar: {dz}", flush=True)
    print("=" * 78, flush=True)

    t0 = time.perf_counter()
    derinlikler: dict[int, float] = {}
    caplar: dict[int, float] = {}

    def kaydet(i, th, st, sahne, x_ref, a1):
        yol = dz / f"nokta_{i:02d}.npz"
        hedef = ~np.asarray(sahne.is_impactor, dtype=bool)
        np.savez_compressed(
            yol, x=st["x"], v=st["v"], m=st["m"], x_referans=x_ref,
            hedef=hedef, theta=np.asarray(th),
            R=float(a1.target_radius), M=float(a1.target_mass),
            p_imp=np.asarray(a1.impactor_momentum),
            d_imp=np.asarray(a1.impact_direction))
        # Derinlik: EKSEN kipinde, hemen olculuyor (post-hoc da olabilir).
        try:
            kr = crater_profile(
                np.asarray(st["x"])[hedef], center=np.zeros(3),
                impact_direction=np.asarray(a1.impact_direction),
                reference_radius=float(a1.target_radius),
                x_reference=np.asarray(x_ref)[hedef],
                **_krater_ayarlari(a.n_bins))
            derinlikler[i] = float(kr.depth)
            # A11: CAP da kaydediliyor. Daha once yalnizca derinlik
            # tutuluyordu ve capin olu olup olmadigi ensemble ciktisindan
            # OKUNAMIYORDU -- her turda ayri bir betikle bakiliyordu.
            caplar[i] = float(kr.diameter)
        except Exception as e:                              # noqa: BLE001
            derinlikler[i] = float("nan")
            caplar[i] = float("nan")
            print(f"      krater OLCULEMEDI: {str(e)[:70]}", flush=True)

    def ilerleme(i, n, mesaj):
        d = derinlikler.get(i, float("nan"))
        print(f"  [{i + 1}/{n}] {mesaj}  derinlik={d:.4f}  "
              f"({time.perf_counter() - t0:.0f} s)", flush=True)

    Y = ileri_kosu_ikiasama(
        X, material=_malzeme(), device=a.device, t1=T1_OLCULEN,
        t_end=a.t_end, r1=3.0, lam1=19.0, r2=25.0, lam2=a.lam2,
        spacing=7.0, sahne_taban=SAHNE, ilerleme=ilerleme,
        durum_kaydi=kaydet)

    D = np.array([derinlikler.get(i, np.nan) for i in range(len(X))])
    C = np.array([caplar.get(i, np.nan) for i in range(len(X))])
    print(f"\n{'=' * 78}", flush=True)
    print(f"{'#':>2} " + " ".join(f"{ad:>14}" for ad in uzay.names)
          + f" {'beta':>9} {'derinlik':>9} {'cap':>9}", flush=True)
    print("-" * 78, flush=True)
    for i, (x, y) in enumerate(zip(X, Y, strict=False)):
        print(f"{i:2d} " + " ".join(f"{v:14.5g}" for v in x)
              + f" {y[0]:9.5f} {D[i]:9.4f} {C[i]:9.4f}", flush=True)

    # A11 -- CAP OLU MU? Yayilim burada, ciktinin ICINDE raporlaniyor;
    # daha once ayri bir betikle bakiliyordu ve her turda unutuluyordu.
    sonlu = C[np.isfinite(C)]
    if sonlu.size:
        yay = float(sonlu.max() - sonlu.min())
        bagil = yay / max(abs(float(np.mean(sonlu))), 1e-30)
        print(f"KRATER CAPI: {sonlu.size} sonlu deger, aralik "
              f"{sonlu.min():.4f} - {sonlu.max():.4f} m, yayilim "
              f"{yay:.4f} m ({100 * bagil:.2f}%)", flush=True)
        # SEVIYE sayisi, `np.unique` DEGIL. Ilk surum `np.unique(sonlu)`
        # kullaniyordu ve `40` dondurmustu -- oysa degerler `2` ayri
        # seviyede toplaniyordu (`5,4032` ve `7,4916`); aradaki fark
        # `1e-4 m`'nin altinda, yani KAYAN NOKTA GURULTUSU. Gosterge
        # "canli" derken aslinda gurultu sayiyordu.
        tol = 0.01
        s = np.sort(sonlu)
        seviye = 1
        for onceki, simdiki in zip(s, s[1:], strict=False):
            if simdiki - onceki > tol:
                seviye += 1
        print(f"  ayri seviye sayisi (tol {tol} m) = {seviye}"
              f"  -> {'OLU' if seviye <= 2 else 'CANLI'}", flush=True)
    else:
        print("KRATER CAPI: hicbir noktada olculemedi", flush=True)

    print("\nPARAMETRE ETKILERI (kose ortalamalari)", flush=True)
    print(f"{'parametre':>16} {'beta farki':>12} {'derinlik farki':>15}",
          flush=True)
    print("-" * 46, flush=True)
    etki = {}
    for j, ad in enumerate(uzay.names):
        dus = X[:, j] == X[:, j].min()
        yuk = X[:, j] == X[:, j].max()
        db = float(np.nanmean(Y[yuk, 0]) - np.nanmean(Y[dus, 0]))
        dd = float(np.nanmean(D[yuk]) - np.nanmean(D[dus]))
        etki[ad] = {"beta": db, "derinlik": dd}
        print(f"{ad:>16} {db:+12.5f} {dd:+15.4f}", flush=True)

    ok = np.isfinite(D)
    bagil = (float((D[ok].max() - D[ok].min()) / max(abs(np.mean(D[ok])), 1e-300))
             if ok.sum() > 1 else float("nan"))
    print(f"\nderinlik bagil yayilim = {bagil:.4e}  (esik {ZAYIF_ESIGI})",
          flush=True)

    y0_dd = abs(etki.get("Y0", {}).get("derinlik", 0.0))
    en_buyuk = max(abs(v["derinlik"]) for v in etki.values()) or 1.0
    print(f"\n{'=' * 78}", flush=True)
    if not ok.any():
        print("SONUC: derinlik hic olculemedi — yargi YOK.", flush=True)
    elif y0_dd >= 0.3 * en_buyuk:
        print("SONUC: Y0 DERINLIKTE GORUNUYOR -> cikarim uzayi kalabilir.",
              flush=True)
    else:
        print(f"SONUC: Y0 derinlikte de GORUNMUYOR (etkisi en buyugun "
              f"%{100 * y0_dd / en_buyuk:.0f}'i).", flush=True)
        print("  -> Y0 uzaydan cikarilmali YA DA daha uzun kosulmali (ADR).",
              flush=True)

    Path(a.out).write_text(json.dumps(
        {"uzay": list(uzay.names), "t_end": a.t_end, "X": X.tolist(),
         "Y": Y.tolist(), "derinlik": D.tolist(), "cap": C.tolist(),
         "etki": etki,
         "gozlenebilirler": list(GOZLENEBILIRLER),
         "krater_ayarlari": KRATER_AYARLARI_DART,
         "durum_dizin": str(dz),
         "duvar_s": time.perf_counter() - t0}, indent=2), encoding="utf-8")
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
