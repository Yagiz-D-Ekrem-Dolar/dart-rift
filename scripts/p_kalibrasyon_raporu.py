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
from dartrift.inference.gp_vekil import gp_grup_loo, gp_uydur  # noqa: E402
from dartrift.inference.posterior import (  # noqa: E402
    grid_posterior_hetero,
    grid_posterior_kovaryans,
)
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
#: P-v4b (2026-09-13, kesmeli veri gelmeden): ZAMAN ORNEKLERI. Her npz'nin
#: `fizik_tani.impuls_egrisi` satirlari `[t, P_hedef/p_imp, beta_hedef,
#: M_ejekta]`. Krater buyurken beta ve kacan kutlenin ZAMAN SEYRI dayanima
#: ve blok alanina tek anlik goruntuden fazla bilgi tasiyabilir.
DONUSUMLER_ZAMAN = {
    "beta_eksi_1_t08": ("log10", 1e-4),
    "beta_eksi_1_t16": ("log10", 1e-4),
    "M_ejekta_t08": ("log10", 1e-3),
    "M_ejekta_t16": ("log10", 1e-3),
}
ZAMAN_ORNEGI = {"beta_eksi_1_t08": (2, 0.008), "beta_eksi_1_t16": (2, 0.016),
                "M_ejekta_t08": (3, 0.008), "M_ejekta_t16": (3, 0.016)}
#: Zaman ornegi hedef ana bu bagil pay icinde degilse `nan`.
ZAMAN_PAYI = 0.10
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
#: P-v3 (A82): gürültü kovaryansının kaynağı ve kat sayısı.
ARTIK_KIPLERI = ("loo", "kfold4")
KAT_SAYISI = 4
GENEL_ADLAR = {3: "UC EKSEN COZULUYOR", 2: "IKI EKSEN COZULUYOR",
               1: "TEK EKSEN COZULUYOR", 0: "HICBIR EKSEN COZULMUYOR"}


def donustur(gozlem: str, deger: float) -> float:
    kip, taban = {**DONUSUMLER, **DONUSUMLER_ZAMAN}[gozlem]
    if not np.isfinite(deger):
        return float("nan")
    if kip == "log10":
        return float(np.log10(max(float(deger), taban)))
    return float(deger)


def kayitlari_oku(kok: Path, desen: str = "N_matris_sahne*.durumlar") -> list[dict]:
    """Her durum dosyası → `{"theta", "tohum", gözlenebilirler}` (dönüşümlü)."""
    import vekil_posterior as vp

    # Onbellek: ayni npz her raporda yeniden hesaplanmaz; anahtar kod ozeti
    # + npz boyut/mtime (scripts/gozlem_onbellek.py).
    from gozlem_onbellek import gozlem

    kayit = []
    gorulen: set = set()
    # Virgulle ayrilmis birden cok desen (P-v4 havuzu).
    dizinler = sorted({d for ds in desen.split(",") for d in glob.glob(str(kok / ds.strip()))})
    for dz in dizinler:
        t = vp._tohum_ayikla(dz)
        for f in sorted(glob.glob(dz + "/nokta_*.npz")):
            z = np.load(f)
            gv = dict(gozlem(f))
            gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
            k = {g: donustur(g, gv.get(g, float("nan"))) for g in DONUSUMLER}
            k.update(zaman_ornekleri(z))
            k["theta"] = np.asarray(z["theta"], float).ravel()
            k["tohum"] = t
            anah = (tuple(np.round(k["theta"], 12)), t)
            # A83 dolgusu: yalniz BIR tohumda patlayan theta icin dolgu kampanyasi
            # iki tohumu da kosuyor; ayni (theta, tohum) ikinci kez SAYILMAZ
            # (gurultu kestirimini sahte daraltirdi). Siralama deterministik:
            # ilk gelen (asil kampanya) tutulur.
            if anah in gorulen:
                continue
            gorulen.add(anah)
            kayit.append(k)
    return kayit


