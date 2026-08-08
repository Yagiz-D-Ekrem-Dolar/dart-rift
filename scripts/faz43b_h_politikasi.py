"""FAZ 4.3b — `h` sabit mi kalmalı? (ADR-0041 madde 2 vs madde 4 çelişkisi)

İki adım:
  1) Gerçek bir koşuda `ρ`'nun (dolayısıyla `N_komşu`'nun) **salınımını** ölç
     — taramanın kapsaması gereken aralığı ölçümden öğren.
  2) `h` **sabit**, `dx` taranarak platonun komşu sayısıyla kayıp kaymadığını
     ölç. `h` sabit olduğu için çözülen ölçek sabittir; yayılım varsa
     suçlu komşu sayısıdır.
"""
from __future__ import annotations

import json
import sys

from pathlib import Path  # noqa: E402

# Depo koku __file__'DAN turetiliyor, sabit yazilmiyor: depo
# tasindiginda ya da baska bir kullaniciyla kosuldugunda sabit
# yol SESSIZCE yanlis src'yi bulur (ya da hic bulmaz).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# Cikti UTF-8'e sabitleniyor: baslıklarda `—` ve `A′` geciyor ve bir
# raporlama betiginin UnicodeEncodeError ile dusmesi raporu yok eder.
# SLURM isi PYTHONIOENCODING=utf-8 veriyor ama betik ELLE de kosulabilir.
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


from dartrift.validation.h_policy import (  # noqa: E402
    judge, measure_density_swing, n_sides_for_swing, run_fixed_h_sweep)

DEV = "cuda:0"


def main() -> int:
    print("=" * 78, flush=True)
    print("FAZ 4.3b — `h` POLITIKASI", flush=True)
    print("=" * 78, flush=True)

    print("\n[1] Gercek kosuda yogunluk salinimi (calisma noktasi)", flush=True)
    sal = measure_density_swing(64, DEV)
    for k in ("n_side", "h", "n_ic", "rho_ilk_ortanca", "rho_son_p01",
              "rho_son_p99", "rho_son_en_kucuk", "rho_son_en_buyuk",
              "N_komsu_ilk", "N_komsu_p01", "N_komsu_p99", "salinim_p99_p01"):
        print(f"    {k:22s} = {sal[k]}", flush=True)

    # Taramayi OLCULEN salinimi kapsayacak sekilde kur.
    # N_komsu ~ (2h/dx)^3 ve dx ~ 2/n  =>  N_komsu ~ (h*n)^3
    h_sabit = float(sal["h"])
    print(f"\n[2] h = {h_sabit:.6g} SABIT, dx taraniyor", flush=True)
    # `n` listesi OLCULEN salinimdan turetiliyor -- elle hesaplayip iki kez
    # yanildim: once kapsamadi (ust uc 524 < 551), sonra kapsadi ama
    # calisma araliginda tek nokta kaldi. Aritmetik artik kodda.
    n_listesi = n_sides_for_swing(sal, h_sabit)
    print(f"    n listesi (salinimdan turetildi) = {n_listesi}", flush=True)
    satirlar = run_fixed_h_sweep(h_sabit, n_listesi, DEV)
    print(f"    {'n':>4s} {'N':>8s} {'N_komsu':>10s} {'r_olc':>10s} "
          f"{'hata':>9s}", flush=True)
    for s in satirlar:
        print(f"    {s['n_side']:>4d} {s['N']:>8d} {s['N_komsu']:>10.2f} "
              f"{s['r_measured']:>10.6f} {s['hata']:>8.2%}", flush=True)

    print("\n[3] YARGI", flush=True)
    y = judge(satirlar, swing=sal)
    for k, v in y.items():
        print(f"    {k:22s} = {v}", flush=True)

    with open(REPO.parent / "faz43b_sonuc.json", "w") as f:
        json.dump({"salinim": sal, "tarama": satirlar, "yargi": y}, f, indent=2)
    print("\nyazildi: faz43b_sonuc.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
