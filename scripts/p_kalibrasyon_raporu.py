"""Protokol P — kapalı döngü posterior kalibrasyonu (kilitli, koşudan ÖNCE).

Bitiş 3'ün son halkası: vekil + posterior **bilinen bir θ'yı geri
buluyor mu**, ve bulurken verdiği aralıklar **dürüst mü**?

N taramasının (24 θ × 2 tohum) her `θ_i`'si sırayla dışarıda bırakılır:

1. Kalan 23 θ'nın 46 koşusuyla gözlenebilir başına ikinci derece vekil
   (`inference.surrogate`) kurulur.
2. Toplam kovaryans = eğitim kümesinin **bırak-birini artıklarının**
   gözlenebilirler arası kovaryansı, köşegene `KUCULTME` kadar
   küçültülmüş. Bu artık gerçekleme gürültüsü + vekil hatasıdır —
   gerçek Dimorphos da TEK bir gerçeklemedir.
3. Dışarıdaki θ'nın her tohumu "gözlem" sayılır; posterior tam
   kovaryanslı ızgarayla (`grid_posterior_kovaryans`) hesaplanır.

48 vakada eksen başına ölçülür: gerçek `u`'nun `%68` aralığında olma
sıklığı (kapsama) ve aralık genişliğinin medyanı.

## Eksen yargısı (eşikler aşağıdaki sabitlerde)

| koşul | yargı |
|---|---|
| kapsama68 `< 0,50` | **AŞIRI GÜVENLİ** — aralıklar yalan söylüyor |
| kapsama68 `0,50–0,87`, medyan genişlik `< 0,34` | **ÇÖZÜLÜYOR** |
| kapsama68 `> 0,87`, medyan genişlik `< 0,34` | **ÇÖZÜLÜYOR (TEMKİNLİ)** |
| medyan genişlik `≥ 0,34` | **BİLGİ YOK** |

`0,50–0,87`: 24 bağımsız θ'da `%68` kapsamanın binom `%95` bandı.
`0,34 = C2_DARALMA × 0,68` (G4-C2 ile aynı ölçüt: önselin `%68`
aralığının yarısı).

## Genel yargı

Herhangi bir eksen AŞIRI GÜVENLİ → **KALİBRASYON DÜŞTÜ**. Aksi halde
çözülen eksen sayısı: ÜÇ / İKİ / TEK / HİÇBİRİ. Gürültü tepkisi (C3 ruhu):
kovaryans `1×, 2×, 4×` iken en dar eksenin medyan genişliği büyümüyorsa
yargıya **GÜRÜLTÜ TEPKİSİZ** eklenir ve sonuç geçersiz sayılır.

Kullanim:
    python scripts/p_kalibrasyon_raporu.py --kok kampanya \\
        --s-n kampanya/S_N.json --json kampanya/S_P.json
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

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402
from dartrift.inference.posterior import grid_posterior_kovaryans  # noqa: E402
from dartrift.inference.recovery import C2_DARALMA  # noqa: E402
from dartrift.inference.surrogate import (  # noqa: E402
    design_matrix,
    fit_surrogate,
    loo_artiklari,
)

#: Gözlenebilir → (dönüşüm, taban). Kütle/hacim/β−1 pozitif ve on yıllar
#: boyunca değişiyor; ikinci derece vekil log uzayında daha az eğri görür.
DONUSUMLER = {
    "d_merkez": ("kimlik", None),
    "R_krater": ("kimlik", None),
    "V_krater": ("log10", 1e-6),
    "dV_sikisma": ("kimlik", None),
    "beta_eksi_1": ("log10", 1e-4),
    "M_ejekta": ("log10", 1e-3),
    "mu_ejekta": ("kimlik", None),
}
#: Gözlenebilir yalnız koşuların en az bu kesrinde sonluysa kullanılır.
SONLU_EN_AZ = 0.90
#: Tam veride vekil `q2` eşiği — `Surrogate.guvenilir` ile aynı.
Q2_ESIGI = 0.5
#: Kovaryansın köşegene küçültülmesi: `(1−λ)Σ + λ diag(Σ)`.
KUCULTME = 0.3
N_IZGARA = 40
KAPSAMA_ALT = 0.50
KAPSAMA_UST = 0.87
GENISLIK_ESIGI = C2_DARALMA * 0.68
GURULTU_CARPANLARI = (1.0, 2.0, 4.0)
#: Gürültü tepkisi: her adımda izin verilen daralma, toplamda gereken büyüme.
TEPKI_TOLERANSI = 0.02
EKSENLER = ("blok_alpha0", "log10_Y0", "blok_kesri")
GENEL_ADLAR = {3: "UC EKSEN COZULUYOR", 2: "IKI EKSEN COZULUYOR",
               1: "TEK EKSEN COZULUYOR", 0: "HICBIR EKSEN COZULMUYOR"}


def donustur(gozlem: str, deger: float) -> float:
    kip, taban = DONUSUMLER[gozlem]
    if not np.isfinite(deger):
        return float("nan")
    if kip == "log10":
        return float(np.log10(max(float(deger), taban)))
    return float(deger)


def kayitlari_oku(kok: Path, desen: str = "N_matris_sahne*.durumlar") -> list[dict]:
    """Her durum dosyası → `{"theta", "tohum", gözlenebilirler}` (dönüşümlü)."""
    import vekil_posterior as vp
    from gozlem_vektoru import gozlem_vektoru

    kayit = []
    for dz in sorted(glob.glob(str(kok / desen))):
        t = vp._tohum_ayikla(dz)
        for f in sorted(glob.glob(dz + "/nokta_*.npz")):
            z = np.load(f)
            gv = gozlem_vektoru(z)
            gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
            k = {g: donustur(g, gv.get(g, float("nan"))) for g in DONUSUMLER}
            k["theta"] = np.asarray(z["theta"], float).ravel()
            k["tohum"] = t
            kayit.append(k)
    return kayit


def gozlem_sec(kayitlar: list[dict], s_n: dict | None) -> tuple[list[str], dict]:
    """Kilitli seçim: sonlu kesir, N yargısı (varsa), tam veride `q2`."""
    tani = {}
    secilen = []
    X = np.array([k["theta"] for k in kayitlar], float)
    for g in DONUSUMLER:
        y = np.array([k[g] for k in kayitlar], float)
        sonlu = np.isfinite(y)
        t = {"sonlu_kesir": float(sonlu.mean()) if len(y) else 0.0}
        if s_n is not None:
            t["N_karar"] = s_n.get("gozlem", {}).get(g, {}).get("karar", "YOK")
        if t["sonlu_kesir"] < SONLU_EN_AZ:
            t["neden"] = "SONLU DEGIL"
        elif s_n is not None and t["N_karar"] != "AYIRT EDIYOR":
            t["neden"] = "N AYIRT ETMIYOR"
        else:
            try:
                v = fit_surrogate(DART_UZAYI_S3, X[sonlu], y[sonlu])
                t["q2"] = v.q2
                t["neden"] = "SECILDI" if (np.isfinite(v.q2) and v.q2 > Q2_ESIGI) \
                    else "VEKIL YETERSIZ"
            except ValueError as e:
                t["neden"] = f"VEKIL KURULAMADI: {e}"
        if t["neden"] == "SECILDI":
            secilen.append(g)
        tani[g] = t
    return secilen, tani


def kuculmus_kov(E: np.ndarray, lam: float = KUCULTME) -> np.ndarray:
    """`(n, k)` artıklardan küçültülmüş kovaryans."""
    E = np.atleast_2d(np.asarray(E, float))
    S = np.cov(E, rowvar=False, ddof=1).reshape(E.shape[1], E.shape[1])
    return (1.0 - lam) * S + lam * np.diag(np.diag(S))


def _gruplar(X: np.ndarray) -> np.ndarray:
    anah = {}
    g = np.empty(len(X), int)
    for i, x in enumerate(X):
        g[i] = anah.setdefault(tuple(np.round(x, 12)), len(anah))
    return g


def _aralik(post, j: int, a: float, b: float) -> tuple[float, float]:
    m = post.marginal(j)
    kum = np.cumsum(m)
    eksen = post.grid_u[j]
    return float(np.interp(a, kum, eksen)), float(np.interp(b, kum, eksen))


def _izgara_tasarimi(n_grid: int) -> np.ndarray:
    eksen = np.linspace(0.0, 1.0, n_grid)
    izg = np.meshgrid(*([eksen] * DART_UZAYI_S3.ndim), indexing="ij")
    return design_matrix(np.column_stack([a.ravel() for a in izg]))


def _egit(X, Y):
    """Vekil katsayıları + bırak-bir-θ artıklarından küçültülmüş kovaryans."""
    space = DART_UZAYI_S3
    grup = _gruplar(X)
    C = np.empty((design_matrix(np.zeros((1, space.ndim))).shape[1], Y.shape[1]))
    E = np.empty_like(Y)
    for i in range(Y.shape[1]):
        C[:, i] = fit_surrogate(space, X, Y[:, i]).coef
        E[:, i] = loo_artiklari(space, X, Y[:, i], gruplar=grup)
    return C, kuculmus_kov(E)


def _vaka(tahmin, S, y, u, grup, n_grid, carpanlar) -> dict:
    space = DART_UZAYI_S3
    vaka = {"grup": int(grup), "gercek_u": np.asarray(u).tolist(), "carpan": {}}
    for c in carpanlar:
        post = grid_posterior_kovaryans(space, tahmin, y, c * S, n_grid)
        vaka["carpan"][float(c)] = {
            "hdi68": post.hdi_u.tolist(),
            "hdi95": [_aralik(post, j, 0.025, 0.975) for j in range(space.ndim)],
            "genislik": post.width_u.tolist(),
            "cakili": [post.pinned(j) for j in range(space.ndim)],
            "ortalama_u": post.mean_u.tolist(),
        }
    return vaka


def kapali_dongu(X, Y, *, n_grid: int = N_IZGARA,
                 carpanlar=GURULTU_CARPANLARI) -> list[dict]:
    """θ-grubu başına bırak-bir-θ kapalı döngü vakaları."""
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    grup = _gruplar(X)
    A_izg = _izgara_tasarimi(n_grid)
    U = DART_UZAYI_S3.to_unit(X)
    vakalar = []
    for g in np.unique(grup):
        egit = grup != g
        C, S = _egit(X[egit], Y[egit])
        tahmin = A_izg @ C
        for r in np.flatnonzero(~egit):
            vakalar.append(_vaka(tahmin, S, Y[r], U[r], g, n_grid, carpanlar))
    return vakalar


def dis_ornek(Xe, Ye, Xt, Yt, *, n_grid: int = N_IZGARA,
              carpanlar=GURULTU_CARPANLARI) -> list[dict]:
    """Bütün eğitim kümesiyle vekil; HİÇ görülmemiş ikinci tasarımda sına.

    Kapalı döngüden farkı: gözlenebilir seçimi ve vekil aynı veriden
    geliyordu (hafif iyimserlik). Burada sınama kümesi seçimde de yok.
    """
    Xe, Ye = np.asarray(Xe, float), np.asarray(Ye, float)
    Xt, Yt = np.asarray(Xt, float), np.asarray(Yt, float)
    C, S = _egit(Xe, Ye)
    tahmin = _izgara_tasarimi(n_grid) @ C
    U = DART_UZAYI_S3.to_unit(Xt)
    grup = _gruplar(Xt)
    return [_vaka(tahmin, S, Yt[r], U[r], grup[r], n_grid, carpanlar)
            for r in range(len(Xt))]


def eksen_yargisi(vakalar: list[dict], j: int, carpan: float = 1.0) -> dict:
    u = np.array([v["gercek_u"][j] for v in vakalar])
    h68 = np.array([v["carpan"][carpan]["hdi68"][j] for v in vakalar])
    h95 = np.array([v["carpan"][carpan]["hdi95"][j] for v in vakalar])
    gen = np.array([v["carpan"][carpan]["genislik"][j] for v in vakalar])
    kap68 = float(np.mean((h68[:, 0] <= u) & (u <= h68[:, 1])))
    kap95 = float(np.mean((h95[:, 0] <= u) & (u <= h95[:, 1])))
    med = float(np.median(gen))
    if kap68 < KAPSAMA_ALT:
        karar = "ASIRI GUVENLI"
    elif med >= GENISLIK_ESIGI:
        karar = "BILGI YOK"
    elif kap68 > KAPSAMA_UST:
        karar = "COZULUYOR (TEMKINLI)"
    else:
        karar = "COZULUYOR"
    return {"kapsama68": kap68, "kapsama95": kap95, "medyan_genislik": med,
            "cakili": int(sum(v["carpan"][carpan]["cakili"][j] for v in vakalar)),
            "n": len(vakalar), "karar": karar}


def gurultu_tepkisi(vakalar: list[dict]) -> dict:
    carp = sorted(vakalar[0]["carpan"])
    med = np.array([[np.median([v["carpan"][c]["genislik"][j] for v in vakalar])
                     for j in range(len(EKSENLER))] for c in carp])
    j = int(np.argmin(med[0]))
    seri = med[:, j]
    tol = TEPKI_TOLERANSI * max(float(seri[0]), 1e-300)
    tepkili = bool(np.all(np.diff(seri) >= -tol)
                   and seri[-1] > seri[0] * (1.0 + TEPKI_TOLERANSI))
    return {"eksen": EKSENLER[j], "carpanlar": carp,
            "medyan_genislik": seri.tolist(), "tepkili": tepkili}


def genel_yargi(eksenler: dict, tepki: dict) -> str:
    if any(e["karar"] == "ASIRI GUVENLI" for e in eksenler.values()):
        return "KALIBRASYON DUSTU"
    n = sum(e["karar"].startswith("COZULUYOR") for e in eksenler.values())
    ad = GENEL_ADLAR[n]
    if n and not tepki["tepkili"]:
        ad += " -- GURULTU TEPKISIZ, GECERSIZ"
    return ad


def _matrisler(kayitlar, secilen):
    X = np.array([k["theta"] for k in kayitlar], float).reshape(-1, DART_UZAYI_S3.ndim)
    Y = np.array([[k[g] for g in secilen] for k in kayitlar], float).reshape(-1, len(secilen))
    iyi = np.all(np.isfinite(Y), axis=1)
    return X[iyi], Y[iyi]


def _yargila(vakalar) -> dict:
    eksenler = {ad: eksen_yargisi(vakalar, j) for j, ad in enumerate(EKSENLER)}
    tepki = gurultu_tepkisi(vakalar)
    return {"eksen": eksenler, "gurultu_tepkisi": tepki,
            "genel": genel_yargi(eksenler, tepki)}


def rapor(kayitlar: list[dict], s_n: dict | None, *, n_grid: int = N_IZGARA,
          test_kayitlar: list[dict] | None = None) -> dict:
    secilen, tani = gozlem_sec(kayitlar, s_n)
    out = {"secim": tani, "secilen": secilen}
    if not secilen:
        out["genel"] = "GOZLENEBILIR YOK"
        return out
    X, Y = _matrisler(kayitlar, secilen)
    out.update(n_kosu=int(len(X)), n_theta=int(len(np.unique(_gruplar(X)))))
    out.update(_yargila(kapali_dongu(X, Y, n_grid=n_grid)))
    if test_kayitlar:
        Xt, Yt = _matrisler(test_kayitlar, secilen)
        if len(Xt):
            d = _yargila(dis_ornek(X, Y, Xt, Yt, n_grid=n_grid))
            d.update(n_kosu=int(len(Xt)), n_theta=int(len(np.unique(_gruplar(Xt)))))
            out["dis_ornek"] = d
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--desen", default="N_matris_sahne*.durumlar")
    ap.add_argument("--test-desen", default=None,
                    help="dış örneklem (ör. N2_matris_sahne*.durumlar)")
    ap.add_argument("--s-n", type=Path, default=None)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    s_n = json.loads(a.s_n.read_text(encoding="utf-8")) \
        if a.s_n and a.s_n.exists() else None
    kayit = kayitlari_oku(a.kok, a.desen)
    test = kayitlari_oku(a.kok, a.test_desen) if a.test_desen else None
    out = rapor(kayit, s_n, test_kayitlar=test)
    print("=" * 78)
    print(f"PROTOKOL P -- kapali dongu kalibrasyonu ({len(kayit)} kosu, "
          f"N yargisi {'VAR' if s_n else 'YOK'})")
    print("=" * 78)
    for g, t in out["secim"].items():
        print(f"  {g:>12}: {t}")
    for ad, e in out.get("eksen", {}).items():
        print(f"  {ad:>12}: kapsama68 {e['kapsama68']:.2f}  kapsama95 "
              f"{e['kapsama95']:.2f}  medyan genislik {e['medyan_genislik']:.3f}  "
              f"cakili {e['cakili']}/{e['n']}  -> {e['karar']}")
    if "gurultu_tepkisi" in out:
        print(f"  gurultu tepkisi: {out['gurultu_tepkisi']}")
    print(f"\nGENEL: {out['genel']}")
    if "dis_ornek" in out:
        d = out["dis_ornek"]
        print(f"\nDIS ORNEKLEM ({d['n_kosu']} kosu, {d['n_theta']} theta)")
        for ad, e in d["eksen"].items():
            print(f"  {ad:>12}: kapsama68 {e['kapsama68']:.2f}  medyan genislik "
                  f"{e['medyan_genislik']:.3f}  -> {e['karar']}")
        print(f"DIS ORNEKLEM GENEL: {d['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