def zaman_ornekleri(z) -> dict:
    """P-v4b: impuls egrisinden 8 ve 16 ms ornekleri (donusumlu)."""
    out = {g: float("nan") for g in DONUSUMLER_ZAMAN}
    try:
        egri = np.asarray(json.loads(str(z["fizik_tani"])).get("impuls_egrisi", []), float)
    except (KeyError, ValueError, TypeError):
        return out
    if egri.ndim != 2 or len(egri) == 0:
        return out
    for g, (sutun, t_hedef) in ZAMAN_ORNEGI.items():
        i = int(np.argmin(np.abs(egri[:, 0] - t_hedef)))
        if abs(egri[i, 0] - t_hedef) <= ZAMAN_PAYI * t_hedef:
            deger = egri[i, sutun] - (1.0 if sutun == 2 else 0.0)
            out[g] = donustur(g, float(deger))
    return out


def _gp_q2(X, y) -> float:
    """GP'nin bırak-bir-θ `q2`'si (tam veride hiperparametrelerle)."""
    v = gp_uydur(DART_UZAYI_S3, X, y)
    e, _ = gp_grup_loo(v, y, _gruplar(X))
    ss = float(np.sum((y - y.mean()) ** 2))
    return float(1.0 - np.sum(e ** 2) / ss) if ss > 0 else float("nan")


def gozlem_sec(kayitlar: list[dict], s_n: dict | None,
               vekil: str = "kuadratik", genis: bool = False) -> tuple[list[str], dict]:
    """Kilitli seçim: sonlu kesir, N yargısı (varsa), tam veride `q2`.

    `q2` seçilen vekilin kendisinden: kuadratikte tek-koşu LOO
    (`fit_surrogate`), GP'de bırak-bir-θ. Polinomun eşik biçimini
    göremediği bir gözlenebiliri GP yolunda polinom yargısıyla elemek,
    GP'ye geçmenin gerekçesini boşa çıkarırdı.
    """
    tani = {}
    secilen = []
    X = np.array([k["theta"] for k in kayitlar], float)
    adaylar = list(DONUSUMLER) + (list(DONUSUMLER_ZAMAN) if genis else [])
    for g in adaylar:
        y = np.array([k.get(g, float("nan")) for k in kayitlar], float)
        sonlu = np.isfinite(y)
        t = {"sonlu_kesir": float(sonlu.mean()) if len(y) else 0.0}
        # P-v4b: zaman ornekleri N raporunda YOK; yalniz sonluluk + q2 kapisi.
        if s_n is not None and g in DONUSUMLER:
            t["N_karar"] = s_n.get("gozlem", {}).get(g, {}).get("karar", "YOK")
        if t["sonlu_kesir"] < SONLU_EN_AZ:
            t["neden"] = "SONLU DEGIL"
        elif s_n is not None and g in DONUSUMLER and t["N_karar"] != "AYIRT EDIYOR":
            t["neden"] = "N AYIRT ETMIYOR"
        elif vekil == "gp":
            q2 = _gp_q2(X[sonlu], y[sonlu])
            t["q2"] = q2
            t["neden"] = "SECILDI" if (np.isfinite(q2) and q2 > Q2_ESIGI) \
                else "VEKIL YETERSIZ"
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


def kuculmus_kor(Z: np.ndarray, lam: float = KUCULTME) -> np.ndarray:
    """Standartlaştırılmış artıklardan birim köşegene küçültülmüş korelasyon."""
    Z = np.atleast_2d(np.asarray(Z, float))
    k = Z.shape[1]
    C = np.corrcoef(Z, rowvar=False).reshape(k, k) if k > 1 else np.ones((1, 1))
    return (1.0 - lam) * C + lam * np.eye(k)


def _izgara_u(n_grid: int) -> np.ndarray:
    eksen = np.linspace(0.0, 1.0, n_grid)
    izg = np.meshgrid(*([eksen] * DART_UZAYI_S3.ndim), indexing="ij")
    return np.column_stack([a.ravel() for a in izg])


def _izgara_tasarimi(n_grid: int) -> np.ndarray:
    return design_matrix(_izgara_u(n_grid))


