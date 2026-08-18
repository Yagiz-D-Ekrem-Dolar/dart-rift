"""ADR-0043 gereksinim #4: **blok sınırları kaba çözünürlükte kalıyor.**

`refine_scene_local` ince bölgenin `α₀`/`Y₀`/`is_boulder` değerlerini
**en yakın kaba parçacıktan** örnekliyor. §4b bunu bir *"yaklaşım"*
diye işaretledi ve `ölçülmedi` dedi. Burada ölçülüyor.

## Neden önemli

`f_boulder` çıkarımın **üç parametresinden biri**. Kaya bloklarının
ince bölgede yanlış yere düşmesi, doğrudan çıkarılacak büyüklüğü
bozar. İnce bölge de tam olarak çarpma noktası — yani `β`'nın
üretildiği yer.

## Ölçüm

`assign_material` blok üyeliğini **herhangi bir noktada** hesaplayabilir
(küre listesine mesafe testi). Yani ince kafes için **kesin** cevap
bilinebiliyor:

| | |
|---|---|
| **kesin** | `assign_material(x_ince, boulders, …)` |
| **kullanılan** | en yakın kaba parçacıktan örnekleme |

İkisinin farkı, `refine_scene_local`'ın yaklaşım hatasıdır.

> Bu **geometrik** hatadır, dinamik etki değil. Blokların yanlış
> yerleşmesinin `β`'ya ne yaptığı ayrı bir koşu ister ve burada
> ölçülmüyor. Ölçülen şey *"ne kadar parçacık yanlış sınıflanıyor"*.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.rubble_generator import assign_material, build_rubble_pile  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE  # noqa: E402

#: `build_scene`in `rho0_solid` varsayilani. `build_rubble_pile` bunu
#: zorunlu tutuyor, `build_scene` ise varsayilanla veriyor; ikisi ayrisirsa
#: asagidaki kontrol yakalar.
RHO0_SOLID = 2700.0


def _cozulmus_malzeme(pile) -> dict:
    """`α₀`/`Y₀`'in **çözülmüş** matris ve blok değerlerini yığından oku.

    `build_scene`in imzasındaki varsayılanları kullanmak **çalışmıyor**:
    `matrix_alpha0` varsayılanı `None` ve gerçek değer
    `matrix_alpha0_for_bulk_density` ile içeride hesaplanıyor
    (`ρ_yığın` hedefini tutturmak için). İmzadan okumak `None` verir ve
    ilk denemem tam bunu yaptı — `TypeError: float - NoneType`.

    Değerleri **yığının kendisinden** okumak hem doğru hem de kaynak
    değişirse birlikte değişir.
    """
    ib = np.asarray(pile.is_boulder, bool)
    if not ib.any() or ib.all():
        raise ValueError("yığında hem blok hem matris olmalı; "
                         f"blok={int(ib.sum())}/{len(ib)}")
    out = {}
    for ad, dizi in (("alpha0", pile.alpha0), ("Y0", pile.Y0)):
        for etiket, sec in (("matrix", ~ib), ("boulder", ib)):
            v = np.unique(np.asarray(dizi)[sec])
            if len(v) != 1:
                raise ValueError(f"{etiket}_{ad} tek değer olmalı, {v} bulundu")
            out[f"{etiket}_{ad}"] = float(v[0])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lam", type=float, nargs="+", default=[2.0, 6.0, 19.0])
    ap.add_argument("--r-ince", type=float, default=25.0)
    ap.add_argument("--out", default=str(REPO.parent / "faz43e_sonuc.json"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("ADR-0043 #4 — BLOK SINIRLARININ KABA KALMASI (geometrik hata)",
          flush=True)
    print("=" * 78, flush=True)

    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    kaba = build_scene(spacing=7.0, device="cpu", **SAHNE)

    # KESIN blok alani: kaba sahneyle AYNI tohum ve parametrelerle
    # yeniden uretiliyor. `Scene` `boulders`i tasimadigi icin bu sart.
    pile = build_rubble_pile(
        mesh, spacing=7.0, bulk_density=SAHNE["bulk_density"],
        root_seed=SAHNE["root_seed"], model_class=SAHNE["model_class"],
        f_boulder=SAHNE["f_boulder"], q=SAHNE["q"],
        r_min=SAHNE["r_min"], r_max=SAHNE["r_max"], rho0_solid=RHO0_SOLID)
    var = _cozulmus_malzeme(pile)
    blk = pile.boulders
    if blk is None or len(blk.radii) == 0:
        print("  BLOK YOK — bu sahnede olculecek bir sey yok", flush=True)
        return 1
    # Kaba sahnenin blok atamasi YENIDEN URETIMLE ayni mi? Degilse
    # asagidaki her sey baska bir sahneyi olcer.
    ayni = np.array_equal(np.asarray(pile.is_boulder, bool),
                          np.asarray(kaba.is_boulder, bool)[~kaba.is_impactor])
    print(f"\nblok sayisi = {len(blk.radii)}, "
          f"yaricap {blk.radii.min():.2f}–{blk.radii.max():.2f} m", flush=True)
    print(f"yeniden uretim kaba sahneyle AYNI mi = {ayni}", flush=True)
    if not ayni:
        print("  UYARI: ayni degil — sonuclar baska bir blok alanina ait",
              flush=True)

    kayitlar = []
    print(f"\n{'lam':>5} {'s_ince':>8} {'n_ince':>8} {'YANLIS%':>8} "
          f"{'kutleli%':>9} {'f_blok(kes)':>12} {'f_blok(kul)':>12} "
          f"{'sapma%':>8}", flush=True)
    print("-" * 78, flush=True)
    for lam in a.lam:
        rs = refine_scene_local(kaba, mesh, r_ince=a.r_ince, lam=lam)
        ince = np.asarray(rs.is_fine, bool) & ~np.asarray(rs.is_impactor, bool)
        xi = rs.x[ince]
        kul_b = np.asarray(rs.is_boulder, bool)[ince]      # KULLANILAN
        a0_kes, y0_kes, kes_b = assign_material(
            xi, blk, var["matrix_alpha0"], var["matrix_Y0"],
            var["boulder_alpha0"], var["boulder_Y0"])      # KESIN

        mi = rs.m[ince]
        yanlis = kul_b != kes_b
        f_kes = float(np.sum(mi[kes_b]) / np.sum(mi))
        f_kul = float(np.sum(mi[kul_b]) / np.sum(mi))

        # DEJENERE DURUM. Ince bolgede hic blok yoksa `f_kes = f_kul = 0`
        # ve sapma `0/1e-300 = 0` cikiyor -- yani ekranda `%0,000` yaziyor
        # ve GECMIS gibi okunuyor. Oysa olculen hicbir sey yok.
        #
        # Ilk surumde tam bunu yaptim: `r_ince = 6 m` icin butun satirlar
        # `0.000` cikti ve bir an "hata yok" diye okudum. Carpma noktasinin
        # `6 m` cevresinde blok YOKTU. Bir sayi yerine `belirsiz` demek
        # dogrudur (RULES.txt).
        blok_var = bool(kes_b.any() or kul_b.any())
        k = {
            "lam": float(lam), "s_ince": float(rs.spacing_fine),
            "n_ince": int(ince.sum()),
            "blok_var": blok_var,
            "durum": "olculdu" if blok_var else "belirsiz",
            "not": "" if blok_var else (
                f"ince bolgede (r={a.r_ince} m) hic blok yok — "
                f"olculecek sinir yok"),
            "yanlis_oran": float(yanlis.mean()),
            "yanlis_kutle_oran": float(np.sum(mi[yanlis]) / np.sum(mi)),
            "f_blok_kesin": f_kes, "f_blok_kullanilan": f_kul,
            "f_blok_sapma": (abs(f_kul - f_kes) / f_kes if f_kes > 0.0
                             else float("nan")),
            # alpha0 dogrudan KUTLEYI belirliyor (m = rho0/alpha0 * V_p).
            "alpha0_bagil_hata_max": float(np.max(
                np.abs(rs.alpha0[ince] - a0_kes) / a0_kes)),
            "alpha0_bagil_hata_ort": float(np.average(
                np.abs(rs.alpha0[ince] - a0_kes) / a0_kes, weights=mi)),
        }
        kayitlar.append(k)
        if not blok_var:
            print(f"{lam:5.0f} {k['s_ince']:8.4f} {k['n_ince']:8d}  "
                  f"BELIRSIZ — ince bolgede blok yok", flush=True)
            continue
        print(f"{lam:5.0f} {k['s_ince']:8.4f} {k['n_ince']:8d} "
              f"{100 * k['yanlis_oran']:8.3f} "
              f"{100 * k['yanlis_kutle_oran']:9.3f} "
              f"{f_kes:12.5f} {f_kul:12.5f} "
              f"{100 * k['f_blok_sapma']:8.3f}", flush=True)

    print("-" * 78, flush=True)
    olculen = [z for z in kayitlar if z["durum"] == "olculdu"]
    if not olculen:
        print("\nHICBIR KOL OLCULEMEDI — kayit bulunamadi.", flush=True)
        print(f"  Carpma noktasinin {a.r_ince} m cevresinde blok yok; "
              f"`--r-ince` buyutun.", flush=True)
        Path(a.out).write_text(json.dumps(
            {"r_ince": a.r_ince, "n_blok": int(len(blk.radii)),
             "yeniden_uretim_ayni": bool(ayni), "durum": "belirsiz",
             "kayitlar": kayitlar}, indent=2, default=float))
        return 1
    en_kotu = max(olculen, key=lambda z: z["yanlis_oran"])
    print(f"\nEN KOTU: lam={en_kotu['lam']:.0f} -> "
          f"parcaciklarin %{100 * en_kotu['yanlis_oran']:.2f}'si YANLIS "
          f"siniflaniyor", flush=True)
    print(f"  f_boulder sapmasi     = %{100 * en_kotu['f_blok_sapma']:.3f} "
          f"-- CIKARIMIN UC PARAMETRESINDEN BIRI", flush=True)
    print(f"  alpha0 bagil hata ort = "
          f"{en_kotu['alpha0_bagil_hata_ort']:.5f}", flush=True)
    print("\nNOT: bu GEOMETRIK hata. Bloklarin yanlis yerlesmesinin "
          "beta'ya\n     etkisi AYRI bir kosu ister; burada OLCULMEDI.",
          flush=True)

    Path(a.out).write_text(json.dumps(
        {"r_ince": a.r_ince, "n_blok": int(len(blk.radii)),
         "yeniden_uretim_ayni": bool(ayni), "kayitlar": kayitlar},
        indent=2, default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
