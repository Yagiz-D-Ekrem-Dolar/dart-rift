"""Kampanya durum dosyalarına **fiziksel yüzey operatörünü** uygula (A73).

Uzman (2026-09-11): mevcut `krater_derinlik` bir yüzey değil; dış
kabuk sabitken `0,49 m` üretiyor, yeniden örneklemeyle `0,34 → 0,71 m`
oynuyor. Yeni operatör (`krater_yuzey`) bu sınavları geçiyor
(`tests/test_krater_yuzey.py`).

Bu betik mevcut kampanyaların (G1, G2, I, J, I2 ...) durum dosyalarını
**yeniden okuyor** — yeni koşu gerekmez. Her kol için:

- nokta başına eski ve yeni derinlik, yarıçap, hacim, ayrılan sayısı;
- `ρ(yeni derinlik, log Y₀)` ve blok eksenleri (permütasyon `p`);
- Protokol I'nın sigmoid + jackknife `x₀`'ı (yeni derinlikte).

> **BETİMLEYİCİ.** Hiçbir kilitli protokolün yargısı bu betikle
> değişmez; o yargılar eski gözlenebilir üzerinden kilitlendi. Bu
> çıktı *"gözlenebilir düzeltilince tablo nasıl görünüyor"* sorusunu
> yanıtlıyor.

Kullanim:
    python scripts/yuzey_krater_raporu.py --kol G1 'kampanya/G1_uretim_sahne*.durumlar' \\
        --kol I 'kampanya/I_orta_sahne*.durumlar' --json yuzey.json
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


def nokta_olc(yol: Path, *, eski: bool = True) -> dict:
    """Tek durum dosyası → ölçüler (hata olursa `hata` alanı)."""
    from dartrift.observables.crater_shape import krater_yuzey_durumdan

    z = np.load(yol)
    k = {"dosya": yol.name,
         "theta": np.asarray(z["theta"], dtype=np.float64).ravel().tolist()}
    try:
        ky = krater_yuzey_durumdan(z)
        k.update(derinlik=ky.derinlik, derinlik_merkez=ky.derinlik_merkez,
                 yaricap=ky.yaricap, hacim=ky.hacim,
                 n_ayrilan=ky.n_ayrilan, kuresel_dusus=ky.kuresel_dusus,
                 hacim_degisimi=ky.hacim_degisimi,
                 rijit_kayma=float(np.linalg.norm(ky.rijit_kayma)),
                 profil=np.round(ky.profil, 6).tolist(),
                 n_bos_isin=ky.tani["n_bos_isin_son"])
    except (KeyError, ValueError) as e:
        k["hata"] = str(e)
    if eski:
        import ayirt_raporu as ar

        k["derinlik_eski"] = float(ar._krater(z))
    if "akma_tani" in z.files:
        k["akma_tani"] = json.loads(str(z["akma_tani"]))
    return k


def kol_olc(desenler, ad: str = "") -> list[dict]:
    import vekil_posterior as vp

    kayit = []
    for des in desenler:
        for dz in sorted(glob.glob(str(des))):
            tohum = vp._tohum_ayikla(dz)
            for yol in sorted(Path(dz).glob("nokta_*.npz")):
                k = nokta_olc(yol)
                k["tohum"] = tohum
                kayit.append(k)
                # ILERLEME HER NOKTADA (ilk surum yalniz kol sonunda yaziyordu;
                # giris dugumunde surec olunce hicbir sey kalmadi).
                print(f"  [{ad}] {len(kayit):3d} {yol.name[:26]}  "
                      f"eski {k.get('derinlik_eski', float('nan')):.4f}  "
                      f"YENI {k.get('derinlik', float('nan')):.4f}"
                      + (f"  HATA {k['hata']}" if "hata" in k else ""),
                      flush=True)
    return kayit


def kol_ozeti(ad: str, kayit: list[dict]) -> dict:
    """Tohumlar arası ortak θ'larda ortalama → sinyal + sigmoid."""
    import ayirt_raporu as ar
    import gecis_raporu as gr

    gruplar: dict = {}
    for k in kayit:
        if "hata" in k or not np.isfinite(k.get("derinlik", np.nan)):
            continue
        gruplar.setdefault(k["tohum"], {})[tuple(np.round(k["theta"], 12))] = k
    if not gruplar:
        return {"ad": ad, "n": 0, "hata": "gecerli nokta yok"}
    kollar = [gruplar[t] for t in sorted(gruplar)]
    ortak = sorted(set(kollar[0]).intersection(*[set(g) for g in kollar[1:]]))
    th = np.array(ortak)
    yeni = np.array([[g[t]["derinlik"] for t in ortak] for g in kollar])
    eski = np.array([[g[t].get("derinlik_eski", np.nan) for t in ortak]
                     for g in kollar])
    x = np.log10(th[:, 1])
    o = {"ad": ad, "n_nokta": int(sum(len(g) for g in kollar)),
         "n_theta_ortak": len(ortak), "n_tohum": len(kollar),
         "yeni_ortalama": float(yeni.mean()), "eski_ortalama": float(np.nanmean(eski))}
    for nicelik, D in (("yeni", yeni), ("eski", eski)):
        d = D.mean(axis=0)
        if not np.all(np.isfinite(d)):
            continue
        s = {}
        for eksen, deger in (("blok_alpha0", th[:, 0]), ("matris_Y0", x),
                             ("blok_kesri", th[:, 2])):
            s[eksen] = {"rho": ar.spearman(deger, d),
                        "p": ar.permutasyon_p(deger, d, n=5000)}
        o[f"sinyal_{nicelik}"] = s
        if len(kollar) > 1:
            gurultu = float(np.mean(D.var(axis=0, ddof=1)))
            o[f"F_{nicelik}"] = float(d.var(ddof=1) / gurultu) if gurultu > 0 \
                else float("inf")
        try:
            o[f"sigmoid_{nicelik}"] = gr.olcek_raporu(ad, x, d)
        except Exception as e:  # uydurma patlarsa rapor yine yazilsin
            o[f"sigmoid_{nicelik}"] = {"hata": str(e)}
    return o


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kol", nargs=2, action="append", metavar=("AD", "DESEN"),
                    required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    cikti = {}
    for ad, desen in a.kol:
        kayit = kol_olc([desen], ad)
        oz = kol_ozeti(ad, kayit)
        cikti[ad] = {"ozet": oz, "noktalar": kayit}
        if a.json:            # ARA KAYIT: her kol bitince
            a.json.write_text(json.dumps(cikti, indent=1, default=float),
                              encoding="utf-8")
        n_hata = sum("hata" in k for k in kayit)
        print("=" * 78)
        print(f"{ad}: {len(kayit)} durum, {n_hata} olculemedi")
        if "sinyal_yeni" not in oz:
            print(f"  {oz.get('hata', 'ozet yok')}")
            continue
        print(f"  ortalama derinlik  eski {oz['eski_ortalama']:.4f}  "
              f"YENI {oz['yeni_ortalama']:.4f} m", flush=True)
        for nic in ("eski", "yeni"):
            s = oz.get(f"sinyal_{nic}")
            if not s:
                continue
            f = oz.get(f"F_{nic}", float("nan"))
            sg = oz.get(f"sigmoid_{nic}", {})
            print(f"  [{nic:>4}] F = {f:9.3g}   " + "  ".join(
                f"{e}: rho={v['rho']:+.3f} p={v['p']:.4f}" for e, v in s.items()))
            if "x0" in sg:
                print(f"         sigmoid x0 = {sg['x0']:.3f} +- {sg['sigma_x0']:.3f}"
                      f"  w = {sg['w']:.3f}  R2 = {sg['R2']:.3f}"
                      f"  gecerli = {sg['gecerli']}")
    if a.json:
        a.json.write_text(json.dumps(cikti, indent=1, default=float),
                          encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
