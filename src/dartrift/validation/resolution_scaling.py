"""SPH'de çözülen ölçeği `h` mi belirliyor, parçacık aralığı `dx` mi?

**Neden bu ölçüm FAZ 4.2'nin kararını belirliyor**

Kod tabanının tamamında `h` **skalerdir**:

```
warp_core/solver.py:179        self.h = float(h)
warp_core/solver_solid.py:299  self.h = float(h)
cpu_reference/solid_ref.py:46  h: float
```

Yani A yaklaşımı (değişken kütle bölgeleri) bu kodda ancak **tek global `h`**
ile uygulanabilir — [`mass_ratio`][dartrift.validation.mass_ratio] modülünün
ölçtüğü şey tam olarak budur.

Eğer SPH'de çözülen ölçek `h` ise, bir bölgeye 8 kat parçacık koyup `h`'yi
kaba tutmak **çözünürlüğü artırmaz**. O zaman A, ADR-0026'nın sorununu (DART
mermisini çapı boyunca 6 parçacıkla çözmek) **çözemez**.

## Neden "tam çözüme göre hata" ölçütü kullanılmıyor

İlk tasarımım şuydu: *"olağan yakınsamada hata küçülmeli (boşluk kontrolü),
sabit `h`'de düzleşmeli."* **Bu tasarım hatalıydı ve ADR-0011'i okumadan
yazılmıştı.** ADR-0011 zaten ölçmüş ki bu kurulumda şok yarıçapı hatası
**%3,9'luk bir tabana** oturur ve sıfıra gitmez — sebebi ayrıklaştırma değil,
**model-form**: enerji noktasal değil, şok yarıçapının ~%32'si kadar bir
bölgeye konuyor; analitik çözüm ise nokta patlaması varsayar.

Dolayısıyla "hata küçülüyor mu" boş bir boşluk kontrolüdür — **küçülmeyeceği
biliniyordu.**

## Doğru ölçüt: öz-yakınsama ve **platonun yeri**

Her kol bir değere **oturur**. Soru hangi değere oturduğudur:

- `h/dx` sabit (yani `h → 0`): plato **0,2400** (ADR-0011, n = 96…112)
- `h = 0,0625` sabit: plato **0,2565** (n = 56…64, son adımda değişim %0,13)

**%6,85 uzakta.** Sabit `h`'de ne kadar parçacık eklenirse eklensin, `h → 0`
limitinin oturduğu yere **ulaşılamıyor**.

Kesin kanıt üçüncü koldadır: **başka bir sabit `h`** başka bir platoya
oturmalıdır. Oturuyorsa platonun yerini `h` belirliyor demektir.
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import RefParams
from .sedov import (GAMMA, H_OVER_DX, T_END_DEFAULT, build_sedov_ic,
                    measure_shock_radius, shock_radius_exact)

__all__ = ["run_single", "run_arm", "judge", "run_resolution_scaling"]


def run_single(n_side: int, h_absolute: float | None, device: str,
               t_end: float = T_END_DEFAULT) -> dict:
    """Tek bir Sedov koşusu. `h_absolute` None ise olağan `h = H_OVER_DX·dx`."""
    from ..warp_core.solver import WarpSPH3D

    ic = build_sedov_ic(n_side)
    h = float(h_absolute) if h_absolute is not None else float(ic["h"])
    solver = WarpSPH3D(ic["x"], ic["v"], ic["m"], ic["u"], h,
                       RefParams(gamma=GAMMA), device=device)
    diag = solver.run(t_end, max_steps=500_000)
    # Kismi kosu SESSIZCE gecerli sayilmaz (ADR-0011 §3): t_end'e ulasilmadan
    # olculen yaricap sistematik olarak KUCUK cikar ve tam da "cozunurlukle
    # kotulesen hata" gibi gorunur.
    if diag["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(
            f"Sedov t_end'e ULASILAMADI: {diag['t_end']:.6g} < {t_end:.6g} "
            f"({diag['n_steps']} adim). Olcum gecersiz.")
    st = solver.state_numpy()
    r_olc = measure_shock_radius(st["x"], st["rho"])
    return {"n_side": n_side, "N": int(len(ic["m"])), "dx": float(ic["dx"]),
            "h": h, "h_over_dx": h / float(ic["dx"]),
            "r_measured": float(r_olc),
            "r_exact": float(shock_radius_exact(t_end)),
            "n_steps": int(diag["n_steps"])}


def run_arm(sides: tuple[int, ...], h_absolute: float | None, device: str,
            t_end: float = T_END_DEFAULT) -> dict:
    """Bir kolu koştur ve **nereye oturduğunu** ölç.

    Plato, en ince iki çözünürlüğün ortalamasıdır; oturmuşluk ölçüsü son iki
    noktanın **göreli** farkıdır. Oturmamış bir kolun platosu anlamsızdır ve
    `settled` alanı bunu açıkça söyler — sessizce plato diye kullanılmaz.
    """
    if len(sides) < 3:
        raise ValueError(f"en az 3 çözünürlük gerekir, {len(sides)} geldi")
    if sorted(sides) != list(sides):
        raise ValueError(f"çözünürlükler artan olmalı: {sides}")
    satirlar = [run_single(n, h_absolute, device, t_end) for n in sides]
    r = np.array([d["r_measured"] for d in satirlar])
    son_degisim = float(abs(r[-1] - r[-2]) / abs(r[-2]))
    return {
        "rows": satirlar,
        "h_absolute": None if h_absolute is None else float(h_absolute),
        "plateau": float(np.mean(r[-2:])),
        "last_rel_change": son_degisim,
        "settled": bool(son_degisim < 0.005),
        "n_steps_max": int(max(d["n_steps"] for d in satirlar)),
    }


def judge(a: dict, b: dict, c: dict, h_coarse: float, h_fine: float,
          t_end: float = T_END_DEFAULT) -> dict:
    """Üç kolun platolarını yorumla — **saf fonksiyon**, GPU gerekmez.

    Yargı koşudan ayrıldı ki **her dalı** sınanabilsin: oturmamış bir kol
    `inconclusive` vermeli; platolar ayrışmıyorsa `dx` de katkı veriyor
    demektir.
    """
    fark_b = abs(b["plateau"] - a["plateau"]) / abs(a["plateau"])
    fark_c = abs(c["plateau"] - a["plateau"]) / abs(a["plateau"])
    kayiyor = abs(c["plateau"] - b["plateau"]) / abs(b["plateau"])

    hepsi_oturdu = bool(a["settled"] and b["settled"] and c["settled"])
    if not hepsi_oturdu:
        yargi = "inconclusive"
    elif kayiyor > 0.01 and fark_b > 0.01:
        # Sabit-h platosu h ile kayiyor ve h->0 limitinden uzak: `h` belirliyor.
        yargi = "h_sets_resolution"
    else:
        yargi = "dx_also_contributes"

    return {
        "standard": a, "fixed_h_coarse": b, "fixed_h_fine": c,
        "h_coarse": h_coarse, "h_fine": h_fine,
        "r_exact": float(shock_radius_exact(t_end)), "t_end": t_end,
        "all_settled": hepsi_oturdu,
        "gap_coarse_vs_limit": float(fark_b),
        "gap_fine_vs_limit": float(fark_c),
        "plateau_shifts_with_h": float(kayiyor),
        # Ince sabit-h platosu, kaba olandan limite DAHA YAKIN olmali:
        # `h` kuculdukce limite yaklasiliyorsa aciklama tutarlidir.
        "finer_h_is_closer": bool(fark_c < fark_b),
        "verdict": yargi,
    }


def run_resolution_scaling(
    standard_sides: tuple[int, ...] = (48, 64, 80, 96, 112),
    fixed_h_sides: tuple[int, ...] = (32, 40, 48, 56, 64),
    fixed_h_sides_2: tuple[int, ...] = (64, 72, 80, 88, 96),
    device: str = "cuda:0",
    t_end: float = T_END_DEFAULT,
) -> dict:
    """Üç kol: `h → 0`, `h` sabit (kaba), `h` sabit (ince).

    Yargı **platoların yerine** bakar, tam çözüme göre hataya değil
    (modül başlığındaki gerekçe).

    Boşluk kontrolü (ADR-0040): her üç kol da **oturmuş** olmalı. Oturmamış
    bir koldan plato okumak, olmayan bir yakınsamayı varsaymaktır.
    """
    h_kaba = H_OVER_DX / float(fixed_h_sides[0])
    h_ince = H_OVER_DX / float(fixed_h_sides_2[0])
    if not h_ince < h_kaba:
        raise ValueError(f"ikinci sabit h daha KÜÇÜK olmalı: {h_ince} !< {h_kaba}")

    a = run_arm(standard_sides, None, device, t_end)
    b = run_arm(fixed_h_sides, h_kaba, device, t_end)
    c = run_arm(fixed_h_sides_2, h_ince, device, t_end)

    return judge(a, b, c, h_kaba, h_ince, t_end)
