"""Protokol L — üç eksenli duyarlılık pilotu (uzman Soru 13).

Uzman: *"Ölçeklenmiş parametrelerde, gözlem hatalarıyla beyazlatılmış
J'nin tekil değerlerine bakın. Bu pilotu üçüncü ayın sonunda değil ilk
ayda yapın. En küçük tekil değer sayısal/yerleşim gürültüsünün
altındaysa, daha fazla MCMC o ekseni açmaz."*

## Tanım

- Parametreler **önsel aralığın çeyreği** ile ölçeklenir: `δ_j` bir
  birim. `θ_c ± δ_j` merkezî farkı:

      J_kj = [y_k(θ_c + δ_j) − y_k(θ_c − δ_j)] / 2

  iki sahne tohumunun ortalaması (ortak rastgele sayılar).
- Beyazlatma: `σ_k`, merkez noktasının `n` sahne gerçeklemesi
  arasındaki sapma. `J̃ = J / σ`.
- Tekil değerler `s₁ ≥ s₂ ≥ s₃`. `s = 2`: çeyrek aralıklık bir
  değişiklik gerçekleme gürültüsünün `2σ` üstünde iz bırakıyor.

## Kilitli eşikler (koşudan ÖNCE)

| `s` | yön |
|---|---|
| `≥ 2` | AYIRT EDİLEBİLİR |
| `1 – 2` | ZAYIF |
| `< 1` | GÜRÜLTÜ ALTINDA |

Türev tekrarı: iki tohumun beyaz sütunları arasındaki bağıl fark
`> 0,5` ise o eksen **"türev gürültüde"** işaretlenir; tekil değer
yargısı o eksen için OKUNMAZ.

Kullanim:
    python scripts/duyarlilik_raporu.py --kok kampanya --kol L_ara_kirpik
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

# --- PROTOKOL L esikleri, SONUCLARDAN ONCE kilitlendi ------------------
AYIRT_ESIGI = 2.0
ZAYIF_ESIGI = 1.0
TUREV_TEKRAR_ESIGI = 0.5
#: Merkez gerceklemesi en az bu kadar olmali (sigma kestirimi).
EN_AZ_GERCEKLEME = 4

#: Merkez nokta ve adimlar -- onsel S3'un ortasi ve CEYREK araliklari.
#: log10 Y0 icin aralik 4 onluk, ceyrek 1; adim yarim onluk tutuldu ki
#: gecis bolgesinin tek tarafinda kalinsin (yerel dogrusallik).
MERKEZ = (1.15, 1.0e5, 0.275)
ADIM = (0.075, 0.5, 0.075)           # (a_b, log10 Y0, f)
EKSENLER = ("boulder_alpha0", "log10_Y0", "f_boulder")


def tasarim() -> dict:
    """Merkez + ±adım noktaları (Y0 log uzayında adımlanır)."""
    a, y, f = MERKEZ
    ly = np.log10(y)
    pts = {"merkez": (a, y, f)}
    for j, ad in enumerate(EKSENLER):
        for isr in (+1, -1):
            q = [a, ly, f]
            q[j] += isr * ADIM[j]
            pts[f"{ad}{'+' if isr > 0 else '-'}"] = (q[0], 10.0 ** q[1], q[2])
    return pts


def _anahtar(th) -> tuple:
    return tuple(np.round(np.asarray(th, float), 9))


def jakobiyen(gozlem: dict, sigma: np.ndarray) -> dict:
    """`gozlem[(nokta_adi, tohum)] = y (k,)` → beyaz J ve tekrar ölçüsü."""
    tohumlar = sorted({t for (ad, t) in gozlem if ad != "merkez"})
    sutunlar, tekrar = [], []
    for ad in EKSENLER:
        ests = []
        for t in tohumlar:
            yp, ym = gozlem.get((ad + "+", t)), gozlem.get((ad + "-", t))
            if yp is not None and ym is not None:
                ests.append((np.asarray(yp) - np.asarray(ym)) / 2.0 / sigma)
        if not ests:
            sutunlar.append(np.full(len(sigma), np.nan))
            tekrar.append(float("nan"))
            continue
        E = np.array(ests)
        sutunlar.append(E.mean(axis=0))
        if len(E) >= 2:
            fark = np.linalg.norm(E[0] - E[1])
            olcek = 0.5 * (np.linalg.norm(E[0]) + np.linalg.norm(E[1]))
            tekrar.append(float(fark / olcek) if olcek > 0 else float("inf"))
        else:
            tekrar.append(float("nan"))
    return {"J": np.column_stack(sutunlar), "tekrar": tekrar,
            "n_tohum": len(tohumlar)}


def yargi(J: np.ndarray, tekrar) -> dict:
    """Tekil değerler + kilitli tablo."""
    if not np.all(np.isfinite(J)):
        return {"karar": "OKUNMAZ", "sebep": "J'de tanimsiz eleman"}
    U, s, Vt = np.linalg.svd(J, full_matrices=False)
    etiket = ["AYIRT EDILEBILIR" if v >= AYIRT_ESIGI else
              "ZAYIF" if v >= ZAYIF_ESIGI else "GURULTU ALTINDA" for v in s]
    n_ayirt = int(np.sum(s >= AYIRT_ESIGI))
    karar = {3: "UC EKSEN AYRISIYOR", 2: "IKI YON", 1: "TEK YON",
             0: "HICBIR YON"}[n_ayirt]
    gurultulu = [EKSENLER[j] for j, r in enumerate(tekrar)
                 if np.isfinite(r) and r > TUREV_TEKRAR_ESIGI]
    return {"karar": karar, "tekil": s.tolist(), "etiket": etiket,
            "zayif_yon": Vt[-1].tolist(), "guclu_yon": Vt[0].tolist(),
            "turev_gurultude": gurultulu,
            "kosul_sayisi": float(s[0] / s[-1]) if s[-1] > 0 else float("inf")}


def gozlem_topla(kok: Path, kol: str) -> tuple[dict, list]:
    """`{kol}_*.durumlar` → `{(nokta_adi, tohum): y}` ve gözlem adları."""
    import vekil_posterior as vp
    from gozlem_vektoru import GOZLEMLER, gozlem_vektoru

    adlar = {_anahtar(th): ad for ad, th in tasarim().items()}
    out = {}
    for dz in sorted(glob.glob(str(kok / f"{kol}_*.durumlar"))):
        t = vp._tohum_ayikla(dz)
        for yol in sorted(Path(dz).glob("nokta_*.npz")):
            z = np.load(yol)
            ad = adlar.get(_anahtar(z["theta"]))
            if ad is None:
                continue
            g = gozlem_vektoru(z)
            out[(ad, t)] = np.array([g[k] for k in GOZLEMLER])
    return out, list(GOZLEMLER)


def rapor(gozlem: dict, adlar: list) -> dict:
    merkez = np.array([y for (ad, _), y in gozlem.items() if ad == "merkez"])
    if len(merkez) < EN_AZ_GERCEKLEME:
        return {"karar": "OKUNMAZ",
                "sebep": f"merkez gerceklemesi {len(merkez)} < {EN_AZ_GERCEKLEME}"}
    sigma = merkez.std(axis=0, ddof=1)
    tum = np.array(list(gozlem.values()))
    kullan = (np.isfinite(sigma) & (sigma > 0)
              & np.all(np.isfinite(tum), axis=0))
    dusen = [a for a, k in zip(adlar, kullan, strict=True) if not k]
    if kullan.sum() < 3:
        return {"karar": "OKUNMAZ", "sebep": f"gecerli gozlem < 3; dusen {dusen}"}
    g2 = {k: v[kullan] for k, v in gozlem.items()}
    jk = jakobiyen(g2, sigma[kullan])
    y = yargi(jk["J"], jk["tekrar"])
    y.update(gozlemler=[a for a, k in zip(adlar, kullan, strict=True) if k],
             dusen_gozlemler=dusen, n_merkez=int(len(merkez)),
             sigma=sigma[kullan].tolist(), J=jk["J"].tolist(),
             turev_tekrari=jk["tekrar"], n_turev_tohumu=jk["n_tohum"])
    return y


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--kol", nargs="+", required=True)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--tasarim-yaz", type=Path, default=None,
                    help="tasarim JSON'unu yaz ve cik (surucu icin)")
    ap.add_argument("--sadece-merkez", action="store_true",
                    help="--tasarim-yaz ile: yalniz merkez noktasi "
                         "(gerceklesme gurultusu gorevleri)")
    a = ap.parse_args(argv)
    if a.tasarim_yaz:
        t = tasarim()
        if a.sadece_merkez:
            t = {"merkez": t["merkez"]}
        a.tasarim_yaz.write_text(json.dumps(
            {"theta": [list(v) for v in t.values()], "adlar": list(t)},
            indent=1), encoding="utf-8")
        return 0
    cikti = {}
    for kol in a.kol:
        g, adlar = gozlem_topla(a.kok, kol)
        r = rapor(g, adlar)
        cikti[kol] = r
        print("=" * 72)
        print(f"PROTOKOL L -- {kol}   ({len(g)} durum)")
        if r["karar"] == "OKUNMAZ":
            print(f"  OKUNMAZ: {r['sebep']}")
            continue
        print(f"  gozlemler: {r['gozlemler']}  (dusen: {r['dusen_gozlemler']})")
        for i, (s, e) in enumerate(zip(r["tekil"], r["etiket"], strict=True)):
            print(f"  s{i + 1} = {s:8.3f}   {e}")
        print(f"  zayif yon (a_b, logY0, f): {np.round(r['zayif_yon'], 3)}")
        print(f"  turev tekrari: {np.round(r['turev_tekrari'], 3)}"
              f"  gurultude: {r['turev_gurultude']}")
        print(f"  YARGI: {r['karar']}")
    if a.json:
        a.json.write_text(json.dumps(cikti, indent=1, default=float),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
