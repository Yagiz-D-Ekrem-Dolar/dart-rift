"""Posterior figür verisi — katlı dış doğrulamanın marjinalleri ve PIT değerleri.

Kilitli yargıyı DEĞİŞTİRMEZ; P-v4/P-v4b ile aynı kodu (`katli_dogrulama`
ile aynı katlar, aynı vekil ve kovaryans) koşar ve her vakanın:

- eksen başına marjinal posteriorunu (birim küpte, `N_IZGARA` düğüm),
- gerçek `u`'yu,
- **PIT** değerini (`F_marjinal(u_gerçek)`) — kalibre bir posteriorda
  `Uniform(0, 1)`,

JSON'a yazar. Çizim yerelde (`p_sekil_ciz.py`).

Kullanim:
    python scripts/p_sekil_verisi.py --kok kampanya --desen "Nk_...,N2k_...,Nkd_..." \\
        --s-n kampanya/S_Nkh.json --genis-gozlem --json kampanya/P_sekil_kaba.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

import p_kalibrasyon_raporu as pr  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402

NOMINAL = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.68, 0.8, 0.9, 0.95)


def pit(marjinal: np.ndarray, eksen: np.ndarray, u: float) -> float:
    """Orta nokta birikimi: düğüm kendi kütlesinin YARISINI içerir.

    İlk sürüm `cumsum`'ı doğrudan kullanıyordu; düğüm kendi kütlesinin
    tamamını sayınca CDF yarım bölme yukarı kayıyor ve dar posteriorda PIT
    `0,5` yerine `0,7` ortalamaya çıkıyordu (sentetik doğru modelde yakalandı).
    """
    # Uc dugumler YARIM hucre (A85, ikinci adim): yamuk agirlik. Duz
    # dagilimda PIT(u) = u tam olarak; yalniz orta nokta 0,16 -> 0,1515 veriyordu.
    # A87 (2026-09-15): ilk yamuk surumu (cumsum(w) - w/2) uc dugumleri ikinci
    # kez yariliyordu (F(0) = p0/4); dogrusu hucre integralleri, F_0 = 0, F_N = 1.
    p = np.asarray(marjinal, float)
    kum = np.cumsum(p) - 0.5 * p[0] - 0.5 * p
    kum = kum / kum[-1]
    return float(np.interp(u, eksen, kum, left=0.0, right=1.0))


def kapsama_egrisi(pitler: np.ndarray, seviyeler=NOMINAL) -> list[float]:
    """Merkezi `q` aralığı gerçeği içeriyor ⇔ `|PIT − 0,5| ≤ q/2`."""
    p = np.asarray(pitler, float)
    return [float(np.mean(np.abs(p - 0.5) <= q / 2)) for q in seviyeler]


def veri(X, Y, *, vekil="kuadratik", artik="kfold4", n_grid=pr.N_IZGARA) -> dict:
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    grup = pr._gruplar(X)
    kat = pr.kat_ata(grup)
    U = DART_UZAYI_S3.to_unit(X)
    eksen = np.linspace(0.0, 1.0, n_grid)
    vakalar = []
    for f in range(pr.KAT_SAYISI):
        t = kat == f
        post_fn = pr._posterior_islevi(X[~t], Y[~t], n_grid, vekil, artik=artik)
        for r in np.flatnonzero(t):
            post = post_fn(Y[r], 1.0)
            marj = [post.marginal(j) for j in range(3)]
            vakalar.append({"theta": X[r].tolist(), "u": U[r].tolist(), "kat": int(f),
                            "marjinal": [m.tolist() for m in marj],
                            "pit": [pit(marj[j], eksen, U[r, j]) for j in range(3)],
                            "ortalama_u": post.mean_u.tolist(),
                            "hdi68_u": post.hdi_u.tolist()})
    pitler = np.array([v["pit"] for v in vakalar])
    return {"eksen_u": eksen.tolist(), "eksenler": list(pr.EKSENLER),
            "nominal": list(NOMINAL),
            "kapsama_egrisi": {ad: kapsama_egrisi(pitler[:, j])
                               for j, ad in enumerate(pr.EKSENLER)},
            "vakalar": vakalar}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--desen", required=True)
    ap.add_argument("--s-n", type=Path, default=None)
    ap.add_argument("--vekil", choices=("kuadratik", "gp"), default="kuadratik")
    ap.add_argument("--genis-gozlem", action="store_true")
    ap.add_argument("--json", type=Path, required=True)
    a = ap.parse_args(argv)
    s_n = json.loads(a.s_n.read_text(encoding="utf-8")) if a.s_n else None
    kayit = pr.kayitlari_oku(a.kok, a.desen)
    secilen, _ = pr.gozlem_sec(kayit, s_n, a.vekil, a.genis_gozlem)
    X, Y = pr._matrisler(kayit, secilen)
    out = veri(X, Y, vekil=a.vekil)
    out.update(secilen=secilen, vekil=a.vekil, genis=a.genis_gozlem, desen=a.desen)
    a.json.write_text(json.dumps(out), encoding="utf-8")
    for ad, k in out["kapsama_egrisi"].items():
        print(ad, "kapsama (nominal", list(NOMINAL), "):", np.round(k, 2).tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