def _posterior_islevi(X, Y, n_grid, vekil="kuadratik", baslangic=None, artik="loo"):
    """Eğitim → `(y, gürültü çarpanı) → GridPosterior`."""
    space = DART_UZAYI_S3
    if vekil == "kuadratik":
        C, S = _egit(X, Y, artik)
        tahmin = _izgara_tasarimi(n_grid) @ C
        return lambda y, c: grid_posterior_kovaryans(space, tahmin, y, c * S, n_grid)
    if vekil != "gp":
        raise ValueError(f"bilinmeyen vekil: {vekil}")
    grup = _gruplar(X)
    Ug = _izgara_u(n_grid)
    mu = np.empty((len(Ug), Y.shape[1]))
    var = np.empty_like(mu)
    Z = np.empty_like(Y)
    for i in range(Y.shape[1]):
        v = gp_uydur(space, X, Y[:, i],
                     baslangic=None if baslangic is None else baslangic[i])
        if artik == "kfold4":
            Z[:, i] = _gp_kfold_z(X, Y[:, i], grup, v.logp)
        else:
            e, s2 = gp_grup_loo(v, Y[:, i], grup)
            Z[:, i] = e / np.sqrt(s2)
        mu[:, i], var[:, i] = v.predict_u(Ug)
    R = kuculmus_kor(Z)
    if artik == "kfold4":
        # P-v3: GP ongoru varyansi da K-kat artiklarinin olcegine
        # getirilir (standart artik sapmasi^2 kadar sisirme, >= 1).
        var = var * np.maximum(np.var(Z, axis=0, ddof=1), 1.0)[None, :]
    return lambda y, c: grid_posterior_hetero(space, mu, c * var, y, R, n_grid)


def _egit(X, Y, artik="loo"):
    """Vekil katsayıları + bırak-bir-θ (ya da K-kat) artıklarından küçültülmüş kovaryans."""
    space = DART_UZAYI_S3
    grup = _gruplar(X)
    C = np.empty((design_matrix(np.zeros((1, space.ndim))).shape[1], Y.shape[1]))
    E = np.empty_like(Y)
    for i in range(Y.shape[1]):
        C[:, i] = fit_surrogate(space, X, Y[:, i]).coef
        if artik == "kfold4":
            E[:, i] = kfold_artiklari(X, Y[:, i], grup)
        else:
            E[:, i] = loo_artiklari(space, X, Y[:, i], gruplar=grup)
    return C, kuculmus_kov(E)


def kat_ata(grup: np.ndarray, K: int = KAT_SAYISI) -> np.ndarray:
    """θ-grubunu kata ata: grup kimliği `% K` (deterministik; grup
    kimlikleri tasarım sırasında verildiği için LHS katmanlarına dağılır)."""
    return np.asarray(grup) % K


def kfold_artiklari(X, y, grup, K: int = KAT_SAYISI) -> np.ndarray:
    """P-v3: θ-gruplu K-kat çapraz doğrulama artıkları (kuadratik).

    A82 tanısı: bırak-bir-θ artıkları dış örneklem hatasını `~1,4` kat
    küçük gösterdi — tek θ çıkınca komşuları vekili aynı yere çeker, köşe
    dışdeğerlemesi hiç sınanmaz. Çeyreği birlikte çıkarmak dış örneklemin
    geometrisine daha yakın.
    """
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    kat = kat_ata(grup, K)
    e = np.empty(len(y))
    for f in range(K):
        t = kat == f
        v = fit_surrogate(DART_UZAYI_S3, X[~t], y[~t])
        e[t] = y[t] - v.predict(X[t])
    return e


def _gp_kfold_z(X, y, grup, logp, K: int = KAT_SAYISI) -> np.ndarray:
    kat = kat_ata(grup, K)
    z = np.empty(len(y))
    for f in range(K):
        t = kat == f
        v = gp_uydur(DART_UZAYI_S3, X[~t], y[~t], baslangic=logp)
        mu, var = v.predict_u(DART_UZAYI_S3.to_unit(X[t]))
        z[t] = (y[t] - mu) / np.sqrt(var)
    return z


def _vaka(post_fn, y, u, grup, carpanlar) -> dict:
    space = DART_UZAYI_S3
    vaka = {"grup": int(grup), "gercek_u": np.asarray(u).tolist(), "carpan": {}}
    for c in carpanlar:
        post = post_fn(y, c)
        vaka["carpan"][float(c)] = {
            "hdi68": post.hdi_u.tolist(),
            "hdi95": [_aralik(post, j, 0.025, 0.975) for j in range(space.ndim)],
            "genislik": post.width_u.tolist(),
            "cakili": [post.pinned(j) for j in range(space.ndim)],
            "ortalama_u": post.mean_u.tolist(),
        }
    return vaka


