"""D-2 — biriktirme yarıçapı **kalibre edilebilir mi**?

## Neden

[KAYIT-029](../../../docs/defter/KAYIT-029_2026-08-04_D1b-duzeltme-kaynak-terimi-duyarli.md)
ölçtü: kaynak teriminin model-form hatası DART bandında **%5–7** ve
biriktirme yarıçapı **serbest bir parametredir**. ADR-0041 bu yüzden
kilitlenmedi.

Serbest bir parametre, **kalibre edilebiliyorsa** kusur olmaktan çıkar. Soru:

> Gerçek mermiyi temsil eden `r_dep` **hesaplanabilir** mi, yoksa her
> kuruluma göre elle mi ayarlanmalı?

## Kalibrasyonun temiz biçimi

Gerçek mermi enerjisini **toplu hareket** (kinetik) olarak taşır ve şokta
ısıya çevirir. Kaynak terimi ise enerjiyi doğrudan **ısı** olarak koyar.
İkisi arasındaki eşleme aranıyor.

Küresel simetriyi bozmadan bunu kuran düzenek: **piston**. `r < R` içindeki
parçacıklara dışa doğru radyal hız verilir; toplam kinetik enerji
`E_INJECT`'e eşitlenir. Bu, "enerjiyi hareket olarak taşıyan sonlu bir
cisim"dir — merminin küresel simetrik karşılığı.

```
piston(R)      :  KE = E_INJECT,  u = arka plan     -> sok yaricapi r_p(R)
biriktirme(r_d):  u  = E_INJECT,  v = 0             -> sok yaricapi r_b(r_d)
```

Kalibrasyon: her `R` için `r_p(R) = r_b(r_d)` sağlayan `r_d`'yi bul.
**`r_d/R` sabitse** kalibrasyon **taşınabilirdir** ve DART'a götürülebilir;
değilse her kurulum için ayrı ölçüm gerekir.

## Boşluk kontrolü (ADR-0040)

1. Piston kolu `R` ile **gerçekten değişmeli**. Değişmiyorsa eşleme
   anlamsızdır (her `r_d` uyar).
2. Piston ile biriktirme kollarının şok yarıçapı aralıkları **örtüşmeli**;
   örtüşmüyorsa kalibrasyon **ekstrapolasyondur** ve öyle işaretlenir.
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import RefParams
from .sedov import (E_INJECT, GAMMA, H_OVER_DX, RHO0, T_END_DEFAULT,
                    U_BACKGROUND, measure_shock_radius, shock_radius_exact)

__all__ = ["build_piston_ic", "run_calibration"]


def build_piston_ic(n_side: int, r_piston: float) -> dict:
    """`r < r_piston` içindeki parçacıklara **dışa radyal** hız ver.

    Toplam kinetik enerji `E_INJECT`'e eşitlenir — biriktirme koluyla
    **aynı enerji**, farklı **biçim**. Hız profili `v ∝ r` (homolog
    genişleme): tek bir kabuk değil, gerçek bir cismin patlama sonrası
    hız alanına daha yakın.
    """
    if not (0.0 < r_piston < 0.5):
        raise ValueError(f"r_piston (0, 0.5) arasında olmalı, {r_piston} geldi")
    dx = 1.0 / n_side
    eksen = (np.arange(n_side) + 0.5) * dx - 0.5
    xx, yy, zz = np.meshgrid(eksen, eksen, eksen, indexing="ij")
    x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    n = len(x)
    m = np.full(n, RHO0 * dx ** 3)
    r = np.linalg.norm(x, axis=1)

    ic = r < r_piston
    n_ic = int(ic.sum())
    if n_ic < 20:
        raise ValueError(
            f"piston bölgesi çok küçük ({n_ic} parçacık); r_piston={r_piston}, "
            f"dx={dx:.5f}")
    # KAYIT-029'UN DERSI: 20 esigi COK GEVSEK. Orada 32 ve 56 parcacikli
    # enjeksiyon bolgeleri hala ORNEKLEME hatasi tasiyordu ve "duyarsiz"
    # yargisini uretmisti. Ayni tuzagi burada tekrarlamamak icin ayri bir
    # bayrak: `piston_well_sampled` (>= 100) ve cagiran taraf ONA bakar.

    v = np.zeros_like(x)
    # Homolog: v = c * x  ->  KE = 0.5 * c^2 * sum(m r^2) = E_INJECT
    s2 = float(np.sum(m[ic] * r[ic] ** 2))
    if s2 <= 0.0:
        raise ValueError("piston bölgesi merkezde yığılmış; r^2 toplamı sıfır")
    c = float(np.sqrt(2.0 * E_INJECT / s2))
    v[ic] = c * x[ic]

    u = np.full(n, U_BACKGROUND)
    ke = 0.5 * float(np.sum(m * np.sum(v * v, axis=1)))
    return {"x": x, "v": v, "m": m, "u": u, "h": H_OVER_DX * dx, "dx": dx,
            "r_piston": float(r_piston), "n_piston": n_ic,
            "kinetic_energy": ke,
            "piston_well_sampled": bool(n_ic >= 100),
            # DOGRULAMA: enerji biriktirme koluyla AYNI olmali.
            "energy_matches": bool(abs(ke - E_INJECT) < 1.0e-9 * E_INJECT)}


def _kostur(ic: dict, device: str, t_end: float) -> dict:
    from ..warp_core.solver import WarpSPH3D

    solver = WarpSPH3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"],
                       RefParams(gamma=GAMMA), device=device)
    diag = solver.run(t_end, max_steps=500_000)
    if diag["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(f"t_end'e ULASILAMADI: {diag['t_end']:.6g}")
    st = solver.state_numpy()
    ke = 0.5 * float(np.sum(st["m"] * np.sum(st["v"] * st["v"], axis=1)))
    return {"r_measured": float(measure_shock_radius(st["x"], st["rho"])),
            "kinetic_fraction": ke / E_INJECT,
            "n_steps": int(diag["n_steps"])}


def calibrate(piston_rows: list[dict], deposit_rows: list[dict]) -> dict:
    """Her piston yarıçapı için eşdeğer biriktirme yarıçapını bul.

    **Saf fonksiyon** — GPU gerekmez, ayrıca sınanabilir.
    """
    if len(piston_rows) < 2 or len(deposit_rows) < 3:
        raise ValueError(
            f"en az 2 piston ve 3 biriktirme noktası gerekir; "
            f"{len(piston_rows)}, {len(deposit_rows)} geldi")
    rd = np.array([d["r_deposit"] for d in deposit_rows], dtype=np.float64)
    rb = np.array([d["r_measured"] for d in deposit_rows], dtype=np.float64)
    sira = np.argsort(rb)
    rd, rb = rd[sira], rb[sira]

    # BOSLUK KONTROLU 1: biriktirme kolu gercekten AYIRT EDIYOR mu?
    ayirt = bool(rb.max() - rb.min() > 1.0e-3)

    # Biriktirme kolunun KE/E'si de (varsa) ara degerlenir: tek parametreli
    # kalibrasyonun IKI gozlenebiliri ayni anda esleyip eslemedigi sorusu.
    kf = None
    if all("kinetic_fraction" in d for d in deposit_rows):
        kf = np.array([d["kinetic_fraction"] for d in deposit_rows],
                      dtype=np.float64)[sira]

    satirlar = []
    for p in piston_rows:
        rp = float(p["r_measured"])
        icinde = bool(rb.min() <= rp <= rb.max())
        # `np.interp` aralik disinda UC DEGERE KELEPCELER. O sayi bir olcum
        # DEGILDIR; oran olarak raporlanirsa yanlis bir "eslesme" gorunur
        # (olculdu: R=0.050 ve 0.070 icin ikisi de 0.0800'e kelepcelendi ve
        # 1.60 / 1.14 gibi UYDURMA oranlar uretti). Aralik disinda NaN.
        r_esdeger = float(np.interp(rp, rb, rd)) if icinde else float("nan")
        satir = {
            "r_piston": float(p["r_piston"]),
            "r_shock_piston": rp,
            "r_deposit_equivalent": r_esdeger,
            "ratio": (r_esdeger / float(p["r_piston"]) if icinde
                      else float("nan")),
            "in_bracket": icinde,
        }
        # IKINCI GOZLENEBILIR: sok yaricapi eslesirken KE/E de esleiyor mu?
        if icinde and kf is not None and "kinetic_fraction" in p:
            kb = float(np.interp(r_esdeger, rd, kf))
            satir["kinetic_deposit_at_match"] = kb
            satir["kinetic_piston"] = float(p["kinetic_fraction"])
            satir["kinetic_mismatch_rel"] = float(
                (p["kinetic_fraction"] - kb) / max(abs(kb), 1e-300))
        satirlar.append(satir)

    ic_olan = np.array([s["in_bracket"] for s in satirlar], dtype=bool)
    oranlar = np.array([s["ratio"] for s in satirlar], dtype=np.float64)
    # Ikinci gozlenebilirin uyusmazligi (varsa)
    uyus = [s["kinetic_mismatch_rel"] for s in satirlar
            if "kinetic_mismatch_rel" in s]
    kin_maks = float(max(abs(u) for u in uyus)) if uyus else float("nan")
    # BOSLUK KONTROLU 2: piston kolu R ile GERCEKTEN degisiyor mu?
    rp_dizi = np.array([s["r_shock_piston"] for s in satirlar])
    piston_ayirt = bool(rp_dizi.max() - rp_dizi.min() > 1.0e-3)

    return {
        "rows": satirlar,
        "deposit_discriminates": ayirt,
        "piston_discriminates": piston_ayirt,
        "n_in_bracket": int(ic_olan.sum()),
        "ratio_mean": float(np.mean(oranlar[ic_olan])) if ic_olan.any()
        else float("nan"),
        # `r_dep/R` SABIT mi? Sabitse kalibrasyon TASINABILIR.
        "ratio_spread_rel": (
            float((oranlar[ic_olan].max() - oranlar[ic_olan].min())
                  / max(abs(np.mean(oranlar[ic_olan])), 1e-300))
            if int(ic_olan.sum()) >= 2 else float("nan")),
        # IKI nokta bir SABITLIK iddiasini tasiyamaz: iki noktayla "yayilim"
        # zaten tek bir farktir. En az UC nokta aralikta olmali.
        "enough_points": bool(int(ic_olan.sum()) >= 3),
        # Tek parametreli kalibrasyon IKI gozlenebiliri ayni anda esliyor mu?
        "kinetic_mismatch_max": kin_maks,
        "second_observable_matches": bool(kin_maks < 0.05) if uyus else False,
        "second_observable_available": bool(bool(uyus)),
        "transferable": bool(
            piston_ayirt and ayirt and int(ic_olan.sum()) >= 3
            and all(p.get("well_sampled", True) for p in piston_rows)
            and bool(uyus) and kin_maks < 0.05
            and float((oranlar[ic_olan].max() - oranlar[ic_olan].min())
                      / max(abs(np.mean(oranlar[ic_olan])), 1e-300)) < 0.20),
    }


def run_calibration(
    pistons: tuple[float, ...] = (0.03, 0.045, 0.06),
    h_injects: tuple[float, ...] = (0.015, 0.020, 0.025, 0.030, 0.040, 0.060),
    n_side: int = 64,
    device: str = "cuda:0",
    t_end: float = T_END_DEFAULT,
) -> dict:
    """Piston ve biriktirme kollarını koştur, eşlemeyi çıkar."""
    from .deposit_radius import _tek

    piston_rows = []
    for rp in pistons:
        ic = build_piston_ic(n_side, rp)
        if not ic["energy_matches"]:
            raise RuntimeError(
                f"piston enerjisi eşleşmedi: {ic['kinetic_energy']:.6e} "
                f"vs {E_INJECT:.6e}")
        d = _kostur(ic, device, t_end)
        piston_rows.append({**d, "r_piston": float(rp),
                            "n_piston": ic["n_piston"],
                            "kinetic_energy": ic["kinetic_energy"],
                            "well_sampled": ic["piston_well_sampled"]})

    deposit_rows = [_tek(n_side, hi, device, t_end) for hi in h_injects]
    tumu_iyi = all(p["well_sampled"] for p in piston_rows)
    return {
        "piston_rows": piston_rows, "deposit_rows": deposit_rows,
        "n_side": n_side, "t_end": t_end,
        "r_exact": float(shock_radius_exact(t_end)),
        # KAYIT-029: az orneklenmis nokta yargiyi CEVIRIR. Susarak gecilmez.
        "all_pistons_well_sampled": tumu_iyi,
        "min_piston_particles": int(min(p["n_piston"] for p in piston_rows)),
        **calibrate(piston_rows, deposit_rows),
    }
