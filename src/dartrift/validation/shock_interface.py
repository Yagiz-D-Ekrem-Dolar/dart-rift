"""E3 — arayüzden **şok** geçerken ne oluyor?

KAYIT-020/022/024'teki her ölçüm **yumuşak** bir basınç alanında yapıldı.
Çarpma probleminin asıl sorusu ise arayüzden geçen **şoktur**.

## Tasarım — üç kol, **aynı** global `h`

KAYIT-023 ölçtü ki sabit `h`'de sonuç bir platoya oturur ve plato `h` ile
belirlenir. Öyleyse `h`'yi sabit tutup yalnızca **parçacık dağılımını**
değiştirirsek, üç kol da **aynı** cevabı vermelidir — arayüz zararsızsa.

| kol | dağılım | beklenen |
|---|---|---|
| **a** | tek popülasyon, **kaba** | `dx` kaba → platonun kaba ucu |
| **b** | **iki bölgeli** (içi ince, dışı kaba) | zararsızsa **a ile c arasında** |
| **c** | tek popülasyon, **ince** | `dx` ince → platonun ince ucu |

Ölçülen büyüklük Sedov şok yarıçapıdır ve **tam analitik** referansı vardır
(ama ADR-0011: bu kurulumda ~%3,9 model-form tabanı var, o yüzden kollar
birbirleriyle kıyaslanır, tam değerle değil).

**Boşluk kontrolü (ADR-0040):** `a` ile `c` **birbirinden farklı** olmalı.
Aynıysa sınav hiçbir şey ayırt edemez ve `b`'nin "aralarında" olması boş bir
doğrudur. (KAYIT-023 kol B ölçtü: sabit `h`'de `dx` değişimi yarıçapı
`0,25278 → 0,25650`, yani **%1,5** oynatıyor — sınav ayırt ediyor.)

## Enerji enjeksiyonu

`build_sedov_ic` enerjiyi **kütle ağırlıklı** dağıtır (`u += E·w/Σmw`) ve
enjeksiyon ölçeği **sabit fiziksel uzunluktur** (ADR-0011). Bu, karışık
çözünürlükte de aynı fiziksel başlangıç koşulunu verir — ama doğrulanır:
her kolun toplam enjekte enerjisi yazdırılır.
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import RefParams
from .sedov import (E_INJECT, GAMMA, H_INJECT, H_OVER_DX, RHO0, T_END_DEFAULT,
                    U_BACKGROUND, measure_shock_radius, shock_radius_exact)

__all__ = ["build_two_zone_sedov_ic", "run_shock_interface"]


def _lattice(n_side: int, lo: float = -0.5, hi: float = 0.5) -> tuple:
    dx = (hi - lo) / n_side
    eksen = (np.arange(n_side) + 0.5) * dx + lo
    xx, yy, zz = np.meshgrid(eksen, eksen, eksen, indexing="ij")
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()]), dx


def build_two_zone_sedov_ic(n_coarse: int, lam: int, r_inner: float,
                            h_absolute: float,
                            h_inject: float = H_INJECT) -> dict:
    """`r < r_inner` içinde `lam` kat ince, dışında kaba kafes.

    Kütle **yerel** hücre hacminden gelir (`m = ρ₀·dx³`) — ADR-0030'un
    değişmezi. `lam = 1` verilirse sonuç tek popülasyondur ve
    `build_sedov_ic` ile **aynı** kafestir (boşluk kontrolü buna dayanır).
    """
    if lam < 1 or int(lam) != lam:
        raise ValueError(f"lam pozitif TAM sayı olmalı, {lam} geldi")
    lam = int(lam)
    if not (0.0 < r_inner < 0.5):
        raise ValueError(f"r_inner (0, 0.5) aralığında olmalı, {r_inner} geldi")

    x_k, dx_k = _lattice(n_coarse)
    r_k = np.linalg.norm(x_k, axis=1)
    dis = r_k >= r_inner

    if lam == 1:
        x = x_k
        m = np.full(len(x), RHO0 * dx_k ** 3)
    else:
        x_i, dx_i = _lattice(n_coarse * lam)
        r_i = np.linalg.norm(x_i, axis=1)
        ic = r_i < r_inner
        x = np.concatenate([x_i[ic], x_k[dis]])
        m = np.concatenate([np.full(int(ic.sum()), RHO0 * dx_i ** 3),
                            np.full(int(dis.sum()), RHO0 * dx_k ** 3)])
        if ic.sum() == 0 or dis.sum() == 0:
            raise ValueError(
                f"bölgelerden biri boş: ince={int(ic.sum())}, kaba={int(dis.sum())}")

    n = len(m)
    u = np.full(n, U_BACKGROUND)
    r = np.linalg.norm(x, axis=1)
    q = r / h_inject
    t = np.maximum(1.0 - 0.5 * q, 0.0)
    w = np.where(q < 2.0, t ** 4 * (2.0 * q + 1.0), 0.0)
    wsum = float(np.sum(m * w))
    if wsum <= 0.0:
        raise ValueError(f"enjeksiyon bölgesi boş: h_inject={h_inject}")
    u += E_INJECT * w / wsum
    # DOGRULAMA: enjekte edilen enerji her kolda AYNI olmali.
    e_enjekte = float(np.sum(m * (u - U_BACKGROUND)))
    # Iki bolgeli kolda toplam kutle TAM 1 olmaz: kure siniri (`r_inner`) iki
    # ayri kafesle ayriklastirildigi icin hucreler mukemmel dosemez. Olculdu
    # (n=16): %0,098 fazla; n buyudukce kucultur. Sedov'da r ~ (E/rho)^(1/5)
    # oldugu icin yaricaba etkisi BESTE BIRIDIR (~%0,02) — ama SUSULMAZ.
    return {"x": x, "v": np.zeros_like(x), "m": m, "u": u,
            "total_mass": float(np.sum(m)),
            "h": float(h_absolute), "dx_coarse": dx_k,
            "n_injected": int(np.count_nonzero(w > 0.0)),
            "energy_injected": e_enjekte,
            "mass_ratio": float(lam ** 3), "r_inner": float(r_inner)}


def _run(ic: dict, device: str, t_end: float) -> dict:
    from ..warp_core.solver import WarpSPH3D

    solver = WarpSPH3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"],
                       RefParams(gamma=GAMMA), device=device)
    diag = solver.run(t_end, max_steps=500_000)
    if diag["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(
            f"t_end'e ULASILAMADI: {diag['t_end']:.6g} < {t_end:.6g}. Ölçüm geçersiz.")
    st = solver.state_numpy()
    return {"N": int(len(ic["m"])), "h": ic["h"],
            "total_mass": ic["total_mass"],
            "energy_injected": ic["energy_injected"],
            "n_injected": ic["n_injected"],
            "r_measured": float(measure_shock_radius(st["x"], st["rho"])),
            "n_steps": int(diag["n_steps"])}


def run_shock_interface(n_coarse: int = 64, lam: int = 2,
                        r_inner: float = 0.15, device: str = "cuda:0",
                        t_end: float = T_END_DEFAULT) -> dict:
    """Üç kolu **aynı** `h` ile koştur ve arayüzün bedelini oku."""
    h = H_OVER_DX / float(n_coarse)          # KABA kafesin h'si, uc kolda AYNI

    a = _run(build_two_zone_sedov_ic(n_coarse, 1, r_inner, h), device, t_end)
    b = _run(build_two_zone_sedov_ic(n_coarse, lam, r_inner, h), device, t_end)
    c = _run(build_two_zone_sedov_ic(n_coarse * lam, 1, r_inner, h), device, t_end)

    lo, hi = min(a["r_measured"], c["r_measured"]), max(a["r_measured"],
                                                       c["r_measured"])
    aralik = hi - lo
    # BOSLUK KONTROLU: a ile c AYIRT EDILEBILIR olmali.
    ayirt_ediyor = bool(aralik / max(abs(lo), 1e-300) > 2.0e-3)
    icinde = bool(lo - 0.1 * aralik <= b["r_measured"] <= hi + 0.1 * aralik)
    # Enjekte enerji uc kolda ayni mi? Degilse farkli PROBLEM cozulmus olur.
    e = [k["energy_injected"] for k in (a, b, c)]
    enerji_ayni = bool((max(e) - min(e)) / max(e) < 1.0e-3)
    # Kutle uyumsuzlugu: `r ~ (E/rho)^(1/5)` -> yaricaba etkisi BESTE BIRI.
    kutle = [k["total_mass"] for k in (a, b, c)]
    kutle_sapmasi = float((max(kutle) - min(kutle)) / max(kutle))
    yaricap_etkisi = kutle_sapmasi / 5.0
    # Bu etki, olculmek istenen ARALIKTAN kucuk olmali; degilse sinyal
    # kutle artiginin icinde kaybolur.
    kutle_ihmal_edilebilir = bool(yaricap_etkisi < 0.2 * aralik / abs(lo))

    if not ayirt_ediyor or not enerji_ayni or not kutle_ihmal_edilebilir:
        yargi = "inconclusive"
    elif icinde:
        yargi = "interface_harmless"
    else:
        yargi = "interface_costs"

    return {
        "uniform_coarse": a, "two_zone": b, "uniform_fine": c,
        "lam": int(lam), "mass_ratio": float(lam ** 3), "r_inner": r_inner,
        "h": h, "t_end": t_end, "r_exact": float(shock_radius_exact(t_end)),
        "bracket": [lo, hi], "bracket_width_rel": float(aralik / abs(lo)),
        "arms_distinguishable": ayirt_ediyor,
        "energy_injection_matches": enerji_ayni,
        "mass_mismatch_rel": kutle_sapmasi,
        "mass_effect_on_radius_rel": yaricap_etkisi,
        "mass_effect_negligible": kutle_ihmal_edilebilir,
        "two_zone_within_bracket": icinde,
        # Arayuzun bedeli: b, [a,c] aralinin DISINA ne kadar tasti?
        "excess_rel": float(max(0.0, lo - b["r_measured"],
                                b["r_measured"] - hi) / abs(lo)),
        "verdict": yargi,
    }