def kapali_dongu(X, Y, *, n_grid: int = N_IZGARA,
                 carpanlar=GURULTU_CARPANLARI, vekil: str = "kuadratik",
                 artik: str = "loo") -> list[dict]:
    """θ-grubu başına bırak-bir-θ kapalı döngü vakaları.

    GP'de hiperparametreler önce tam veride çok-başlangıçla bulunur; her
    katta oradan yerel arama yapılır (katlar arası ucuz, sonuç deterministik).
    """
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    grup = _gruplar(X)
    U = DART_UZAYI_S3.to_unit(X)
    baslangic = ([gp_uydur(DART_UZAYI_S3, X, Y[:, i]).logp for i in range(Y.shape[1])]
                 if vekil == "gp" else None)
    vakalar = []
    for g in np.unique(grup):
        egit = grup != g
        post_fn = _posterior_islevi(X[egit], Y[egit], n_grid, vekil, baslangic, artik)
        for r in np.flatnonzero(~egit):
            vakalar.append(_vaka(post_fn, Y[r], U[r], g, carpanlar))
    return vakalar


def dis_ornek(Xe, Ye, Xt, Yt, *, n_grid: int = N_IZGARA,
              carpanlar=GURULTU_CARPANLARI, vekil: str = "kuadratik",
              artik: str = "loo") -> list[dict]:
    """Bütün eğitim kümesiyle vekil; HİÇ görülmemiş ikinci tasarımda sına.

    Kapalı döngüden farkı: gözlenebilir seçimi ve vekil aynı veriden
    geliyordu (hafif iyimserlik). Burada sınama kümesi seçimde de yok.
    """
    Xe, Ye = np.asarray(Xe, float), np.asarray(Ye, float)
    Xt, Yt = np.asarray(Xt, float), np.asarray(Yt, float)
    post_fn = _posterior_islevi(Xe, Ye, n_grid, vekil, artik=artik)
    U = DART_UZAYI_S3.to_unit(Xt)
    grup = _gruplar(Xt)
    return [_vaka(post_fn, Yt[r], U[r], grup[r], carpanlar) for r in range(len(Xt))]


def katli_dogrulama(X, Y, *, K: int = KAT_SAYISI, n_grid: int = N_IZGARA,
                    carpanlar=GURULTU_CARPANLARI, vekil: str = "kuadratik",
                    artik: str = "kfold4") -> list[dict]:
    """P-v4: havuzlanmış tasarımda θ-gruplu K-kat dış doğrulama.

    Her katta vekil ve gürültü kovaryansı YALNIZ öbür katlarla kurulur;
    o kattaki θ'lar (iki tohumuyla) hiç görülmemiş gözlem sayılır. N→N2
    dış örnekleminin geometrisini korur ama eğitim `23 → 36` θ olur
    (A82: 24 θ'lık vekilin kendi sapması baskındı).
    """
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    grup = _gruplar(X)
    kat = kat_ata(grup, K)
    U = DART_UZAYI_S3.to_unit(X)
    vakalar = []
    for f in range(K):
        t = kat == f
        post_fn = _posterior_islevi(X[~t], Y[~t], n_grid, vekil, artik=artik)
        for r in np.flatnonzero(t):
            vakalar.append(_vaka(post_fn, Y[r], U[r], grup[r], carpanlar))
    return vakalar


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


