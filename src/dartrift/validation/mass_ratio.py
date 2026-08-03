"""FAZ 4.1 — kütle oranı toleransı: yerel incelme ne kadar agresif olabilir?

SORU. ADR-0026 ölçtü: DART mermisini çözmek **1,72e9** parçacık ister, fizibil
sınır **1,12e7** — **153 kat** fark. Tek yol çarpma bölgesinde yerel yüksek
çözünürlük. ADR-0026 §2 bunun *nasıl* yapılacağını FAZ 4'e ve **ölçüme**
bıraktı.

Bu modül en temel seçeneği (A: değişken kütle bölgeleri) sınar ve tek bir
sayı üretir: **çözücü hangi kütle oranına kadar temiz kalıyor?**

O sayı doğrudan seviye sayısını verir: oran `R` ise `153 = R^k` çözülür.
Örneğin `R = 8` → `k ≈ 2,4` → **3 seviye** yeter.

DÜZENEK. Aynı fiziksel küre iki popülasyonla doldurulur:
  * **iç bölge** (r < r_ic): ince parçacıklar, aralık `s/λ`
  * **dış bölge**: kaba parçacıklar, aralık `s`
Kütleler ADR-0030 kuralıyla atanır (`m = ρ·V_p`), yani oran tam `λ³` olur.

NEDEN ŞİMDİ YAPILABİLİR. ADR-0030'dan **önce** bu ölçüm yorumlanamazdı:
kütleler tekdüzeydi ve `m/ρ ≠ V_p` tutarsızlığı (K7) her sonucu kirletirdi.
Şimdi `m_i = ρ_i·V_p` tam tutuyor (`[1,000000 ; 1,000000]`), yani kütle
oranını değiştirmek **yalnızca** kütle oranını değiştiriyor.

BOŞLUK KONTROLÜ (ADR-0040). `λ = 1` (oran 1:1) durumunda sonuç **tam temiz**
çıkmalı. Çıkmazsa düzeneğin kendisi bozuktur ve hiçbir sayı yorumlanamaz —
bu, döndürülen sözlükte `baseline_clean` olarak raporlanır.
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import kernel_w

__all__ = ["build_two_zone", "measure_partition_of_unity", "run_mass_ratio_scan"]


def build_two_zone(
    r_outer: float = 60.0,
    r_inner: float = 25.0,
    spacing: float = 8.0,
    lam: float = 2.0,
    rho: float = 2700.0,
) -> dict:
    """İki bölgeli küre: iç bölge `lam` kat daha ince.

    FCC kafesler ayrı ayrı kurulur; iç bölgenin kaba parçacıkları atılır.
    Kütle ADR-0030 kuralıyla: `m = rho * V_p(aralık)`.

    `lam = 1` -> tek popülasyon (taban durumu).

    `rho` VARSAYILANI 2700 (Tillotson bazalt `rho0`), 1800 DEĞİL. Gerekçe:
    gözeneklilik kapalıyken (`alpha = 1`) çözücü başlangıç yoğunluğunu
    `rho0_solid/alpha = rho0_solid` olarak atar (ADR-0022). Kütleyi 1800'den
    üretmek `m/rho ≠ V_p` yapardı — **K7'nin ta kendisi**. İlk yazdığım
    sürümde 1800 kullanmıştım; kampanyanın kuralı burada da geçerli:
    *kütle, çözücünün atadığı yoğunlukla tutarlı olmak zorunda.*
    """
    if lam < 1.0:
        raise ValueError(f"lam >= 1 olmali, {lam} geldi")
    if not (0.0 < r_inner < r_outer):
        raise ValueError(f"0 < r_inner < r_outer olmali: {r_inner}, {r_outer}")

    def _fcc(s: float, rmax: float) -> np.ndarray:
        a = s * np.sqrt(2.0)
        base = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0],
                         [0.5, 0.0, 0.5], [0.0, 0.5, 0.5]]) * a
        n = int(np.ceil(2.0 * rmax / a)) + 2
        g = (np.arange(n) - n // 2) * a
        cell = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
        pts = (cell[:, None, :] + base[None, :, :]).reshape(-1, 3)
        return pts[np.linalg.norm(pts, axis=1) <= rmax]

    s_in = spacing / lam
    kaba = _fcc(spacing, r_outer)
    kaba = kaba[np.linalg.norm(kaba, axis=1) > r_inner]      # ic bolgeyi bosalt
    ince = _fcc(s_in, r_inner)

    v_kaba = spacing**3 / np.sqrt(2.0)
    v_ince = s_in**3 / np.sqrt(2.0)
    x = np.vstack([ince, kaba])
    m = np.concatenate([np.full(len(ince), rho * v_ince),
                        np.full(len(kaba), rho * v_kaba)])
    ic_mi = np.concatenate([np.ones(len(ince), bool), np.zeros(len(kaba), bool)])
    return {
        "x": x, "m": m, "is_inner": ic_mi,
        "rho": np.full(len(x), rho),
        "V_p": np.where(ic_mi, v_ince, v_kaba),
        "spacing_outer": spacing, "spacing_inner": s_in,
        "mass_ratio": float(v_kaba / v_ince),        # tam lam^3 olmali
        "lam": float(lam),
        "n_inner": int(len(ince)), "n_outer": int(len(kaba)),
        "r_inner": r_inner, "r_outer": r_outer,
    }


def measure_partition_of_unity(z: dict, h_over_spacing: float = 2.0) -> dict:
    """`Σ_j (m_j/ρ_j) W_ij` — 1'den sapma, ayrıklaştırmanın tutarsızlığıdır.

    Düzgün tek popülasyonda 1'e çok yakın çıkar (ADR-0030 sonrası ölçülen
    1,0002). İki popülasyonun **arayüzünde** sapma beklenir; bu ölçümün
    amacı o sapmanın kütle oranıyla nasıl büyüdüğünü görmektir.

    `h` KABA aralıktan türetilir — yerel incelmede kaba taraf kısıtı belirler.
    """
    x, m, rho = z["x"], z["m"], z["rho"]
    h = h_over_spacing * z["spacing_outer"]
    d = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)
    S = kernel_w(d / h, h, 3) @ (m / rho)

    r = np.linalg.norm(x, axis=1)
    kenar = r < z["r_outer"] - 2.5 * z["spacing_outer"]       # yuzeyden uzak
    ri = z["r_inner"]
    arayuz = kenar & (np.abs(r - ri) < 1.5 * z["spacing_outer"])
    derin_ic = kenar & (r < ri - 1.5 * z["spacing_outer"])
    derin_dis = kenar & (r > ri + 1.5 * z["spacing_outer"])

    def _ozet(mask):
        if not np.any(mask):
            return {"n": 0, "mean": float("nan"), "max_dev": float("nan")}
        v = S[mask]
        return {"n": int(mask.sum()), "mean": float(v.mean()),
                "max_dev": float(np.max(np.abs(v - 1.0)))}

    return {"interface": _ozet(arayuz), "deep_inner": _ozet(derin_ic),
            "deep_outer": _ozet(derin_dis), "h": h}


def run_mass_ratio_scan(
    lams: tuple[float, ...] = (1.0, 1.26, 1.44, 1.59, 2.0, 2.52),
    r_outer: float = 60.0,
    r_inner: float = 25.0,
    spacing: float = 8.0,
) -> dict:
    """Kütle oranını tara ve bozulmanın nerede başladığını raporla.

    `lams` uzunluk oranıdır; kütle oranı `lam^3`'tür:
        1.00 -> 1:1      1.26 -> 2:1      1.44 -> 3:1
        1.59 -> 4:1      2.00 -> 8:1      2.52 -> 16:1

    BOŞLUK KONTROLÜ: `lam = 1` durumu **temiz** çıkmalı; `baseline_clean`
    False ise düzenek bozuktur ve diğer satırlar yorumlanamaz.
    """
    satirlar = []
    for lam in lams:
        z = build_two_zone(r_outer, r_inner, spacing, lam)
        pu = measure_partition_of_unity(z)
        sa = measure_spurious_acceleration(z)
        satirlar.append({
            "lam": float(lam),
            "mass_ratio": z["mass_ratio"],
            "n_total": int(len(z["m"])),
            "n_inner": z["n_inner"],
            "interface_max_dev": pu["interface"]["max_dev"],
            "interface_n": pu["interface"]["n"],
            "deep_inner_max_dev": pu["deep_inner"]["max_dev"],
            "deep_outer_max_dev": pu["deep_outer"]["max_dev"],
            "a_interface_over_ref": sa["a_interface_over_reference"],
            "a_deep": sa["a_max_deep"],
            "a_interface": sa["a_max_interface"],
            "field_is_uniform": sa["field_is_uniform"],
        })

    taban = satirlar[0]
    taban_temiz = bool(
        abs(taban["mass_ratio"] - 1.0) < 1e-9
        and taban["interface_max_dev"] < 0.02
        and taban["deep_outer_max_dev"] < 0.02)
    # ADR-0039'un dersi: olcum = TABAN + sinyal. Taban, kafesin kureyle
    # kesilmesinden gelen ayriklastirma hatasidir ve KUTLE ORANIYLA ILGISIZDIR.
    # Kriter FAZLALIGA bakmali.
    a_taban = taban["a_interface_over_ref"]
    for st in satirlar:
        st["a_excess_over_baseline"] = st["a_interface_over_ref"] - a_taban
    return {
        "rows": satirlar,
        "baseline_clean": taban_temiz,
        "baseline_interface_dev": taban["interface_max_dev"],
        "baseline_a_over_ref": a_taban,
        "max_excess": max(st["a_excess_over_baseline"] for st in satirlar),
        "note": ("lam=1 taban durumudur ve TEMIZ cikmali; cikmazsa duzenek "
                 "bozuktur ve diger satirlar yorumlanamaz (ADR-0040). "
                 "Yapay ivme TABAN + kutle-orani katkisi toplamidir; taban "
                 "kafesin kureyle kesilmesinden gelir ve oranla ILGISIZDIR "
                 "(ADR-0039 dersi) — bu yuzden FAZLALIK raporlanir."),
    }


def measure_spurious_acceleration(z: dict, h_over_spacing: float = 2.0,
                                  rho0: float = 2700.0,
                                  eps: float = 0.01) -> dict:
    """DÜZGÜN (sabit) bir basınç alanında `a_SPH` — **sıfır** olmalı.

    SPH'in sıfırıncı mertebe tutarlılık sınavı: **sabit bir alanın gradyanı
    sıfırdır.** Düzensiz ya da karışık kütleli bir dağılımda ayrık gradyan
    bunu tam veremez ve **yapay kuvvet** doğar. Yerel incelmenin bedeli tam
    olarak budur.

    İLK YAZDIĞIM HÂLİ BOŞ BİR TESTTİ (ADR-0040'ın ta kendisi). `rho = rho0`
    ve `u = 0` alıyordum; o durumda `P = 0` ve `S = 0`, dolayısıyla kuvvet
    terimi `T = (-P I + S)/rho^2` **özdeş olarak sıfır**. İvmenin sıfır
    çıkması ayrıklaştırmayla ilgisiz, **cebirsel bir zorunluluktu** — ölçüm
    16:1 kütle oranında bile `0.0000e+00` veriyordu ve hiçbir şey sınamıyordu.

    Düzeltilmiş kurulum: `rho = rho0 * (1 + eps)` DÜZGÜN sıkıştırma →
    `P` her yerde AYNI ve SIFIRDAN FARKLI. Gradyan yine sıfır olmalı, ama
    artık bunu sağlamak ayrıklaştırmanın işidir.

    CPU referansı kullanılır (`evaluate_solid`): N küçük, GPU gerekmez ve
    referans zaten çapraz kontrollü.
    """
    from ..cpu_reference.materials import (
        DamageParams, GravityParams, MaterialParams, PorosityParams,
        StrengthParams)
    from ..cpu_reference.solid_ref import SolidState, evaluate_solid
    from ..cpu_reference.sph_ref import RefParams

    x, m = z["x"], z["m"]
    n = len(m)
    h = h_over_spacing * z["spacing_outer"]
    mat = MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e5, mu_f=0.8, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=False),
        gravity=GravityParams(enabled=False),
        damage=DamageParams(enabled=False),
        density_method="continuity")
    # DUZGUN sikistirma: P her yerde AYNI ve sifirdan farkli.
    st = SolidState(x=x.copy(), v=np.zeros_like(x), m=m, u=np.zeros(n), h=h,
                    active=np.ones(n, bool), alpha=np.ones(n),
                    rho=np.full(n, rho0 * (1.0 + eps)))
    evaluate_solid(st, mat, RefParams(cfl=0.2))
    # Alan gercekten DUZGUN mu? Degilse bu olcum baska bir seyi olcer.
    p_yayilim = float(np.ptp(st.P))

    a = np.linalg.norm(st.a, axis=1)
    r = np.linalg.norm(x, axis=1)
    kenar = r < z["r_outer"] - 2.5 * z["spacing_outer"]
    ri = z["r_inner"]
    arayuz = kenar & (np.abs(r - ri) < 1.5 * z["spacing_outer"])
    derin = kenar & (np.abs(r - ri) >= 1.5 * z["spacing_outer"])

    # Olcek: ayni kurulumda GERCEK bir basinctan dogacak ivme mertebesi.
    # Boylece "buyuk mu" sorusu mutlak degil, KIYASLI yanitlanir.
    # Olcek: uygulanan DUZGUN basincin kendisinden dogacak ivme mertebesi
    # (P / (rho * h)). Boylece "buyuk mu" sorusu mutlak degil, KIYASLI.
    p_uygulanan = float(np.mean(st.P))
    a_ref = abs(p_uygulanan) / (rho0 * h)
    return {
        "a_max_interface": float(a[arayuz].max()) if arayuz.any() else float("nan"),
        "a_max_deep": float(a[derin].max()) if derin.any() else float("nan"),
        "a_max_all": float(a[kenar].max()) if kenar.any() else float("nan"),
        "P_max_abs": float(np.max(np.abs(st.P))),
        "P_applied": p_uygulanan,
        "P_spread": p_yayilim,
        "field_is_uniform": bool(p_yayilim < 1.0e-6 * max(abs(p_uygulanan), 1.0)),
        "a_reference_scale": float(a_ref),
        "a_interface_over_reference": (
            float(a[arayuz].max() / a_ref) if arayuz.any() else float("nan")),
        "n_interface": int(arayuz.sum()),
    }
