"""FAZ 4.4 — ADR-0041 §5 **boşluk 3**: A′ mukavemetli malzemede de duruyor mu?

Üç aşama:
  1) `t_end` **ölçülerek** seçilir (S4'ün dersi: zaman ölçeği tahmin edilmez).
  2) Üç kol koşulur: tekdüze kaba / iki bölgeli **A′** / tekdüze ince.
  3) Kontrol kolu: aynı geometri ama **tek `h`** — A′'nın katkısını yalıtır.

Yargı KAYIT-026'nınkiyle **aynı** ölçüttür (parantez), böylece ideal gaz
sonucuyla doğrudan karşılaştırılabilir.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "/arf/scratch/egitimg16/driftclaude/dart-rift/src")

from dartrift.validation.solid_interface import (  # noqa: E402
    BASALT_SOLID, _malzeme, run_solid_interface)

DEV = "cuda:0"
N_KABA = 32
R_IC = 0.15


def _yaz(y: dict) -> None:
    print(f"    yargi                    = {y['yargi']}", flush=True)
    print(f"    parantez                 = [{y['parantez'][0]:.6f}, "
          f"{y['parantez'][1]:.6f}]  (genislik {y['parantez_genisligi_rel']:.3%})",
          flush=True)
    print(f"    iki bolgeli r            = {y['iki_bolgeli']['r_measured']:.6f}",
          flush=True)
    print(f"    TASMA                    = {y['tasma_rel']:.4%}", flush=True)
    print(f"    esik yargilari           = {y.get('esik_yargilari')}", flush=True)
    print(f"    kollar ayirt edilebilir  = {y['kollar_ayirt_edilebilir']}",
          flush=True)
    print(f"    enerji esit              = {y['enerji_esit']}", flush=True)
    print(f"    kutle ihmal edilebilir   = {y['kutle_ihmal_edilebilir']} "
          f"(sapma {y['kutle_sapmasi_rel']:.4%})", flush=True)
    for ad in ("tekduze_kaba", "iki_bolgeli", "tekduze_ince"):
        k = y[ad]
        print(f"      {ad:14s} N={k['N']:7d}  r={k['r_measured']:.6f}  "
              f"rho_max={k['rho_max']:.1f}  adim={k['n_steps']}", flush=True)


def main() -> int:
    print("=" * 78, flush=True)
    print("FAZ 4.4 — ADR-0041 §5 BOSLUK 3 (mukavemetli malzemede A')", flush=True)
    print("=" * 78, flush=True)

    # t_end SONDADAN (job 1460685) okundu -- tahmin degil, olcum:
    #        t (s)   v_max   r@0.01   r@0.02   r@0.05
    #     2.000e-05   34.24   0.2738   0.2476   0.2137
    #     5.000e-05   26.65   0.4383   0.2808   0.2270
    #     1.000e-04   18.53   0.6130   0.4622   0.2138
    #     4.000e-04    0.93   0.8390   0.8390   0.8390   <- kutu doldu
    # Kullanilabilir pencere t = 2e-5..5e-5: cephe r_inner=0.15'i GECMIS
    # ama kutu yuzunden (0.5) uzak. t=3e-5 secildi.
    t_end = 3.0e-5
    print(f"\n[1] t_end = {t_end:.3e} (sonda job 1460685'ten okundu)", flush=True)

    sonuclar = {}

    print("\n[2] ANA KOL — Tillotson + mukavemet + gozeneklilik + hasar, A' (h_i)",
          flush=True)
    y = run_solid_interface(N_KABA, 2, R_IC, DEV, t_end, BASALT_SOLID,
                            per_particle_h=True, etiket="basalt-tam-Aprime")
    _yaz(y)
    sonuclar["basalt_tam_Aprime"] = y

    print("\n[3] KONTROL — ayni geometri, TEK h (A' yok)", flush=True)
    y2 = run_solid_interface(N_KABA, 2, R_IC, DEV, t_end, BASALT_SOLID,
                             per_particle_h=False, etiket="basalt-tam-tek-h")
    _yaz(y2)
    sonuclar["basalt_tam_tek_h"] = y2

    print("\n[4] AYRISTIRMA — hangi modul etkiliyor", flush=True)
    for ad, mat in (("yalniz-EOS", _malzeme(False, False, False)),
                    ("mukavemet", _malzeme(True, False, False)),
                    ("muk+gozenek", _malzeme(True, True, False))):
        print(f"  -- {ad}", flush=True)
        yk = run_solid_interface(N_KABA, 2, R_IC, DEV, t_end, mat,
                                 per_particle_h=True, etiket=ad)
        _yaz(yk)
        sonuclar[ad] = yk

    with open("/arf/scratch/egitimg16/driftclaude/faz44_sonuc.json", "w") as f:
        json.dump({"t_end": t_end, "sonuclar": sonuclar}, f, indent=2)
    print("\nyazildi: faz44_sonuc.json", flush=True)

    print("\n[5] OZET", flush=True)
    for ad, y in sonuclar.items():
        print(f"    {ad:22s} yargi={y['yargi']:18s} tasma={y['tasma_rel']:.4%}",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
