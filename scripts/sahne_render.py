"""Üretim sahnesinin **parçacık** görüntüsü — depodaki veriden.

Deponun ön sayfası sayı ve şekil doluydu ama *modellenen şeyin kendisi*
hiçbir yerde görünmüyordu. Bu betik onu çizer: `96` noktalık üretim
kampanyasının her koşusunun başladığı cisim.

## Ne çizilir

| kaynak | ne |
|---|---|
| `docs/preprint/veri/tumgovde.dat` | `7 641` parçacık, `x y z` + matris/blok etiketi |
| `docs/preprint/veri/blok_kureleri.dat` | `5` blok küresi, merkez ve yarıçap |

İkisi de üretim sahnesinin kendi kurucusundan üretilmiştir
(`blok_uretici=v1`, `spacing 7,0 m`, `root_seed 20260906` —
`truba/is_HAVUZ.slurm` ile aynı). Burada **hiçbir şey uydurulmaz**:
çizilen her nokta sahnedeki bir parçacıktır.

## Niçin matplotlib'in 3B'si değil

`Axes3D.scatter` derinliği yalnız kabaca sıralar, saydamlığı doğru
harmanlamaz ve 7 600 noktada hamur gibi görünür. Burada izdüşüm elle
yapılır: döndür, ortografik izdüşür, **derinliğe göre sırala** ve uzak
parçacığı küçült + karart. Ressam algoritması; pahalı değil, ve
sonucu kontrol edilebilir.

Aydınlatma de sahtelenmez: parlaklık, parçacığın cisim merkezinden
dışa bakan yönü ile ışık yönü arasındaki açıdan gelir. Bu bir gölge
hesabı değil, bir **derinlik ipucu**dur ve öyle adlandırılmıştır.

Kullanım:

    python scripts/sahne_render.py --cikti docs/figures/sahne.png
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

KOK = os.path.join(os.path.dirname(__file__), "..")
GOVDE = os.path.join(KOK, "docs", "preprint", "veri", "tumgovde.dat")
BLOKLAR = os.path.join(KOK, "docs", "preprint", "veri", "blok_kureleri.dat")

#: arXiv koyu paleti -- docs/figures/common.tex ile AYNI.
CANVAS = "#282623"
INK = "#F9F7F7"
MUTED = "#ADA4A4"
MATRIS = (0.42, 0.52, 0.60)      # soguk gri-mavi
BLOK = (0.78, 0.60, 0.36)        # sicak kum
VURGU = "#2198D4"

#: Uretim sahnesi (truba/is_HAVUZ.slurm): elipsoit yari eksenleri [m].
YARI_EKSEN = (88.5, 87.0, 58.0)
#: Carpma noktasi `aim = (0,0,1)` ile +z kutbudur; gelis acisi 17 derece.
CARPMA_ACISI = 17.0


def _oku(yol: str) -> np.ndarray:
    """Sayisal satirlari oku.

    Dosyalarda `#` yorumlarinin ARDINDAN bir de sutun basligi var
    (`x y z blok`) ve o yorum isaretli degil; `np.loadtxt` ona takiliyor.
    Bu yuzden satirlar elle suzuluyor: ilk alani sayiya cevrilen her
    satir veridir, otekiler baslik.
    """
    satir = []
    with open(yol, encoding="utf-8") as f:
        for ham in f:
            s = ham.strip()
            if not s or s.startswith("#"):
                continue
            try:
                satir.append([float(t) for t in s.split()])
            except ValueError:
                continue          # sutun basligi
    if not satir:
        raise SystemExit(f"BOSLUK: {yol} icinde sayisal satir yok")
    return np.asarray(satir, dtype=np.float64)


def _dondur(x: np.ndarray, egim: float, donus: float) -> np.ndarray:
    """Once z ekseni etrafinda, sonra x ekseni etrafinda dondur."""
    a, b = np.radians(donus), np.radians(egim)
    Rz = np.array([[np.cos(a), -np.sin(a), 0.0],
                   [np.sin(a), np.cos(a), 0.0],
                   [0.0, 0.0, 1.0]])
    Rx = np.array([[1.0, 0.0, 0.0],
                   [0.0, np.cos(b), -np.sin(b)],
                   [0.0, np.sin(b), np.cos(b)]])
    return x @ Rz.T @ Rx.T


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cikti", required=True)
    p.add_argument("--egim", type=float, default=22.0)
    p.add_argument("--donus", type=float, default=35.0)
    p.add_argument("--dpi", type=int, default=200)
    a = p.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ham = _oku(GOVDE)
    x, blok = ham[:, :3], ham[:, 3].astype(int)
    kure = np.atleast_2d(_oku(BLOKLAR))
    if x.shape[1] != 3 or len(x) < 1000:
        raise SystemExit(f"beklenmeyen govde verisi: {ham.shape}")

    xr = _dondur(x, a.egim, a.donus)
    # Isik: izleyicinin sol ustunden. Parlaklik = disa bakan yon . isik.
    n = x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-9)
    nr = _dondur(n, a.egim, a.donus)
    isik = np.array([-0.45, 0.35, 0.82])
    isik = isik / np.linalg.norm(isik)
    lam = np.clip(nr @ isik, 0.0, 1.0) ** 0.8

    # Derinlik: +y izleyiciye dogru (dondurmeden sonra).
    d = xr[:, 1]
    # NumPy 2'de `ndarray.ptp` kaldirildi; `np.ptp` her iki surumde de var
    # ve ADR-0005 iki surumu birden destekliyor.
    dn = (d - d.min()) / max(float(np.ptp(d)), 1e-9)

    # Cismin TAMAMINI esit cizmek onu saydam gosteriyor: 7 600 noktanin
    # yarisi arka yarikurede ve on yuzeyin uzerine biniyor. Iki olcut
    # ayristirilir:
    #   `kabuk` -- normallestirilmis yaricap; yuzeye yakin mi?
    #   `on`    -- disa bakan yon izleyiciye mi donuk?
    # Ikisinin carpimi "gorunur yuzey"dir ve parlak cizilir; gerisi
    # karartilir ama SILINMEZ -- ic yapi (bloklar) gorunsun diye.
    a_, b_, c_ = YARI_EKSEN
    s_ = np.sqrt((x[:, 0] / a_) ** 2 + (x[:, 1] / b_) ** 2
                 + (x[:, 2] / c_) ** 2)

    # KABUK CIZILIR, IC CIZILMEZ. Butun hacmi cizmek cismi saydam
    # gosteriyordu: duzenli FCC kafesinin arka katmanlari on katmanla
    # ust uste binip moire deseni uretiyor ve govde "tram" gibi
    # okunuyordu. Yalniz dis kabuk cizilince yuzey YUZEY gibi duruyor.
    #
    # Ic yapi yine de kaybolmasin diye derindeki BLOK parcaciklari cok
    # soluk birakilir -- cismin icinde bir sey oldugu gorunsun ama one
    # cikmasin.
    n_tam, n_blok_tam = len(x), int((blok == 1).sum())
    kabuk = s_ > 0.78
    derin_blok = (~kabuk) & (blok == 1)
    tut = kabuk | derin_blok

    x, xr, blok, lam, nr = x[tut], xr[tut], blok[tut], lam[tut], nr[tut]
    d, s_ = xr[:, 1], s_[tut]
    dn = (d - d.min()) / max(float(np.ptp(d)), 1e-9)
    kabuk = kabuk[tut]

    on = np.clip(nr[:, 1], 0.0, 1.0)
    # Gorunur yuzey agirligi: kabukta VE izleyiciye donuk.
    one = np.where(kabuk, 0.25 + 0.75 * on, 0.0)

    sira = np.argsort(d)
    xr, blok, lam = xr[sira], blok[sira], lam[sira]
    dn, one, kabuk = dn[sira], one[sira], kabuk[sira]

    taban = np.where(blok[:, None] == 1, np.array(BLOK), np.array(MATRIS))
    parlak = (0.62 + 1.05 * lam) * (0.50 + 0.50 * one) * (0.62 + 0.38 * dn)
    renk = np.clip(taban * parlak[:, None], 0.0, 1.0)
    alfa = np.where(kabuk, np.clip(0.34 + 0.62 * one, 0.0, 0.98), 0.10)
    boy = np.where(kabuk, 3.0 + 15.0 * one * dn ** 1.2, 2.0)

    gen = 2.0 * max(YARI_EKSEN) * 1.18
    fig = plt.figure(figsize=(9.6, 6.4), dpi=a.dpi)
    fig.patch.set_facecolor(CANVAS)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(CANVAS)
    ax.set_xlim(-gen * 0.82, gen * 0.66)
    ax.set_ylim(-gen * 0.49, gen * 0.49)
    ax.set_aspect("equal")
    ax.axis("off")

    # Blok kureleri CIZILMEZ: blok parcaciklari zaten onlari gosteriyor
    # ve tam yaricapli cemberler cismin disina tasip govdeyi
    # kalabaliklastiriyordu. `Circle` yine de iceri alinmis durumda --
    # ileride kesit gorunumu istenirse diye.

    ax.scatter(xr[:, 0], xr[:, 2], s=boy, c=renk, alpha=alfa,
               linewidths=0, zorder=2, rasterized=True)

    # Carpma: +z kutbu, 17 derecelik gelis.
    pk = _dondur(np.array([[0.0, 0.0, YARI_EKSEN[2]]]), a.egim, a.donus)[0]
    yon = _dondur(np.array([[np.sin(np.radians(CARPMA_ACISI)), 0.0,
                             np.cos(np.radians(CARPMA_ACISI))]]),
                  a.egim, a.donus)[0]
    uzunluk = 0.52 * max(YARI_EKSEN)
    ax.annotate("", xy=(pk[0], pk[2]),
                xytext=(pk[0] + yon[0] * uzunluk, pk[2] + yon[2] * uzunluk),
                arrowprops=dict(arrowstyle="-|>", color=VURGU, lw=1.3,
                                shrinkA=0, shrinkB=2), zorder=4)
    ax.scatter([pk[0]], [pk[2]], s=26, facecolor="none", edgecolor=VURGU,
               lw=1.1, zorder=5)

    ax.text(pk[0] + yon[0] * uzunluk * 1.02, pk[2] + yon[2] * uzunluk * 1.02,
            "DART  6.1 km s$^{-1}$", color=VURGU, fontsize=9,
            ha="left", va="bottom", zorder=6)

    # Olcek cubugu: 50 m.
    x0, y0 = -gen * 0.68, -gen * 0.42
    ax.plot([x0, x0 + 50.0], [y0, y0], color=MUTED, lw=1.2, zorder=6)
    ax.text(x0 + 25.0, y0 + 3.0, "50 m", color=MUTED, fontsize=8.5,
            ha="center", va="bottom")

    ax.text(-gen * 0.68, gen * 0.415,
            "Dimorphos — production scene", color=INK, fontsize=12.5,
            ha="left", va="top")
    ax.text(-gen * 0.68, gen * 0.415 - 11.0,
            f"{n_tam:,} SPH particles  ·  {n_blok_tam:,} in boulders  ·  "
            f"{len(kure)} boulders\n"
            f"outer shell drawn, {len(xr):,} of them\n"
            f"triaxial {YARI_EKSEN[0]}×{YARI_EKSEN[1]}×{YARI_EKSEN[2]} m  ·  "
            f"impact {CARPMA_ACISI:g}° from the surface normal",
            color=MUTED, fontsize=8.6, ha="left", va="top", linespacing=1.5)

    fig.savefig(a.cikti, facecolor=CANVAS, dpi=a.dpi)
    print(f"parcacik : {len(x)}  (blok {int((blok == 1).sum())})")
    print(f"blok kuresi: {len(kure)}")
    print(f"yazildi  : {a.cikti}")


if __name__ == "__main__":
    main()
