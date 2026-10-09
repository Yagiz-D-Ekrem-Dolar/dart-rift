"""Export plain-text data tables for the PGFPlots figures of the preprint.

Design choice: the figures are *drawn by LaTeX* (PGFPlots/TikZ), not by
Python. Python only produces the numbers. Two reasons:

1. Every label, axis and symbol is then typeset by the same engine as the
   body text, so fonts, maths and point sizes match exactly.
2. The numbers land in the repository as readable tables. A reader can
   check a figure against the data without running anything.

Usage:
    python scripts/onkayit_veri.py [--out docs/preprint/veri]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from dartrift.anlik_plan import VIDEO_PLANI, kare_zamanlari
from dartrift.inference.design import DART_UZAYI_S4, lhs_design
from dartrift.inference.ic_ice_tasarim import ayrim_raporu, maximin_alt_kume
from dartrift.inference.tarih_esleme import MODEL_EKSIKLIGI_KAYNAKLI
from dartrift.setup.rubble_generator import URETIM_BLOK, place_boulders_v2
from dartrift.setup.scene import impact_geometry
from dartrift.setup.shape_mesh import ellipsoid

# PROTOKOL-HAVUZ S3 / is_HAVUZ.slurm (kilitli uretim degerleri)
N_KABA, N_INCE, TOHUM = 96, 12, 20260906
YARI_EKSEN = (88.5, 87.0, 58.0)
F_TEMSIL = 0.25
CARPMA_ACI = 17.0          # is_HAVUZ.slurm --carpma-acisi

#: PROTOKOL-HAVUZ S5 -- `beta` icin secilen sigma_model terimleri.
BETA_TERIMLERI = ("gerceklem_beta_DART", "cozunurluk_uzak",
                  "cozunurluk_yakin", "plato_olculen_DART",
                  "hedef_sekli_olculen", "carpma_yeri_olculen")
#: Olculmus ama paydaya GIRMEYEN (ust sinir / kosullu dal).
PAYDA_DISI = ("mermi_geometrisi_olculen", "matris_cekme_olculen")


def _yaz(yol: Path, basliklar, sutunlar, *, aciklama: str) -> None:
    """Bosluk ayrilmis, basligi olan dat dosyasi (PGFPlots `table`)."""
    sut = [np.asarray(c).ravel() for c in sutunlar]
    n = {c.size for c in sut}
    if len(n) != 1:
        raise ValueError(f"sutun uzunluklari uyusmuyor: {n}")
    with yol.open("w", encoding="ascii", newline="\n") as f:
        f.write(f"# {aciklama}\n")
        f.write(" ".join(basliklar) + "\n")
        for i in range(sut[0].size):
            f.write(" ".join(
                ("nan" if isinstance(v := c[i], float) and not np.isfinite(v)
                 else f"{v:.10g}" if isinstance(v, (float, np.floating))
                 else str(v))
                for c in sut) + "\n")


def tasarim(out: Path) -> dict:
    X = lhs_design(DART_UZAYI_S4, N_KABA, root_seed=TOHUM)
    u = DART_UZAYI_S4.to_unit(X)
    idx = maximin_alt_kume(u, N_INCE)
    ince = np.zeros(N_KABA, dtype=int)
    ince[idx] = 1
    _yaz(out / "tasarim.dat", ("alphab", "Y0", "f", "ince"),
         (X[:, 0], X[:, 1], X[:, 2], ince),
         aciklama=("locked design: lhs_design(DART_UZAYI_S4, 96, "
                   f"root_seed={TOHUM}); ince=1 marks the {N_INCE} nested "
                   "fine points chosen by maximin (ADR-0059 S3.2)"))
    r = ayrim_raporu(u, idx)
    return {"indeks": idx.tolist(), **r}


def butce(out: Path) -> dict:
    adlar = list(BETA_TERIMLERI) + list(PAYDA_DISI)
    deg, bayrak = [], []
    for ad in adlar:
        s, _ = MODEL_EKSIKLIGI_KAYNAKLI[ad]
        deg.append(s)
        bayrak.append(0 if ad in BETA_TERIMLERI else 1)
    _yaz(out / "butce.dat", ("sira", "deger", "disarida"),
         (np.arange(len(adlar)), np.asarray(deg, dtype=float),
          np.asarray(bayrak)),
         aciklama=("measured model-discrepancy terms; disarida=1 means "
                   "measured but deliberately excluded from the denominator"))
    (out / "butce_adlar.tex").write_text(
        "\n".join(a.replace("_", r"\_") for a in adlar) + "\n",
        encoding="ascii")
    return dict(zip(adlar, deg, strict=True))


def kare_plani(out: Path) -> dict:
    t = kare_zamanlari(VIDEO_PLANI)
    esit = np.linspace(0.0, 600.0, t.size)
    taban = 1e-4                       # log eksende t=0 icin taban
    _yaz(out / "kare_plani.dat", ("tlog", "tesit"),
         (np.maximum(t, taban), np.maximum(esit, taban)),
         aciklama=("snapshot schedule: segmented-logarithmic versus uniform, "
                   "same number of frames; t=0 clamped to 1e-4 for log axis"))
    return {"n": int(t.size),
            "erken_log": int(np.count_nonzero(t <= 1.0)),
            "erken_esit": int(np.count_nonzero(esit <= 1.0))}


def sahne(out: Path) -> dict:
    a, b, c = YARI_EKSEN
    m = ellipsoid(a, b, c, subdiv=3)
    bf, bilgi = place_boulders_v2(
        m, F_TEMSIL, URETIM_BLOK["q"], URETIM_BLOK["r_min"],
        URETIM_BLOK["r_max"], root_seed=TOHUM)
    cen, yar = np.asarray(bf.centers), np.asarray(bf.radii)

    _yaz(out / "bloklar.dat", ("x", "y", "z", "r"),
         (cen[:, 0], cen[:, 1], cen[:, 2], yar),
         aciklama=(f"interior blocks, f_target={F_TEMSIL}, "
                   f"f_realised={bilgi['f_gercek']:.4f}, "
                   f"r in [{URETIM_BLOK['r_min']}, {URETIM_BLOK['r_max']}] m, "
                   f"q={URETIM_BLOK['q']}, root_seed={TOHUM}"))

    # Kesit duzlemi y = 0, yani x-z duzlemi. Bu secim keyfi DEGIL: carpma
    # noktasi (88.5, 0, 0) ve geliş yonu (-0.956, 0, 0.292) ikisi de bu
    # duzlemde; z = 0 kesiti 17 derecelik egikligi GOSTEREMEZDI.
    kesen = np.abs(cen[:, 1]) < yar
    rk = np.sqrt(np.maximum(yar[kesen] ** 2 - cen[kesen, 1] ** 2, 0.0))
    _yaz(out / "bloklar_kesit.dat", ("x", "z", "r"),
         (cen[kesen, 0], cen[kesen, 2], rk),
         aciklama="blocks intersected by the y=0 plane (x-z), as circles")

    g = impact_geometry(m, np.array([1.0, 0.0, 0.0]),
                        angle_deg=CARPMA_ACI, azimuth_deg=0.0)
    (out / "carpma.tex").write_text(
        # TikZ koordinati bilimsel gosterimi okumaz; `3.7e-17` gibi
        # yuvarlama artiklari sifira kirpilir.
        "".join((f"\\def\\{k}{{{v:d}}}\n" if isinstance(v, int)
                 else f"\\def\\{k}{{{0.0 if abs(v) < 1e-9 else v:.6f}}}\n")
                for k, v in (
            ("carpmaX", g.point[0]), ("carpmaZ", g.point[2]),
            ("yonX", g.direction[0]), ("yonZ", g.direction[2]),
            ("aciDeg", round(g.angle_deg)),
            ("cosGeliş", g.diagnostics["cos_incidence"]),
            ("ekseneA", YARI_EKSEN[0]), ("ekseneB", YARI_EKSEN[1]),
            ("ekseneC", YARI_EKSEN[2]))).replace("ş", "s"),
        encoding="ascii")
    return {"n_blok": int(cen.shape[0]), "n_kesit": int(kesen.sum()),
            "r_min": float(yar.min()), "r_max": float(yar.max()),
            "f_gercek": float(bilgi["f_gercek"]),
            "f_se": float(bilgi["f_se"]), "hacim": float(m.volume),
            "yari_eksen": YARI_EKSEN,
            "carpma_noktasi": np.round(g.point, 4).tolist(),
            "yon": np.round(g.direction, 5).tolist()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/preprint/veri")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for ad, fn in (("tasarim", tasarim), ("butce", butce),
                   ("kare_plani", kare_plani), ("sahne", sahne)):
        print(f"{ad}: {fn(out)}")
    print(f"-> {out.resolve()}")


if __name__ == "__main__":
    main()
