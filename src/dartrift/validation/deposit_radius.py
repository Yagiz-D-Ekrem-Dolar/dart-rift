"""D-1 — kaynak terimi yaklaşımının **model-form hatası** nasıl ölçeklenir?

## Soru

**D**, mermiyi hiç çözmez: momentumunu ve enerjisini bir **kaynak terimi**
olarak hedefe koyar. Getirdiği hata bir *ayrıklaştırma* hatası değil,
**model-form** hatasıdır — gerçek mermi sonlu bir yapıya sahiptir, kaynak
terimi ise onu bir **biriktirme bölgesine** indirger.

Doğrudan kıyas **imkânsızdır**: DART mermisini çözmek `1,72e9` parçacık ister
(ADR-0026), fizibil sınır `1,12e7`. O yüzden **dolaylı** bir kıyas gerekir.

## Dolaylı kıyasın mantığı

Kaynak terimi, *"aynı enerji, **yapısız**"* demektir. Öyleyse sorulacak şey:

> **Gözlenebilir, enerjinin biriktirildiği bölgenin yarıçapına ne kadar
> duyarlı?**

Duyarlı değilse D geçerlidir; duyarlıysa duyarlılığın **yasası** ölçülmeli ve
DART'ın çalışma noktasına götürülmelidir.

## Bu proje bunu kısmen zaten ölçtü

ADR-0011: Sedov'da enerji **noktasal değil**, şok yarıçapının ~%32'si kadar
bir bölgeye konuyor ve bu **%3,9'luk** bir model-form tabanı yaratıyor.

Bu modül o tek noktayı bir **eğriye** çevirir: `r_enj / r_şok` taranır ve
hatanın nasıl ölçeklendiği ölçülür. Sedov'un **tam analitik** çözümü
(nokta patlaması) burada `r_enj → 0` limitidir — yani doğrudan referanstır.

**Boşluk kontrolü (ADR-0040):** en büyük ve en küçük `r_enj` **ayırt
edilebilir** hata vermeli. Vermezse gözlenebilir biriktirme yarıçapına
duyarsızdır ve tarama hiçbir şey ölçmez (ki bu da bir sonuçtur — ama
**ölçülmüş** bir sonuç).
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import RefParams
from .sedov import (E_INJECT, GAMMA, H_OVER_DX, T_END_DEFAULT, build_sedov_ic,
                    measure_shock_radius, shock_radius_exact)

__all__ = ["analyse_scan", "run_deposit_radius_scan"]


def _tek(n_side: int, h_inject: float, device: str, t_end: float) -> dict:
    from ..warp_core.solver import WarpSPH3D

    ic = build_sedov_ic(n_side, h_inject=h_inject)
    solver = WarpSPH3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"],
                       RefParams(gamma=GAMMA), device=device)
    diag = solver.run(t_end, max_steps=500_000)
    if diag["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(f"t_end'e ULASILAMADI: {diag['t_end']:.6g}")
    st = solver.state_numpy()
    r_olc = float(measure_shock_radius(st["x"], st["rho"]))
    r_tam = float(shock_radius_exact(t_end))
    # IKINCI GOZLENEBILIR — ADR-0041 §5 boslugu 2 icin.
    # Kinetik enerji kesri, Sedov'da beta'nin en yakin karsiligidir: enerjinin
    # ne kadari HAREKETE gitti, ne kadari ISI olarak kaldi? ADR-0011 olctu ki
    # nokta patlamasinda ~0,28, sonlu enjeksiyonda ~0,19 — yani sok
    # yaricapindan (%4) COK DAHA duyarli (%32). O yuzden bu tarama sok
    # yaricapiyla YETINMEZ.
    ke = 0.5 * float(np.sum(st["m"] * np.sum(st["v"] * st["v"], axis=1)))
    return {"h_inject": float(h_inject),
            "kinetic_fraction": ke / E_INJECT,
            "r_deposit": 2.0 * float(h_inject),      # cekirdek destegi
            "n_injected": int(ic["n_injected"]),
            "r_measured": r_olc, "r_exact": r_tam,
            "rel_err": abs(r_olc - r_tam) / r_tam,
            "signed_err": (r_olc - r_tam) / r_tam,
            "deposit_over_shock": 2.0 * float(h_inject) / r_tam,
            "n_steps": int(diag["n_steps"])}


def _kinetik_ozet(rows: list[dict], iyi: np.ndarray) -> dict:
    """Kinetik enerji kesri özeti — anahtar yoksa sessizce atlanır.

    Eski çıktılarla (bu alan eklenmeden önce üretilmiş) uyumlu kalır; ama
    **var olduğunda** raporlanır ve `kinetic_available` bunu söyler.
    """
    if not all("kinetic_fraction" in r for r in rows):
        return {"kinetic_available": False}
    kf = np.array([r["kinetic_fraction"] for r in rows], dtype=np.float64)
    if not iyi.any():
        return {"kinetic_available": True, "kinetic_well_sampled_range":
                [float("nan"), float("nan")], "kinetic_spread_rel": float("nan")}
    lo, hi = float(kf[iyi].min()), float(kf[iyi].max())
    return {
        "kinetic_available": True,
        "kinetic_all": [float(v) for v in kf],
        "kinetic_well_sampled_range": [lo, hi],
        # GORELI yayilim: sok yaricapi yayilimiyla kiyaslanabilsin diye.
        "kinetic_spread_rel": float((hi - lo) / max(abs(lo), 1e-300)),
    }


def analyse_scan(rows: list[dict], well_sampled_min: int = 100) -> dict:
    """Tarama satırlarını yorumla — **GPU gerekmez**, saf fonksiyon.

    Koşudan ayrıldı ki **asıl mantık** (iki rejimin ayrılması) sınanabilsin.
    Ölçülen veriyle doğrulandı: `n_side = 64` taramasında `n_enj = 32` ve
    `56` noktaları hâlâ **örnekleme** hatası taşıyordu; eşik `20` değil
    **100** olmalıydı.
    """
    if len(rows) < 3:
        raise ValueError(f"en az 3 nokta gerekir, {len(rows)} geldi")
    hatalar = np.array([r["rel_err"] for r in rows], dtype=np.float64)
    oranlar = np.array([r["deposit_over_shock"] for r in rows], dtype=np.float64)
    n_dizi = np.array([r["n_injected"] for r in rows], dtype=np.int64)
    if np.any(oranlar <= 0.0):
        raise ValueError("deposit_over_shock pozitif olmali")

    iyi = n_dizi >= int(well_sampled_min)

    def _us(mask: np.ndarray) -> float:
        m = mask & (hatalar > 1.0e-6)
        if int(m.sum()) < 3:
            return float("nan")
        return float(np.polyfit(np.log(oranlar[m]), np.log(hatalar[m]), 1)[0])

    return {
        "scan_discriminates": bool(hatalar.max() - hatalar.min() > 0.01),
        "error_exponent": _us(iyi),
        "error_exponent_contaminated": _us(np.ones_like(iyi)),
        "n_well_sampled": int(iyi.sum()),
        "min_injected_particles": int(n_dizi.min()),
        "well_sampled_err_range": (
            [float(hatalar[iyi].min()), float(hatalar[iyi].max())]
            if iyi.any() else [float("nan"), float("nan")]),
        "well_sampled_spread": (
            float(hatalar[iyi].max() - hatalar[iyi].min()) if iyi.any()
            else float("nan")),
        # Ikinci gozlenebilir: kinetik kesir. Sok yaricapindan DAHA DUYARLI
        # oldugu icin D hakkindaki yargi buna da bakmali (ADR-0041 §5-2).
        **_kinetik_ozet(rows, iyi),
        "injection_well_sampled": bool(int(n_dizi.min()) >= int(well_sampled_min)),
        "enough_well_sampled_points": bool(int(iyi.sum()) >= 3),
    }


def run_deposit_radius_scan(
    h_injects: tuple[float, ...] = (0.010, 0.015, 0.020, 0.030, 0.040, 0.060),
    n_side: int = 64,
    device: str = "cuda:0",
    t_end: float = T_END_DEFAULT,
) -> dict:
    """`r_enj / r_şok` taranır; hatanın **ölçeklenme yasası** çıkarılır.

    `h_inject` çok küçülürse enjeksiyon bölgesi **boşalır** (hiçbir parçacık
    destek içinde kalmaz) ve `build_sedov_ic` açıkça hata verir. Alt sınır
    kafes aralığına bağlıdır: `dx = 1/n_side`.
    """
    dx = 1.0 / float(n_side)
    if min(h_injects) < H_OVER_DX * dx * 0.4:
        raise ValueError(
            f"en kucuk h_inject={min(h_injects)} kafes icin cok kucuk "
            f"(dx={dx:.5f}); enjeksiyon bolgesi bosalir")
    if sorted(h_injects) != list(h_injects):
        raise ValueError(f"h_inject listesi artan olmali: {h_injects}")

    satirlar = [_tek(n_side, hi, device, t_end) for hi in h_injects]

    return {
        "rows": satirlar, "n_side": n_side, "dx": dx, "t_end": t_end,
        "r_exact": float(shock_radius_exact(t_end)),
        **analyse_scan(satirlar),
    }
