"""A17 — çarpma bölgesinde **hangi malzeme** duruyor?

## Neden bu ölçüm

A17'nin bütün elemeleri (`Y0` altı mertebe, yerçekimi, koşu süresi
`3000×`) `β = 1,411216`'yı **bit düzeyinde** değiştirmedi. Elemelerin
`Y0` kolu `scripts/faz48_iki_asama.py::_sahne_Y0` üzerinden koştu ve o
işlev **yalnızca `matrix_Y0`'ı** eziyor:

    return {**kw, "matrix_Y0": float(Y0)}

`build_scene`'in `boulder_Y0` varsayılanı `1,0e7 Pa` ve `SAHNE`
(`scripts/faz44_dart_yakinsama.py`) onu **hiç vermiyor**; `f_boulder =
0,25`, `r_min = 14 m`, `r_max = 42 m`, `radius = 82 m`. Yani hedefin
kütlece dörtte biri, bütün taramalar boyunca `1e7 Pa`'da **sabit**
kaldı — ve blok yarıçapları ölçülen kraterle (`≈15 m`) aynı mertebede,
hatta cismin yarıçapının yarısına kadar çıkıyor.

Buradan sınanabilir bir soru çıkıyor: *`Y0` taramaları çarpmanın
gerçekten gördüğü malzemeyi değiştirdi mi?*

## Ölçüt — **veriye bakılmadan** yazıldı

Bölge: çarpma noktası merkezli `r ≤ 15 m` (ölçülen krater ölçeği,
derinlik `15,28 m` / çap `≈14,8 m`), üretim tohumu `20260801`.

- blok kütle payı `>= %50` **veya** kütle ağırlıklı `Y0 >= 1e6 Pa`
  -> `Y0` taramaları çalışma noktasını **değiştirmemiş**; `boulder_Y0`
  sınanmamış bir adaydır.
- blok kütle payı `<= %10` **ve** kütle ağırlıklı `Y0 <= 1e5 Pa`
  -> çarpma matrise düşüyor; taramalar gerçek; bu aday **elenir**.
- arası -> kısmi; tek tohumla karar verilemez.

Tohum bağımlılığı ayrıca ölçülüyor: üretim tohumu tipik mi, yoksa
şanslı/şanssız bir çekiliş mi? (`--tohum-sayisi`)

## İkinci ölçüt — **çözünürlük tabanı** (yine veriye bakılmadan)

Üretim koşusu kaba sahneyi `r_iç = 25 m` içinde `λ₂ = 2` ile inceltiyor
(`faz48_iki_asama.py` varsayılanları). Ölçülen kraterin içinde kaç
**hedef** parçacık duruyor?

- `>= 100` -> kazı akışı ayrıklaştırmayla temsil ediliyor; eksik ejekta
  bir **sayım tabanı** yapaylığı değildir.
- `<= 20` -> ejekta öyle kaba nicemlenmiş ki `β` yalnızca büyük
  basamaklarla oynayabilir.
- arası -> kısmi.

## Bu ölçüm neyi **kanıtlamaz**

Bloğun orada olması `β`'yı bloğun tuttuğunu **göstermez** — onu ancak
`boulder_Y0` taraması gösterir ve o bir GPU koşusudur. Buradaki ölçüm
yalnızca *"taranan şey çarpmanın gördüğü şey miydi"* sorusunu
yanıtlıyor.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz44_dart_yakinsama import SAHNE  # noqa: E402

from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402

# Ölçülen krater (rapor A17 / A15): derinlik 15,28 m, çap ≈ 14,8 m.
KRATER_YARICAP_M = 15.0
# Gözlemi (β = 3,2225) üretmek için eksik olan ejekta momentumu.
GEREKEN_P = 6.449e6


def _bolge_ozeti(sc, yaricap: float) -> dict:
    hedef = ~sc.is_impactor
    d = np.linalg.norm(sc.x - sc.impact_point[None, :], axis=1)
    b = hedef & (d <= yaricap)
    m = sc.m[b]
    if m.size == 0:
        return {"yaricap_m": yaricap, "n": 0}
    blok = sc.is_boulder[b]
    return {
        "yaricap_m": yaricap,
        "n": int(m.size),
        "kutle_kg": float(m.sum()),
        "blok_kutle_payi": float(m[blok].sum() / m.sum()),
        "blok_sayi_payi": float(np.count_nonzero(blok) / m.size),
        "Y0_kutle_agirlikli_Pa": float(np.sum(sc.Y0[b] * m) / m.sum()),
        "Y0_medyan_Pa": float(np.median(sc.Y0[b])),
        "parcacik_kutlesi_medyan_kg": float(np.median(m)),
    }


# Uretim kosusunun asama-2 inceltmesi (faz48_iki_asama.py varsayilanlari).
R_INCE2_M = 25.0
LAM2 = 2.0
# Butun taramalarin dokunmadigi deger (build_scene varsayilani).
BOULDER_Y0_PA = 1.0e7
# FAZ 4.12 + KAYIT-049'da taranan matris mukavemetleri.
TARANAN_MATRIS_Y0 = (1.0, 10.0, 100.0, 3513.0, 1.0e4, 2.15e6)


def _tarama_etkisi(blok_kutle_payi: float) -> dict:
    """Matris taramasi bolgenin kutle agirlikli `Y0`'ini ne kadar oynatiyor.

    Bu bir **sinav degil**, olculmus `blok_kutle_payi`'nin aritmetik
    sonucu: bloklar `1e7 Pa`'da sabit kaldigi icin ortalamanin blok
    terimi taramadan **bagimsiz**.
    """
    f = float(blok_kutle_payi)
    d = {f"{y:.6g}": f * BOULDER_Y0_PA + (1.0 - f) * y
         for y in TARANAN_MATRIS_Y0}
    v = list(d.values())
    return {"kutle_agirlikli_Y0_Pa": d, "oran_max_min": max(v) / min(v)}


def olc(tohum: int, spacing: float, ince: bool = False) -> dict:
    kw = {**SAHNE, "root_seed": int(tohum)}
    sc = build_scene(spacing=spacing, device="cpu", **kw)
    if ince:
        mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
        sc = refine_scene_local(sc, mesh, r_ince=R_INCE2_M, lam=LAM2)
    hedef = ~sc.is_impactor
    mh = sc.m[hedef]
    return {
        "tohum": int(tohum),
        "ince": bool(ince),
        "spacing_m": float(getattr(sc, "spacing", None)
                           or sc.spacing_fine),
        "n_toplam": int(sc.n),
        "hedef_kutlesi_kg": float(mh.sum()),
        "blok_kutle_payi_KURE": float(
            mh[sc.is_boulder[hedef]].sum() / mh.sum()),
        "parcacik_kutlesi_medyan_kg": float(np.median(mh)),
        "bolgeler": [_bolge_ozeti(sc, r)
                     for r in (8.0, KRATER_YARICAP_M, 25.0)],
    }


def bas(sonuc: dict) -> None:
    print("\n=== A17 — carpma bolgesinin malzemesi ===", flush=True)
    print(f"  tohum {sonuc['tohum']}  spacing {sonuc['spacing_m']:.3f} m  "
          f"N = {sonuc['n_toplam']}", flush=True)
    print(f"  KURE genelinde blok kutle payi = "
          f"{sonuc['blok_kutle_payi_KURE']:.4f}  (f_boulder = 0,25)",
          flush=True)
    print(f"  hedef parcacik kutlesi medyan  = "
          f"{sonuc['parcacik_kutlesi_medyan_kg']:.4e} kg", flush=True)
    print("\n  bolge      n    blok(kutle)  blok(sayi)   Y0_agirlikli  "
          "Y0_medyan", flush=True)
    for b in sonuc["bolgeler"]:
        if b["n"] == 0:
            print(f"  r<={b['yaricap_m']:4.0f} m   0   (bos)", flush=True)
            continue
        print(f"  r<={b['yaricap_m']:4.0f} m {b['n']:4d}   "
              f"{b['blok_kutle_payi']:9.4f}   {b['blok_sayi_payi']:9.4f}   "
              f"{b['Y0_kutle_agirlikli_Pa']:12.4e}  {b['Y0_medyan_Pa']:.4e}",
              flush=True)


def yargi(sonuc: dict) -> str:
    b = next(x for x in sonuc["bolgeler"]
             if x["yaricap_m"] == KRATER_YARICAP_M)
    if b["n"] == 0:
        return "olculemedi"
    if b["blok_kutle_payi"] >= 0.50 or b["Y0_kutle_agirlikli_Pa"] >= 1.0e6:
        return "taramalar_calisma_noktasini_degistirmemis"
    if b["blok_kutle_payi"] <= 0.10 and b["Y0_kutle_agirlikli_Pa"] <= 1.0e5:
        return "aday_elendi"
    return "kismi"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--tohum-sayisi", type=int, default=1)
    ap.add_argument("--cikti", type=Path, default=None)
    a = ap.parse_args()

    uretim = olc(SAHNE["root_seed"], a.spacing)
    bas(uretim)
    y = yargi(uretim)
    print(f"\n  YARGI-1 (uretim tohumu, kaba sahne) = {y}", flush=True)

    kb = next(x for x in uretim["bolgeler"]
              if x["yaricap_m"] == KRATER_YARICAP_M)
    te = _tarama_etkisi(kb["blok_kutle_payi"])
    print()
    print("  MATRIS TARAMASININ BOLGEYE ETKISI (aritmetik, sinav degil)", flush=True)
    for k, v in te["kutle_agirlikli_Y0_Pa"].items():
        print(f"    matrix_Y0 = {k:>10} Pa  ->  bolge <Y0> = {v:.4e} Pa",
              flush=True)
    print(f"    alti mertebelik tarama bolgeyi {te['oran_max_min']:.4f} kat "
          f"oynatiyor", flush=True)

    ince = olc(SAHNE["root_seed"], a.spacing, ince=True)
    bas(ince)
    ib = next(x for x in ince["bolgeler"]
              if x["yaricap_m"] == KRATER_YARICAP_M)
    n_kr = ib["n"]
    y2 = ("cozunurluk_yeterli" if n_kr >= 100
          else "nicemleme_tabani" if n_kr <= 20 else "kismi")
    print()
    print(f"  YARGI-2 (uretim inceltmesi, r<=15 m'de n = {n_kr}) = {y2}", flush=True)

    p_par = ib["parcacik_kutlesi_medyan_kg"]
    print(f"\n  gereken ejekta momentumu = {GEREKEN_P:.4e} kg m/s", flush=True)
    for v in (1.0, 10.0, 100.0):
        kg = GEREKEN_P / v
        print(f"    {v:6.1f} m/s'de -> {kg:.4e} kg = "
              f"{kg / p_par:8.2f} parcacik", flush=True)

    dagilim = None
    if a.tohum_sayisi > 1:
        tohumlar = [SAHNE["root_seed"] + i for i in range(a.tohum_sayisi)]
        hepsi = [olc(t, a.spacing) for t in tohumlar]
        paylar = [next(x for x in s["bolgeler"]
                       if x["yaricap_m"] == KRATER_YARICAP_M)
                  ["blok_kutle_payi"] for s in hepsi]
        dagilim = {"tohumlar": tohumlar, "blok_kutle_paylari": paylar,
                   "yargilar": [yargi(s) for s in hepsi]}
        print(f"\n  {len(tohumlar)} tohumda r<=15 m blok kutle payi: "
              f"min {min(paylar):.4f}  medyan {np.median(paylar):.4f}  "
              f"max {max(paylar):.4f}", flush=True)

    if a.cikti:
        a.cikti.write_text(json.dumps(
            {"uretim": uretim, "yargi_1": y, "ince": ince,
             "yargi_2": y2, "tarama_etkisi": te,
             "dagilim": dagilim},
            ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
