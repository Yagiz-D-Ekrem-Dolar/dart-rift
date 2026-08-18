"""A17 — kaydedilmiş son durumdan **momentum anatomisi**.

`β`'nın neden düşük kaldığını ölçen tanı betiği. Üç soruyu ayırır ve
üçünü ayrı ayrı ölçer, çünkü tek bir `β` sayısı üçünü birbirine
karıştırıyor:

1. **Momentum var mı?** Gövdedeki dışarı giden maddenin *eksenel net*
   momentumu gerekenle karşılaştırılır.
2. **Yönlü mü?** Eş yönlü genleşme (çınlama) eksenel nete **sıfır**
   katkı yapar; `β`'ya yalnızca asimetrik koni katkı verir. Oran
   `|p_eksen| / p_radyal` bunu ayırır: `~0` çınlama, `~1` koni.
3. **Çıkıyor mu?** Üretim ölçütü `d > 2R` kontrol yüzeyine bakıyor.
   Madde yeterli momentumu taşısa bile oraya varmamışsa `β` düşük
   çıkar — ve bu **model hatası değil, süre yetersizliğidir**.

## Neden bu ayrım gerekliydi

`t_end` `0,2 → 100 s` yapıldığında `β` değişmedi ve bundan
*"süre sebep değil"* diye çıkarılmıştı. Yanlıştı: `2R`'ye varış süresi
bu betikle `~550 s` ölçüldü, yani `100 s` ölçütün **altında** kalıyor.
`β`'nın sabit kalması *"ejekta yok"* değil *"ejekta sayılmıyor"*
anlamına da gelebiliyordu ve iki durum ayrılmamıştı.

## Okuma uyarısı

`p_eksen` bant bant **işaret değiştiriyorsa** madde tutarlı bir tabaka
halinde değil, salınım halindedir; o durumda anlık `p_eksen` kaçacak
momentumun üst sınırı **değildir** — salınımın o fazdaki değeridir.
Betik bu yüzden bandı bandı basar, tek toplam vermez.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

G = 6.674e-11
# beta = 1 + |p_ejekta| / p_mermi ;  olculen periyot degisiminden
# beta = 3,2225 ve p_mermi = 3,5604e6 -> gereken p_ejekta:
GEREKEN_P_EJEKTA = 7.91e6
HIZ_BANTLARI = ((0.0, 0.1), (0.1, 0.5), (0.5, 2.0), (2.0, 10.0),
                (10.0, 100.0), (100.0, np.inf))
KABUKLAR = ((0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0), (1.0, 2.0))


def anatomi(yol: Path) -> dict:
    d = np.load(yol)
    x, v, m = d["x"], d["v"], d["m"]
    R, t = float(d["R"]), float(d["t"])
    r = np.linalg.norm(x, axis=1)
    yon = x / np.maximum(r, 1e-300)[:, None]
    vr = np.einsum("ij,ij->i", v, yon)
    p = m[:, None] * v

    p_top = p.sum(axis=0)
    eksen = int(np.argmax(np.abs(p_top)))
    v_kacis = float(np.sqrt(2.0 * G * float(m.sum()) / R))
    disa = vr > 0.0

    out: dict = {
        "dosya": yol.name, "t": t, "R": R, "N": int(len(m)),
        "kutle_toplam": float(m.sum()),
        "p_toplam_buyukluk": float(np.linalg.norm(p_top)),
        "baskin_eksen": "xyz"[eksen],
        "p_baskin_eksen": float(p_top[eksen]),
        "v_kacis": v_kacis,
        "n_disa": int(disa.sum()),
        "kutle_disa": float(m[disa].sum()),
        "p_radyal_disa": float((m[disa] * vr[disa]).sum()),
        "p_eksenel_disa": float(p[disa, eksen].sum()),
        "gereken_p_ejekta": GEREKEN_P_EJEKTA,
    }
    out["yonluluk"] = (abs(out["p_eksenel_disa"]) / out["p_radyal_disa"]
                       if out["p_radyal_disa"] > 0 else float("nan"))
    out["gereken_kat"] = abs(out["p_eksenel_disa"]) / GEREKEN_P_EJEKTA

    # --- kontrol yuzeyi sayimlari ------------------------------------
    out["n_r_ustu_R"] = int((r > R).sum())
    out["n_r_ustu_2R"] = int((r > 2.0 * R).sum())

    # --- varis suresi kestirimi (URETIM olcutu 2R) -------------------
    ic = disa & (r <= R) & (vr > 0.05)
    if ic.sum() >= 5:
        r_med, v_med = float(np.median(r[ic])), float(np.median(vr[ic]))
        out["ic_disa"] = {
            "n": int(ic.sum()), "r_medyan": r_med, "vr_medyan": v_med,
            "varis_R_s": (R - r_med) / v_med,
            "varis_2R_s": (2.0 * R - r_med) / v_med,
        }
        out["ic_disa"]["sure_yeterli_mi"] = t >= out["ic_disa"]["varis_2R_s"]

    # --- hiz bantlari (isaret donusu = salinim imzasi) ---------------
    bant = []
    for lo, hi in HIZ_BANTLARI:
        s = disa & (vr >= lo) & (vr < hi)
        bant.append({"lo": lo, "hi": None if hi == np.inf else hi,
                     "n": int(s.sum()),
                     "kutle": float(m[s].sum()) if s.any() else 0.0,
                     "p_eksen": float(p[s, eksen].sum()) if s.any() else 0.0})
    out["hiz_bantlari"] = bant
    isaretler = [np.sign(b["p_eksen"]) for b in bant if b["n"] > 0]
    out["isaret_donusu"] = int(sum(
        1 for a, b in zip(isaretler, isaretler[1:], strict=False) if a != b and a and b))

    # --- MERMI / HEDEF AYRISTIRMASI ----------------------------------
    # A17'nin kilidi: `beta`nin payi mermi geri sekmesi mi, hedef
    # ejektasi mi? Kimlik `mermi_kesri` ile tasiniyor (yoksa eski
    # dosya; alan atlanir ve bu ACIKCA yazilir).
    if "mermi_kesri" in d.files:
        f = np.asarray(d["mermi_kesri"], dtype=np.float64)
        kac2R = r > 2.0 * R
        m_mermi = m * f
        m_hedef = m * (1.0 - f)
        out["ayristirma"] = {
            "var": True,
            "mermi_kutlesi_toplam": float(m_mermi.sum()),
            "mermi_kutlesi_kacan": float(m_mermi[kac2R].sum()),
            "hedef_kutlesi_kacan": float(m_hedef[kac2R].sum()),
            "n_kacan": int(kac2R.sum()),
            # Eksenel momentum KUTLE PAYLARINA gore bolunuyor: bir
            # karisim parcaciginin momentumu tek bir tarafa yazilamaz.
            "p_eksen_mermi": float((m_mermi[kac2R] * v[kac2R, eksen]).sum()),
            "p_eksen_hedef": float((m_hedef[kac2R] * v[kac2R, eksen]).sum()),
        }
        ay = out["ayristirma"]
        top = abs(ay["p_eksen_mermi"]) + abs(ay["p_eksen_hedef"])
        ay["hedef_payi"] = (abs(ay["p_eksen_hedef"]) / top if top > 0
                            else float("nan"))
        ay["beta_mermiden"] = 1.0 + abs(ay["p_eksen_mermi"]) / 3.5604e6
        ay["beta_hedeften"] = abs(ay["p_eksen_hedef"]) / 3.5604e6
    else:
        out["ayristirma"] = {
            "var": False,
            "neden": ("dosyada `mermi_kesri` yok -- kimligin tasinmasindan "
                      "ONCE kaydedilmis durum; ayristirma YAPILAMAZ"),
        }

    # --- kabuklar ----------------------------------------------------
    kab = []
    for lo, hi in KABUKLAR:
        s = disa & (r >= lo * R) & (r < hi * R)
        if s.sum() < 5:
            continue
        pr = float((m[s] * vr[s]).sum())
        pa = float(p[s, eksen].sum())
        kab.append({"lo": lo, "hi": hi, "n": int(s.sum()),
                    "p_radyal": pr, "p_eksen": pa,
                    "yonluluk": abs(pa) / pr if pr > 0 else float("nan")})
    out["kabuklar"] = kab
    return out


def bas(a: dict) -> None:
    print("=" * 74, flush=True)
    print(f"A17 MOMENTUM ANATOMISI — {a['dosya']}  (t = {a['t']:.1f} s)",
          flush=True)
    print("=" * 74, flush=True)
    print(f"\nN = {a['N']}   kutle = {a['kutle_toplam']:.4e} kg   "
          f"R = {a['R']:.2f} m   v_kacis = {a['v_kacis']:.4f} m/s", flush=True)
    print(f"KORUNUM: |p_toplam| = {a['p_toplam_buyukluk']:.4e}  "
          f"(eksen {a['baskin_eksen']}: {a['p_baskin_eksen']:+.4e})",
          flush=True)

    print("\n[1] MOMENTUM VAR MI", flush=True)
    print(f"    disari giden: {a['n_disa']} parcacik, "
          f"{a['kutle_disa']:.4e} kg", flush=True)
    print(f"    p_eksenel net = {a['p_eksenel_disa']:+.4e}   "
          f"gereken = {a['gereken_p_ejekta']:.4e}   "
          f"-> {a['gereken_kat']:.3f} kat", flush=True)

    print("\n[2] YONLU MU  (|p_eksen|/p_radyal; ~0 cinlama, ~1 koni)",
          flush=True)
    print(f"    genel yonluluk = {a['yonluluk']:.5f}", flush=True)
    for k in a["kabuklar"]:
        print(f"      r/R {k['lo']:4.2f}-{k['hi']:4.2f}  n={k['n']:5d}  "
              f"p_rad={k['p_radyal']:+.3e}  p_eks={k['p_eksen']:+.3e}  "
              f"yonluluk={k['yonluluk']:7.4f}", flush=True)

    print("\n[3] CIKIYOR MU  (uretim olcutu d > 2R)", flush=True)
    print(f"    r > R : {a['n_r_ustu_R']:5d}      "
          f"r > 2R: {a['n_r_ustu_2R']:5d}", flush=True)
    if "ic_disa" in a:
        g = a["ic_disa"]
        print(f"    ic disa giden: {g['n']} parcacik, "
              f"r_medyan={g['r_medyan']:.2f} m, "
              f"v_r medyan={g['vr_medyan']:.4f} m/s", flush=True)
        print(f"    varis R  ~ {g['varis_R_s']:8.1f} s", flush=True)
        print(f"    varis 2R ~ {g['varis_2R_s']:8.1f} s   <-- OLCUT",
              flush=True)
        yeter = "YETERLI" if g["sure_yeterli_mi"] else "YETERSIZ"
        print(f"    kosulan {a['t']:.0f} s  ->  SURE {yeter}", flush=True)

    ay = a.get("ayristirma", {"var": False, "neden": "alan yok"})
    print("\n[3b] MERMI mi HEDEF mi  (beta'nin PAYI kimin)", flush=True)
    if not ay.get("var"):
        print(f"     YAPILAMADI: {ay.get('neden')}", flush=True)
    else:
        print(f"     kacan {ay['n_kacan']} parcacik icinde:", flush=True)
        print(f"       mermi kutlesi = {ay['mermi_kutlesi_kacan']:12.4e} kg "
              f"(sahnedeki toplam {ay['mermi_kutlesi_toplam']:.4e})",
              flush=True)
        print(f"       hedef kutlesi = {ay['hedef_kutlesi_kacan']:12.4e} kg",
              flush=True)
        print(f"       p_eksen mermi = {ay['p_eksen_mermi']:+12.4e}",
              flush=True)
        print(f"       p_eksen hedef = {ay['p_eksen_hedef']:+12.4e}",
              flush=True)
        print(f"       hedef payi    = {ay['hedef_payi']:.4f}", flush=True)
        print(f"       beta (yalniz mermiden)  = "
              f"{ay['beta_mermiden']:.4f}", flush=True)
        print(f"       beta katkisi (hedeften) = "
              f"{ay['beta_hedeften']:.4f}", flush=True)
        if ay["hedef_payi"] < 0.1:
            print("     -> beta bir HEDEF EJEKTASI olcumu DEGIL, "
                  "MERMI GERI SEKME olcumu", flush=True)

    print("\n[4] HIZ BANTLARI  (isaret donusu = salinim imzasi)", flush=True)
    print(f"    {'v_r araligi':>17s} {'n':>6s} {'kutle kg':>12s} "
          f"{'p_eksen':>12s}", flush=True)
    for b in a["hiz_bantlari"]:
        hi = "inf" if b["hi"] is None else f"{b['hi']:.0f}"
        print(f"    {b['lo']:8.1f}-{hi:<8s} {b['n']:6d} "
              f"{b['kutle']:12.3e} {b['p_eksen']:+12.3e}", flush=True)
    print(f"    isaret donusu sayisi = {a['isaret_donusu']}", flush=True)
    if a["isaret_donusu"] >= 2:
        print("    -> SALINIM: anlik p_eksen kacacak momentumun ust siniri "
              "DEGIL", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("durumlar", nargs="+")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    hepsi = []
    for y in a.durumlar:
        d = anatomi(Path(y))
        bas(d)
        hepsi.append(d)
        print("", flush=True)
    if a.out:
        Path(a.out).write_text(json.dumps(hepsi, indent=2, default=float),
                               encoding="utf-8")
        print(f"yazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    for _a in (sys.stdout, sys.stderr):
        try:
            _a.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
