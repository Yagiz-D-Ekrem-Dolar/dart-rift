"""U/V koşularına **ek tanı** — ADR-0050 ölçümleriyle (yargı DEĞİL).

Kilitli U ve V yargısı (KAYIT-057, KAYIT-064) **değişmez**. Bu betik aynı
`npz` durumlarını yeni ölçümlerden geçirir ve şunları yan yana yazar:

1. `beta_kacan` (defterin kilitli ölçütü, `r > R` ve `v_r > v_esc`),
2. `beta_km` — bağlı kütle merkezi yolu (L1'in 2. yöntemi) ve
   `mermi_bagsiz_kesri` (`1`'e yakınsa `beta_km` **okunmaz**),
3. ejekta **koni açısı** (gözlem: `140 ± 4°`, L17),
4. **bekleyen** madde: `r ≤ R` ama `v_r > v_esc` — momentumu ve çarpma
   noktasına göre profili (`momentum_transfer`). Önceden ölçülmüştü ki bu
   maddenin çoğu kazı değil **cismin çınlaması**; profil onu gösterir.

Kullanim:
    python scripts/uv_ek_tani.py --kok kampanya --json kampanya/S_UV_ek.json
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

from dartrift.observables.beta_iki_yontem import (  # noqa: E402
    beta_iki_yontem,
)
from dartrift.observables.momentum_transfer import (  # noqa: E402
    bekleyen_profili,
    escape_speed,
    kacis_bekleyenler,
)

DESEN = re.compile(
    r"(?P<onek>[UV])_(?P<varyant>[UV]\d+)_(?P<merdiven>kaba|orta|ince)"
    r"_sahne(?P<tohum>\d+)")


def tek_dosya(f: str) -> dict:
    z = np.load(f)
    x = np.asarray(z["x"], float)
    v = np.asarray(z["v"], float)
    m = np.asarray(z["m"], float)
    fk = np.asarray(z["mermi_kesri"], float)
    hedef = fk < 0.5
    R = float(z["R"])
    ehat = np.asarray(z["ehat"], float)
    p_imp = float(z["p_imp"])
    M_hedef = float(m[hedef].sum())
    v_esc = float(escape_speed(M_hedef, R))
    b2 = beta_iki_yontem(x, v, m, mermi_kesri=fk, R=R, v_esc=v_esc,
                         ehat=ehat, p_imp=p_imp)
    bek = kacis_bekleyenler(x, v, m, hedef=hedef, R=R, v_esc=v_esc)
    # bekleyenin EKSENEL momentumu: defterin isaret kuralinda beta katkisi
    p_bek = float(np.asarray(bek["bekleyen_p"], float) @ ehat)
    # Carpma noktasi `npz`de saklanmiyor; U/V sahnelerinde nisan +z ve mermi
    # `ehat` yonunde gidiyor -> carpma noktasi yuzeyde `-R * ehat`.
    carpma = -R * ehat
    prof = bekleyen_profili(x, v, m, hedef=hedef, R=R, v_esc=v_esc,
                            carpma_noktasi=carpma)
    return {
        "t": float(z["t"]),
        "beta_kacan": b2["beta_kacan_hedef"],
        "beta_km": b2["beta_km"],
        "mermi_bagsiz_kesri": b2["mermi_bagsiz_kesri"],
        "koni_tam_acisi_derece": b2["koni_tam_acisi_derece"],
        "M_ejekta_hedef": b2["M_ejekta_hedef"],
        "M_hedef": M_hedef,
        "n_bekleyen": int(bek["n_bekleyen"]),
        "bekleyen_kutle_kesri": float(bek["bekleyen_kutle_kesri"]),
        # UST SINIR: bekleyenin TAMAMI ejekta sayilsaydi beta ne olurdu
        "beta_ust_sinir_bekleyenle": b2["beta_kacan_hedef"] - p_bek / p_imp,
        "bekleyen_profili_yargisi": prof.get("yargi"),
        "bekleyen_yakin_oran": prof.get("yakin_oran"),
        "bekleyen_uzak_oran": prof.get("uzak_oran"),
        "bekleyen_kusaklar": prof.get("kusaklar"),
        "carpma_noktasi": [float(t) for t in carpma],
    }


def topla(kok: Path, onekler=("U", "V")) -> dict:
    out: dict = {}
    for onek in onekler:
        for dz in sorted(glob.glob(str(kok / f"{onek}_*_*_sahne*.durumlar"))):
            m = DESEN.search(Path(dz).name)
            if not m:
                continue
            for f in sorted(glob.glob(dz + "/nokta_*.npz")):
                ad = f"{m.group('varyant')}:{m.group('merdiven')}:{m.group('tohum')}"
                out[ad] = tek_dosya(f)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    v = topla(a.kok)
    print("=" * 92)
    print(f"U/V EK TANI (ADR-0050 olcumleri) -- {len(v)} kosu; YARGI DEGIL")
    print("=" * 92)
    print(f"{'kosu':>22} {'t':>6} {'beta':>7} {'beta_km':>8} {'mermi_bagsiz':>12} "
          f"{'koni':>7} {'bekleyen%':>10} {'beta_ust':>9} {'profil':>16}")
    for ad, k in sorted(v.items()):
        print(f"{ad:>22} {k['t']:>6.3f} {k['beta_kacan']:>7.3f} "
              f"{k['beta_km']:>8.3f} {k['mermi_bagsiz_kesri']:>12.3f} "
              f"{k['koni_tam_acisi_derece']:>7.1f} "
              f"{100 * k['bekleyen_kutle_kesri']:>10.2f} "
              f"{k['beta_ust_sinir_bekleyenle']:>9.3f} "
              f"{str(k['bekleyen_profili_yargisi']):>16}")
    if a.json:
        a.json.write_text(json.dumps(v, indent=1, default=float),
                          encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
