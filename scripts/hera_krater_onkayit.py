"""PROTOKOL-HT (+ EK-1) — Hera için mühürlü **krater** ön kaydını üretir.

Ana protokol `docs/truba/PROTOKOL-HT-HERA-TAHMIN.md` 2026-09-14'te,
EK-1 `docs/truba/PROTOKOL-HT-EK1-2026-10-28.md` ise bu betik yazılmadan
ve **hiçbir öngörü hesaplanmadan önce** kilitlendi. Burada hiçbir eşik,
kantil, nokta kümesi ya da yargı **tanımlanmaz**; hepsi oradan okunur.

Zincir:

1. Krater değerleri `tani_tarama_yonu.json`'dan (ADR-0063 ölçümü).
   Kullanılan nokta kümesi EK-1 §3: yalnız **çapraz doğrulanmış**
   olanlar. Dışlananlar sayılır ve sebebiyle kayda girer (kural 8).
2. `θ` ↔ kilitli tasarım eşlemesi dosyanın kendi `theta`'sından.
3. `V_krater` ve `d_merkez` için GP vekili (EK-1 §4: ADR-0058 ailesi).
4. Posterior, `uretim_posterior`'ün birebir aynı yolundan (`_ortak`),
   `grid_posterior_hetero` ile. EK-1 §5: ağırlık **POSTERIOR**.
5. `20 000` örnek, tohum `20260914` (HT §3).
6. `V_krater → Y₀` koşullu eşlemesi (EK-1 §7).
7. `ONKAYIT_HERA_KRATER_<etiket>.json`, SHA-256'lı, **üzerine yazılmaz**.

Kullanım (sıfır GPU):

    python scripts/hera_krater_onkayit.py <havuz_posterior_girdi.csv> \\
        --tarama <tani_tarama_yonu.json> --etiket uretim96 \\
        --cikti docs/onkayit
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "src"))

from up_onsel_ve_tarih import _ortak, tarih_esleme  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.gp_vekil import gp_uydur  # noqa: E402
from dartrift.inference.posterior import grid_posterior_hetero  # noqa: E402

N_NOKTA, TOHUM_TASARIM = 96, 20260906

#: HT §3 -- ongoru uretilmeden once secildi.
N_ORNEK, TOHUM_ONGORU = 20000, 20260914
KANTILLER = (0.05, 0.16, 0.50, 0.84, 0.95)

#: EK-1 §3 -- yalniz bu etiketler kullanilir.
CAPRAZ_KABUL = ("EVET_distan_ile", "EVET_60m_ile")

#: EK-1 §2 -- muhurlenen gozlenebilirler (`M_ejekta` ve `R_krater` HARIC).
GOZLENEBILIRLER = ("V_krater", "d_merkez")

#: `theta = (alpha_b, Y_0, f)`.
I_Y0 = 1


def _commit() -> str:
    """Betiğin kendi deposundaki HEAD. Bulunamazsa **durur**.

    Künyesiz bir ön kayıt mühür sayılmaz (HT §4, EK-1 §9).
    """
    import subprocess
    kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        c = subprocess.run(["git", "-C", kok, "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise SystemExit(
            f"git commit okunamadi ({kok}): {e}. Kunyesiz on kayit "
            "uretilmez (EK-1 §9).") from e
    return c.stdout.strip()


def krateri_oku(yol: Path) -> tuple[dict, list]:
    """ADR-0063 ölçümü (`havuz_krater_tarama_96.csv`).

    Tek doğruluk kaynağı: hangi noktanın kabul edileceğine **aynı
    dosyadaki** `capraz_dogrulandi` sütunu karar verir. Dışlanan her
    nokta sebebiyle listeye girer — sessiz atlama yok (kural 8).

    Döner: `(kabul, dislanan)`.
    """
    import csv
    kabul: dict[int, dict] = {}
    dislanan: list[dict] = []
    n = 0
    with open(yol, newline="", encoding="utf-8") as f:
        for s in csv.DictReader(f):
            n += 1
            k, et = int(s["kuresel"]), s["capraz_dogrulandi"]
            y0 = float(s["Y0"])
            if et not in CAPRAZ_KABUL:
                dislanan.append({"idx": k, "Y0": y0, "sebep": et})
                continue
            kabul[k] = {"capraz": et, "Y0": y0,
                        "V_krater": float(s["icten_V_krater"]),
                        "d_merkez": float(s["icten_d_merkez"])}
    if n != N_NOKTA:
        raise SystemExit(f"KURAL 8: {N_NOKTA} satir BEKLENIYORDU, {n} var")
    if len(kabul) + len(dislanan) != N_NOKTA:
        raise SystemExit("KURAL 8: kabul + dislanan != 96")
    return kabul, dislanan


def _kant(x: np.ndarray) -> dict:
    return {f"q{int(100 * q):02d}": float(np.quantile(x, q))
            for q in KANTILLER}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("havuz", type=Path, help="idx,beta,ejf,kos")
    ap.add_argument("--tarama", type=Path, required=True,
                    help="havuz_krater_tarama_96.csv (ADR-0063 olcumu)")
    ap.add_argument("--etiket", required=True)
    ap.add_argument("--cikti", type=Path, default=Path("docs/onkayit"))
    ap.add_argument("--n-grid", type=int, default=60)
    a = ap.parse_args(argv)

    a.cikti.mkdir(parents=True, exist_ok=True)
    hedef = a.cikti / f"ONKAYIT_HERA_KRATER_{a.etiket}.json"
    if hedef.exists():                      # EK-1 §9: uzerine YAZILMAZ
        raise SystemExit(f"KAYIT ZATEN VAR: {hedef}. Ustune yazilmaz; "
                         "yeni etiket secin.")

    kabul, dislanan = krateri_oku(a.tarama)
    if len(kabul) < 30:
        raise SystemExit(f"kabul edilen nokta {len(kabul)} < 30; vekil "
                         "kurmak anlamsiz")

    idx = np.array(sorted(kabul), dtype=int)
    X = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA,
                              root_seed=TOHUM_TASARIM))[idx]

    # --- posterior: uretim_posterior ile BIREBIR ayni yol -------------
    o = _ortak(a.havuz, a.n_grid)
    te = tarih_esleme(o)
    te.pop("maske")
    te.pop("I")
    post = grid_posterior_hetero(DART_UZAYI_S4, o["ort"], o["varyans"],
                                 o["veri"], o["R"], n_grid=a.n_grid)
    eksen = o["eksen"]
    U = np.column_stack([g.ravel() for g in
                         np.meshgrid(*([eksen] * 3), indexing="ij")])
    p = np.asarray(post.p, dtype=np.float64).ravel()
    p = p / p.sum()

    # --- vekiller + ongoru --------------------------------------------
    rng = np.random.default_rng(TOHUM_ONGORU)
    sec = rng.choice(U.shape[0], size=N_ORNEK, p=p)
    u_orn = U[sec]
    Y0_orn = DART_UZAYI_S4.from_unit(u_orn)[:, I_Y0]

    ongoru, vekil_tani, ornekler = {}, {}, {}
    for g in GOZLENEBILIRLER:
        y = np.array([kabul[i][g] for i in idx], dtype=np.float64)
        if not np.all(np.isfinite(y)):
            raise SystemExit(f"{g}: sonlu olmayan deger var")
        gp = gp_uydur(DART_UZAYI_S4, X, y)
        mu, var = gp.predict_u(u_orn)
        orn = mu + np.sqrt(var) * rng.standard_normal(N_ORNEK)
        ornekler[g] = orn
        ongoru[g] = _kant(orn)
        # FIZIKSEL DESTEK: GP Gauss'tur, ornekler destegin disina
        # tasabilir (`V_krater < 0` imkansizdir). Orani OLCULUR ve
        # kayda girer -- vekilin ne kadar ekstrapole ettiginin dogrudan
        # gostergesi. Kirpilmaz: kirpmak genisligi sahte bicimde
        # daraltir ve ongoruyu "duzeltilmis" gosterir.
        destek_disi = (float(np.mean(orn < 0.0))
                       if g == "V_krater" else None)
        vekil_tani[g] = {"ell": gp.ell.tolist(), "n_egitim": int(len(y)),
                         "egitim_araligi": [float(y.min()), float(y.max())],
                         "ornek_destek_disi_orani": destek_disi}

    # --- V_krater -> Y0 koşullu eşlemesi (EK-1 §7) --------------------
    v = ornekler["V_krater"]
    kenar = np.quantile(v, np.linspace(0.0, 1.0, 7))
    eslem = []
    for i in range(len(kenar) - 1):
        m_ = (v >= kenar[i]) & (v <= kenar[i + 1])
        if int(m_.sum()) < 50:
            continue
        eslem.append({"V_krater_araligi_m3": [float(kenar[i]),
                                              float(kenar[i + 1])],
                      "n": int(m_.sum()), "Y0_Pa": _kant(Y0_orn[m_])})

    dis_y0 = [d["Y0"] for d in dislanan if np.isfinite(d["Y0"])]
    kabul_y0 = [kabul[i]["Y0"] for i in idx]

    kayit = {
        "protokol": "PROTOKOL-HT-HERA-TAHMIN + EK-1 (2026-10-28)",
        "etiket": a.etiket,
        "uretildi_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _commit(),
        "kosul": "POSTERIOR",
        "kosul_gerekcesi": (
            "HT §2: onsel ICINDE -> posterior agirlik. Tarih eslemesinde "
            f"model gozleme ULASIYOR: I_min = {te.get('I_min', float('nan')):.4f}, "
            f"bagdasir hacim %{100 * te.get('V_bagdasir', float('nan')):.2f}."),
        "havuz": str(a.havuz),
        "krater_olcumu": str(a.tarama),
        "t_end_s": 600.0,
        "n_ornek": N_ORNEK,
        "tohum_ongoru": TOHUM_ONGORU,
        "kantiller": list(KANTILLER),
        "nokta_kumesi": {
            "beklenen": N_NOKTA,
            "kullanilan": len(kabul),
            "dislanan": len(dislanan),
            "kullanilan_idx": [int(i) for i in idx],
            "dislanan_detay": dislanan,
            "capraz_dagilim": {
                e: sum(1 for i in idx if kabul[i]["capraz"] == e)
                for e in CAPRAZ_KABUL},
            "SECILIM_YANLILIGI": {
                "kullanilan_Y0_Pa": [float(min(kabul_y0)),
                                     float(max(kabul_y0))],
                "dislanan_Y0_Pa": ([float(min(dis_y0)), float(max(dis_y0))]
                                   if dis_y0 else None),
                "kullanilan_Y0_ortanca": float(np.median(kabul_y0)),
                "dislanan_Y0_ortanca": (float(np.median(dis_y0))
                                        if dis_y0 else None),
                "not": ("EK-1 §3: dislanan noktalar Y_0'in DUSUK ucunda "
                        "yigili. Vekil orada EKSTRAPOLE ediyor; ongoru "
                        "genisligi bunu yansitmali. Dar cikmasi basari "
                        "degil HATA isaretidir."),
            },
        },
        "vekil": vekil_tani,
        "vekil_notu": ("EK-1 §4: GP (ADR-0058 ailesi) kullanildi; HT §3 "
                       "'ikinci derece vekil' diyordu. Sapma ongoru "
                       "hesaplanmadan once EK-1'de yazildi."),
        "FIZIKSEL_DESTEK_UYARISI": (
            "V_krater ornekleri GP'nin Gauss ongoru dagilimindan geliyor "
            "ve bir kismi NEGATIF cikiyor; hacim negatif OLAMAZ. "
            "Kirpilmadi: kirpmak genisligi sahte bicimde daraltirdi. "
            "Negatif oran `vekil.V_krater.ornek_destek_disi_orani` "
            "alaninda ve vekilin ne kadar EKSTRAPOLE ettiginin dogrudan "
            "olcusudur."),
        "ONGORU": {
            "V_krater_m3": ongoru["V_krater"],
            "d_merkez_m": ongoru["d_merkez"],
        },
        "MUHURLENMEYENLER": {
            "R_krater": ("96 noktanin 2'sinde sonlu (4,0 ve 3,8 m). "
                         "A11'in 'krater yaricapi gozlenemez' yargisi "
                         "ayakta; sayi yerine bu sayim muhurlenir."),
            "M_ejekta": ("Hera'nin olcecegi bir nicelik degil VE "
                         "posteriorun kosullandigi veri "
                         "(M_EJEKTA_GOZ = 1,6e7 kg). Kendi verisini "
                         "ongoru diye muhurlemek dongusel olurdu."),
        },
        "V_krater_Y0_eslemesi": eslem,
        "yanlislanma": ("Hera'nin olcecegi deger q05-q95 disinda -> "
                        "TUTARSIZ, icinde -> TUTARLI (HT §7). Kantil "
                        "yazilir. UYARI_kaydin_parcasi yargının yanina "
                        "aynen tasinir."),
        "UYARI_kaydin_parcasi": [
            "ZAMAN OLCEGI (HT §5, artik SAYILI): model krateri "
            "t_end = 600 s'deki GECICI kraterdir; Hera SON krateri "
            "(ejekta dustukten sonra) olcecek. 2026-10-28 olcumu: "
            "eksende kacmamis ejekta 6,50-47,99 m yukseklikte, ortanca "
            "30,89 m (KAYIT-090). Bu bir MEKANIZMA on kaydidir, son "
            "krater ongorusu DEGIL.",
            "SECILIM YANLILIGI: 96 noktanin 30'u disarida ve Y_0'in "
            "dusuk ucunda yigili (EK-1 §3).",
            "n_yon = 1 (KAYIT-079): alpha_b ve f onselden ayirt "
            "edilemiyor; ongoru genisliginin bir kismi onselin "
            "genisligidir.",
            "COZUNURLUK YANLILIGI (KAYIT-085): ince kosu 7/7 noktada "
            "ayni yone sapiyor, Y_0'da x3,22. Krater bundan muaf "
            "degildir; kayit yeniden uretilecekse YENI ETIKETLE.",
            "TEK SABIT SAHNE; ongoru o sahneye kosullu.",
            "OLCUM TANIMI: krater degerleri ADR-0063'un 'icten' "
            "taramasiyla, yalniz capraz dogrulanmis noktalarda. "
            "Varsayilan operator 'distan' ve DEGISTIRILMEDI.",
        ],
    }

    govde = json.dumps(kayit, ensure_ascii=False, indent=1, sort_keys=True)
    kayit["sha256"] = hashlib.sha256(govde.encode("utf-8")).hexdigest()
    hedef.write_text(json.dumps(kayit, ensure_ascii=False, indent=1),
                     encoding="utf-8")

    print("=" * 72)
    print(f"PROTOKOL-HT + EK-1 — MUHURLU KRATER ON KAYDI  [{a.etiket}]")
    print("=" * 72)
    print(f"kullanilan nokta : {len(kabul)}/{N_NOKTA}  "
          f"({kayit['nokta_kumesi']['capraz_dagilim']})")
    print(f"dislanan         : {len(dislanan)}")
    sy = kayit["nokta_kumesi"]["SECILIM_YANLILIGI"]
    print(f"   Y0 ortanca kullanilan {sy['kullanilan_Y0_ortanca']:.2f} Pa, "
          f"dislanan {sy['dislanan_Y0_ortanca']:.2f} Pa")
    print(f"kosul            : {kayit['kosul']}")
    print(f"ornek            : {N_ORNEK}, tohum {TOHUM_ONGORU}")
    print()
    for ad, q in kayit["ONGORU"].items():
        print(f"ONGORU {ad}:")
        for k, v2 in q.items():
            print(f"   {k} = {v2:.6g}")
    print()
    print("V_krater -> Y0 eslemesi (Hera bir hacim olcerse Y0 ne olur):")
    for e in eslem:
        r = e["V_krater_araligi_m3"]
        print(f"   V {r[0]:9.2f}..{r[1]:9.2f} m3 (n={e['n']:5d})  "
              f"Y0: q05={e['Y0_Pa']['q05']:9.2f} "
              f"q50={e['Y0_Pa']['q50']:9.2f} q95={e['Y0_Pa']['q95']:9.2f} Pa")
    print()
    print(f"SHA-256 : {kayit['sha256']}")
    print(f"yazildi : {hedef}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