def yol_sec(kuadratik: dict, gp: dict) -> dict:
    """§4c: iki yolun DIŞ ÖRNEKLEM yargılarından esas olanı seç (kilitli)."""
    def elendi(d):
        return d["genel"].startswith("KALIBRASYON") or "GECERSIZ" in d["genel"]

    def n_cozulen(d):
        return sum(e["karar"].startswith("COZULUYOR") for e in d["eksen"].values())

    aday = {ad: d for ad, d in (("kuadratik", kuadratik), ("gp", gp)) if not elendi(d)}
    if not aday:
        return {"esas": None, "genel": "KALIBRASYON DUSTU"}
    if len(aday) == 1:
        esas = next(iter(aday))
    else:
        esas = "gp" if n_cozulen(gp) > n_cozulen(kuadratik) else "kuadratik"
    return {"esas": esas, "genel": aday[esas]["genel"],
            "cozulen": {ad: n_cozulen(d) for ad, d in aday.items()}}


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
          test_kayitlar: list[dict] | None = None, vekil: str = "kuadratik",
          artik: str = "loo", katli: bool = False, genis: bool = False) -> dict:
    secilen, tani = gozlem_sec(kayitlar, s_n, vekil, genis)
    out = {"vekil": vekil, "artik": artik, "genis": genis, "secim": tani,
           "secilen": secilen}
    if not secilen:
        out["genel"] = "GOZLENEBILIR YOK"
        return out
    X, Y = _matrisler(kayitlar, secilen)
    out.update(n_kosu=int(len(X)), n_theta=int(len(np.unique(_gruplar(X)))))
    if katli:
        # P-v4: kapali dongu yerine K-kat dis dogrulama; yargi `katli` altinda.
        d = _yargila(katli_dogrulama(X, Y, n_grid=n_grid, vekil=vekil, artik=artik))
        d.update(n_kosu=int(len(X)), n_theta=out["n_theta"], K=KAT_SAYISI)
        out["katli"] = d
        out["genel"] = d["genel"]
        return out
    out.update(_yargila(kapali_dongu(X, Y, n_grid=n_grid, vekil=vekil, artik=artik)))
    if test_kayitlar:
        Xt, Yt = _matrisler(test_kayitlar, secilen)
        if len(Xt):
            d = _yargila(dis_ornek(X, Y, Xt, Yt, n_grid=n_grid, vekil=vekil, artik=artik))
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
    ap.add_argument("--vekil", choices=("kuadratik", "gp"), default="kuadratik")
    ap.add_argument("--genis-gozlem", action="store_true",
                    help="P-v4b: 8 ve 16 ms beta-1 ve M_ejekta zaman ornekleri de aday")
    ap.add_argument("--katli", action="store_true",
                    help="P-v4: --desen havuzunda theta-gruplu 4-kat dis dogrulama")
    ap.add_argument("--artik", choices=ARTIK_KIPLERI, default="loo",
                    help="gurultu kovaryansi: 'loo' birak-bir-theta (P), "
                         "'kfold4' theta-gruplu 4 kat (P-v3, A82)")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    s_n = json.loads(a.s_n.read_text(encoding="utf-8")) \
        if a.s_n and a.s_n.exists() else None
    kayit = kayitlari_oku(a.kok, a.desen)
    test = kayitlari_oku(a.kok, a.test_desen) if a.test_desen else None
    out = rapor(kayit, s_n, test_kayitlar=test, vekil=a.vekil, artik=a.artik,
                katli=a.katli, genis=a.genis_gozlem)
    print("=" * 78)
    print(f"PROTOKOL P -- kapali dongu kalibrasyonu ({len(kayit)} kosu, "
          f"N yargisi {'VAR' if s_n else 'YOK'}, vekil {a.vekil})")
    print("=" * 78)
    for g, t in out["secim"].items():
        print(f"  {g:>12}: {t}")
    for ad, e in out.get("eksen", {}).items():
        print(f"  {ad:>12}: kapsama68 {e['kapsama68']:.2f}  kapsama95 "
              f"{e['kapsama95']:.2f}  medyan genislik {e['medyan_genislik']:.3f}  "
              f"cakili {e['cakili']}/{e['n']}  -> {e['karar']}")
    if "gurultu_tepkisi" in out:
        print(f"  gurultu tepkisi: {out['gurultu_tepkisi']}")
    if "katli" in out:
        d = out["katli"]
        print(f"\nP-v4 KATLI DIS DOGRULAMA ({d['n_kosu']} kosu, {d['n_theta']} theta, "
              f"K={d['K']}, artik {out['artik']})")
        for ad, e in d["eksen"].items():
            print(f"  {ad:>12}: kapsama68 {e['kapsama68']:.2f}  kapsama95 "
                  f"{e['kapsama95']:.2f}  medyan genislik {e['medyan_genislik']:.3f}  "
                  f"-> {e['karar']}")
        print(f"  gurultu tepkisi: {d['gurultu_tepkisi']}")
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
