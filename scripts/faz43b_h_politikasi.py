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

sys.path.insert(0, "/arf/scratch/egitimg16/driftclaude/dart-rift/src")

from dartrift.validation.h_policy import (  # noqa: E402
    judge, measure_density_swing, run_fixed_h_sweep)

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
    # Taramanin OLCULEN salinimi (268 -> 551) KAPSAMASI gerekiyor.
    # Nominal kurulumda h/dx = 2 sabittir, yani calisma noktasi her n'de
    # N_komsu = (4/3)pi(2*2)^3 = 268. Ust ucu 551'e tasimak icin
    # h/dx >= (551*3/4pi)^(1/3)/2 = 2.543  =>  n >= 64*1.27 = 81.4.
    # Ilk kosuda ust uc n=80'de 524'te kaldi ve judge() dogru bicimde
    # "belirsiz" dondu. n=84 ile kapaniyor.
    n_listesi = [40, 48, 56, 64, 72, 84]
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

    with open("/arf/scratch/egitimg16/driftclaude/faz43b_sonuc.json", "w") as f:
        json.dump({"salinim": sal, "tarama": satirlar, "yargi": y}, f, indent=2)
    print("\nyazildi: faz43b_sonuc.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
