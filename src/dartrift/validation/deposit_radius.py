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
from .sedov import (GAMMA, H_OVER_DX, T_END_DEFAULT, build_sedov_ic,
                    measure_shock_radius, shock_radius_exact)

__all__ = ["run_deposit_radius_scan"]


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
    return {"h_inject": float(h_inject),
            "r_deposit": 2.0 * float(h_inject),      # cekirdek destegi
            "n_injected": int(ic["n_injected"]),
            "r_measured": r_olc, "r_exact": r_tam,
            "rel_err": abs(r_olc - r_tam) / r_tam,
            "signed_err": (r_olc - r_tam) / r_tam,
            "deposit_over_shock": 2.0 * float(h_inject) / r_tam,
            "n_steps": int(diag["n_steps"])}


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

    # BOSLUK KONTROLU: tarama gercekten AYIRT EDIYOR mu?
    hatalar = np.array([s["rel_err"] for s in satirlar])
    oranlar = np.array([s["deposit_over_shock"] for s in satirlar])
    ayirt = bool(hatalar.max() - hatalar.min() > 0.01)

    # AYRIKLASTIRMA KIRLENMESI. Enjeksiyon bolgesinde parcacik sayisi azsa
    # hata model-form degil ORNEKLEME hatasidir. Ilk esigim (>= 20) COK
    # GEVSEKTI: olculdu (n_side=64) —
    #   n_enj= 32 -> hata %7,11
    #   n_enj= 56 -> hata %9,61      <-- az orneklenen rejim
    #   n_enj=136 -> hata %4,03
    #   n_enj=208 -> hata %4,44
    #   n_enj=552 -> hata %4,46
    #   n_enj=1904 -> hata %3,26     <-- iyi orneklenen rejim, ~%4'te DUZ
    # Tum noktalarla uydurulan us +0,647; yalniz iyi orneklenenlerle +0,264.
    # Ilki KIRLENMISTIR ve yasa diye raporlanmamalidir.
    n_dizi = np.array([s["n_injected"] for s in satirlar])
    n_min = int(n_dizi.min())
    iyi = n_dizi >= 100

    def _us(mask) -> float:
        m = mask & (hatalar > 1.0e-6)
        if int(m.sum()) < 3:
            return float("nan")
        return float(np.polyfit(np.log(oranlar[m]), np.log(hatalar[m]), 1)[0])

    p = _us(iyi)                       # YALNIZCA iyi orneklenen rejim
    p_ham = _us(np.ones_like(iyi))     # kirlenmis — kiyas icin

    return {
        "rows": satirlar, "n_side": n_side, "dx": dx, "t_end": t_end,
        "r_exact": float(shock_radius_exact(t_end)),
        "scan_discriminates": ayirt,
        # Us YALNIZCA iyi orneklenen noktalardan; ham hali kiyas icin.
        "error_exponent": p,
        "error_exponent_contaminated": p_ham,
        "n_well_sampled": int(iyi.sum()),
        "min_injected_particles": n_min,
        # Iyi rejimde hatanin YAYILIMI: kucukse gozlenebilir biriktirme
        # yaricapina DUYARSIZDIR (D icin iyi haber).
        "well_sampled_err_range": [float(hatalar[iyi].min()),
                                   float(hatalar[iyi].max())] if iyi.any()
        else [float("nan"), float("nan")],
        # Ayriklastirma kirlenmesi denetimi: en kucuk enjeksiyon bolgesinde
        # bile YETERLI parcacik olmali (yoksa yasa model-formu degil,
        # ornekleme hatasini olcer).
        # Esik 20 DEGIL 100: olculdu ki 32 ve 56 parcacikli noktalar hala
        # ornekleme hatasi tasiyor (bkz. yukaridaki tablo).
        "injection_well_sampled": bool(n_min >= 100),
        "enough_well_sampled_points": bool(int(iyi.sum()) >= 3),
    }
