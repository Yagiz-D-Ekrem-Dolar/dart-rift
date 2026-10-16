"""PROTOKOL-HS — Hera için mühürlü **spin** ön kaydını üretir.

Protokol (`docs/truba/PROTOKOL-HS-HERA-SPIN.md`) 2026-10-16'da, bu
betik yazılmadan ve hiçbir öngörü hesaplanmadan **önce** kilitlendi.
Burada hiçbir eşik, kantil ya da yargı **tanımlanmaz**; hepsi oradan
okunur.

Zincir:

1. 96 durum dosyasında `si_son_isleme.olc` → `ω` (PROTOKOL-SI §5'in
   tanımı, değiştirilmeden). Geçersiz/okunmaz koşu **sessiz
   atlanmaz**, sayılır ve kayda girer.
2. `θ` ↔ kilitli tasarım eşlemesi dosyanın kendi `theta`'sından.
3. `ω` için GP vekili (havuz `β`/`M_ejekta` vekilleriyle aynı aile).
4. §4.2: `θ` örnekleri **eleme bölgesinden** (`I ≤ 3`), bölge içinde
   **düzgün** — posterior ağırlığı kullanılmaz, çünkü §6 posteriorun
   daha dar olduğunu söylüyor ve dar olanı seçmek öngörüyü sahte
   biçimde keskinleştirirdi.
5. §4.3: `ω → f` eşlemesi — Hera bir `ΔL` verdiğinde `f` ne olur.
6. §5: `ONKAYIT_HERA_SPIN_<etiket>.json`, SHA-256'lı, **üzerine
   yazılmaz**.

σ notu: `ω` için **ölçülmüş bir `σ_model` yok** (`tarih_esleme`'deki
terimler `β` ve `M_ejekta` için). Öngörüye yalnız vekil öngörü
varyansı giriyor ve bu kayda açıkça yazılıyor — protokolün istediği
"ihmal edilmez" şartı, var olmayan bir terimi uydurmakla karşılanmaz.

Kullanım:

    python scripts/hera_spin_onkayit.py <havuz.csv> --kampanya <dizin> \\
        --etiket uretim96 --cikti docs/onkayit
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "src"))

from si_son_isleme import olc  # noqa: E402
from up_onsel_ve_tarih import _ortak, tarih_esleme  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.gp_vekil import gp_uydur  # noqa: E402

N_NOKTA, TOHUM_TASARIM = 96, 20260906

#: PROTOKOL-HS §4.4 — ongoru uretilmeden once secildi.
N_ORNEK, TOHUM_ONGORU = 20000, 20261016
KANTILLER = (0.05, 0.16, 0.50, 0.84, 0.95)


def _commit() -> str:
    """Betiğin kendi deposundaki HEAD. Bulunamazsa **durur**.

    Künyesiz bir ön kayıt mühür sayılmaz: PROTOKOL-HS §5 commit'i
    meta'nın parçası yapıyor ve commit tarihi zaman damgasının ikinci
    kanıtı. Çalışma dizininden bağımsız olsun diye betiğin kendi yolu
    kullanılıyor — ilk üretimde bu yüzden boş kalmıştı.
    """
    import subprocess
    kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        c = subprocess.run(["git", "-C", kok, "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise SystemExit(
            f"git commit okunamadi ({kok}): {e}. Kunyesiz on kayit "
            "uretilmez (PROTOKOL-HS §5).") from e
    return c.stdout.strip()


def omega_oku(kampanya: str) -> tuple[np.ndarray, np.ndarray, dict]:
    """Her durum dosyasında `ω`; kilitli tasarımla eşleştirilmiş."""
    tasarim = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA,
                                    root_seed=TOHUM_TASARIM), dtype=np.float64)
    bulunan: dict[int, float] = {}
    atlanan: list[dict] = []
    desen = os.path.join(kampanya, "HAVUZ_g1p0.dilim*_24.durumlar")
    for dizin in sorted(glob.glob(desen)):
        if not re.search(r"dilim(\d+)_24", dizin):
            raise ValueError(f"dilim okunamadi: {dizin}")
        for yol in sorted(glob.glob(os.path.join(dizin, "nokta_*.npz"))):
            s = olc(yol)
            th = np.asarray(s["theta"], dtype=np.float64).ravel()
            uz = np.max(np.abs(tasarim - th) /
                        np.maximum(np.abs(tasarim), 1e-30), axis=1)
            k = int(np.argmin(uz))
            if uz[k] > 1e-9:
                raise SystemExit(f"{os.path.basename(yol)}: theta kilitli "
                                 f"tasarimda yok (bagil {uz[k]:.2e})")
            if s.get("genel") != "OLCULDU" or "spin" not in s:
                atlanan.append({"idx": k, "sebep": s.get("genel", "?")})
                continue
            if k in bulunan:
                raise SystemExit(f"ayni tasarim noktasi iki kez: {k}")
            bulunan[k] = float(s["spin"]["omega"])

    tani = {"olculen": len(bulunan), "hedef": N_NOKTA, "atlanan": atlanan}
    if not bulunan:
        raise SystemExit("hicbir noktada omega olculemedi")
    idx = np.array(sorted(bulunan), dtype=int)
    return idx, np.array([bulunan[i] for i in idx], dtype=np.float64), tani


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("havuz", type=Path)
    ap.add_argument("--kampanya", required=True)
    ap.add_argument("--etiket", required=True)
    ap.add_argument("--cikti", type=Path, default=Path("docs/onkayit"))
    ap.add_argument("--n-grid", type=int, default=60)
    a = ap.parse_args(argv)

    a.cikti.mkdir(parents=True, exist_ok=True)
    hedef = a.cikti / f"ONKAYIT_HERA_SPIN_{a.etiket}.json"
    if hedef.exists():                      # §5: uzerine YAZILMAZ
        raise SystemExit(f"KAYIT ZATEN VAR: {hedef}. Ustune yazilmaz "
                         "(PROTOKOL-HS §5); yeni etiket secin.")

    # --- eleme bolgesi (§4.2) ---------------------------------------
    o = _ortak(a.havuz, a.n_grid)
    te = tarih_esleme(o)
    maske = te.pop("maske")
    te.pop("I")
    eksen = o["eksen"]
    U = np.column_stack([g.ravel() for g in
                         np.meshgrid(*([eksen] * 3), indexing="ij")])
    U_bagdasir = U[maske]
    if U_bagdasir.shape[0] < 100:
        raise SystemExit(f"bagdasir dugum {U_bagdasir.shape[0]} < 100; "
                         "ornekleme anlamsiz")

    # --- omega vekili ------------------------------------------------
    idx, omega, om_tani = omega_oku(a.kampanya)
    X = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA,
                              root_seed=TOHUM_TASARIM))[idx]
    if np.any(omega <= 0.0):
        raise SystemExit("omega <= 0 olan nokta var; log vekili kurulamaz")
    gp_w = gp_uydur(DART_UZAYI_S4, X, np.log(omega))

    # --- ongoru (§4.4) ------------------------------------------------
    rng = np.random.default_rng(TOHUM_ONGORU)
    sec = rng.integers(0, U_bagdasir.shape[0], size=N_ORNEK)
    u_orn = U_bagdasir[sec]
    mu, var = gp_w.predict_u(u_orn)
    log_w = mu + np.sqrt(var) * rng.standard_normal(N_ORNEK)
    w_orn = np.exp(log_w)
    f_orn = DART_UZAYI_S4.from_unit(u_orn)[:, 2]

    def kant(x):
        return {f"q{int(100*q):02d}": float(np.quantile(x, q))
                for q in KANTILLER}

    # --- omega -> f eslemesi (§4.3) ----------------------------------
    kenar = np.quantile(w_orn, np.linspace(0.0, 1.0, 7))
    eslem = []
    for i in range(len(kenar) - 1):
        m_ = (w_orn >= kenar[i]) & (w_orn <= kenar[i + 1])
        if int(m_.sum()) < 50:
            continue
        eslem.append({
            "omega_araligi": [float(kenar[i]), float(kenar[i + 1])],
            "n": int(m_.sum()),
            "f": kant(f_orn[m_]),
        })

    kayit = {
        "protokol": "PROTOKOL-HS-HERA-SPIN",
        "etiket": a.etiket,
        "uretildi_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _commit(),
        "havuz": str(a.havuz),
        "n_ornek": N_ORNEK,
        "tohum_ongoru": TOHUM_ONGORU,
        "kantiller": list(KANTILLER),
        "omega_olcumu": om_tani,
        "ornekleme": {
            "bolge": "tarih esleme I <= 3 (PROTOKOL-UP §6)",
            "agirlik": "bolge icinde DUZGUN; posterior agirligi KULLANILMADI",
            "bagdasir_dugum": int(maske.sum()),
            "toplam_dugum": int(maske.size),
            "V_bagdasir": float(np.mean(maske)),
        },
        "vekil_omega": {"ell": gp_w.ell.tolist(), "n_egitim": int(X.shape[0])},
        "ONGORU_omega_rad_s": kant(w_orn),
        "ONGORU_L_yok": ("|L| ayrica muhurlenmedi: omega = |L|/I ile birebir "
                         "bagli ve I theta'ya gore degisiyor; tek nicelik "
                         "muhurlemek daha az yorum gerektirir."),
        "omega_f_eslemesi": eslem,
        "sigma_notu": ("omega icin OLCULMUS bir sigma_model YOK "
                       "(tarih_esleme terimleri beta ve M_ejekta icin). "
                       "Ongoruye yalniz vekil ongoru varyansi girdi. "
                       "Var olmayan bir terim uydurulmadi."),
        "yanlislanma": ("Hera'nin olcecegi deger q05-q95 disinda -> "
                        "TUTARSIZ, icinde -> TUTARLI (PROTOKOL-HS §6). "
                        "Kantil yazilir."),
        "UYARI_kaydin_parcasi": [
            "ZAMAN OLCEGI: model omega'si t_end = 600 s'deki, yani "
            "carpmanin KATTIGI acisal momentum. Hera dort yil evrilmis "
            "bir durum olcecek (NPA sonumu, gelgit, yeniden birikme). "
            "Ikisi ayni nicelik DEGIL; dogrudan karsilastirma bir "
            "geri-yayma modeli ister ve o model bu depoda YOK.",
            "f ONSELDEN BASKIN (n_yon = 1, KAYIT-079). Ongoru genisligi "
            "buyuk olcude onselin genisligi. Dar cikmasi basari degil "
            "HATA isaretidir.",
            "TEK SABIT SAHNE; ongoru o sahneye kosullu.",
            "ADR-0059 cozunurluk acigi (sigma mi yanlilik mi) KAPANMADI; "
            "ince kosu yanlilik gosterirse bu kayit yeniden uretilmeli.",
        ],
    }

    govde = json.dumps(kayit, ensure_ascii=False, indent=1, sort_keys=True)
    kayit["sha256"] = hashlib.sha256(govde.encode("utf-8")).hexdigest()
    hedef.write_text(json.dumps(kayit, ensure_ascii=False, indent=1),
                     encoding="utf-8")

    print("=" * 70)
    print(f"PROTOKOL-HS — MUHURLU SPIN ON KAYDI  [{a.etiket}]")
    print("=" * 70)
    print(f"omega olculen nokta : {om_tani['olculen']}/{om_tani['hedef']}")
    if om_tani["atlanan"]:
        for s in om_tani["atlanan"]:
            print(f"   ATLANDI idx {s['idx']}: {s['sebep']}")
    print(f"bagdasir bolge      : %{100*np.mean(maske):.2f} "
          f"({int(maske.sum())}/{maske.size} dugum)")
    print(f"ornek               : {N_ORNEK}, tohum {TOHUM_ONGORU}")
    print()
    print("ONGORU  omega (rad/s):")
    for k, v in kayit["ONGORU_omega_rad_s"].items():
        print(f"   {k} = {v:.6e}")
    print()
    print("omega -> f eslemesi (Hera bir omega olcerse f ne olur):")
    for e in eslem:
        print(f"   omega {e['omega_araligi'][0]:.3e}..{e['omega_araligi'][1]:.3e}"
              f"  (n={e['n']:5d})  f: q05={e['f']['q05']:.3f} "
              f"q50={e['f']['q50']:.3f} q95={e['f']['q95']:.3f}")
    print()
    print(f"SHA-256 : {kayit['sha256']}")
    print(f"yazildi : {hedef}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
