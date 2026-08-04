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


def _masks(z: dict, h: float) -> dict:
    """Bölge maskeleri. Kenar payı **çekirdek desteğinden** türetilir.

    Wendland C2'nin desteği `2h`'dir. Dış yüzeye `2h`'den yakın bir parçacığın
    komşuluğu **kesiktir** ve orada yapay kuvvet doğar — bu, kütle oranıyla
    ilgisiz bir yüzey artığıdır.

    İLK YAZDIĞIM HÂLİ 2,5·aralık pay bırakıyordu; `h = 2·aralık` olduğu için
    destek `4·aralık`tır, yani pay **yetersizdi**. Ölçüldü (tek popülasyon,
    düzgün basınç — doğru cevap tam sıfır):

        kenar payı   n     a_maks       a/ölçek
          2,5·s     683   5,4813e+02    0,0878
          3,0·s     555   8,5467e+01    0,0137
          4,0·s     249   5,8938e-12    0,0000   <-- destek sınırı
          5,0·s      87   4,1911e-12    0,0000

    Yani "taban 0,0397" diye raporladığım şey **tamamen** maskemin artığıydı.
    Doğru pay ile taban makine hassasiyetinde sıfır çıkıyor ve arayüz katkısı
    **yalnız kalıyor**.
    """
    r = np.linalg.norm(z["x"], axis=1)
    s_out = z["spacing_outer"]
    pay = 2.0 * h + 0.5 * s_out           # destek + yarim aralik guvenlik
    ri = z["r_inner"]
    # GEOMETRI YETERLI MI: pay disaridan, h de arayuzden yer yiyor. "Derin dis"
    # bolgesi bos kalirsa olcum sessizce yalnizca ic bolgeyi olcer.
    if z["r_outer"] - pay <= ri + h:
        raise ValueError(
            f"geometri yetersiz: r_outer={z['r_outer']:.1f} ama kenar payi "
            f"{pay:.1f} + arayuz {h:.1f} + r_inner {ri:.1f} = "
            f"{pay + h + ri:.1f} gerekiyor. Derin DIS bolge bos kalirdi.")
    kenar = r < z["r_outer"] - pay
    return {
        "r": r, "kenar": kenar, "margin": pay,
        "arayuz": kenar & (np.abs(r - ri) < h),
        "derin_ic": kenar & (r < ri - h),
        "derin_dis": kenar & (r > ri + h),
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

    mk = _masks(z, h)
    arayuz, derin_ic, derin_dis = mk["arayuz"], mk["derin_ic"], mk["derin_dis"]

    def _ozet(mask):
        if not np.any(mask):
            return {"n": 0, "mean": float("nan"), "max_dev": float("nan")}
        v = S[mask]
        return {"n": int(mask.sum()), "mean": float(v.mean()),
                "max_dev": float(np.max(np.abs(v - 1.0)))}

    return {"interface": _ozet(arayuz), "deep_inner": _ozet(derin_ic),
            "deep_outer": _ozet(derin_dis), "h": h, "margin": mk["margin"]}


def run_mass_ratio_scan(
    lams: tuple[float, ...] = (1.0, 1.26, 1.44, 1.59, 2.0, 2.52),
    r_outer: float = 70.0,
    r_inner: float = 25.0,
    spacing: float = 8.0,
    h_over_spacing: float = 1.3,
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
        pu = measure_partition_of_unity(z, h_over_spacing)
        sa = measure_spurious_acceleration(z, h_over_spacing)
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
            "a_p50": sa["a_p50_interface"],
            "a_rms": sa["a_rms_interface"],
            "a_radial_mean": sa["a_radial_mean_interface"],
            "systematic_ratio": sa["systematic_ratio"],
            "momentum_residual": sa["net_momentum_residual"],
            "n_deep": sa["n_deep"],
            "field_is_uniform": sa["field_is_uniform"],
        })

    taban = satirlar[0]
    # Taban tek populasyondur: DUZGUN basincta yapay kuvvet MAKINE
    # HASSASIYETINDE sifir olmali. Olculdu: 9,263e-16.
    # Bolgelerin DOLU olmasi da sart — bos bolge sessizce olcum kaybettirir.
    taban_temiz = bool(
        abs(taban["mass_ratio"] - 1.0) < 1e-9
        and taban["a_interface_over_ref"] < 1.0e-9
        and taban["interface_n"] > 20
        and np.isfinite(taban["deep_outer_max_dev"]))
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
                                  eps: float = 0.01,
                                  rho_base: np.ndarray | None = None,
                                  interior_mask: np.ndarray | None = None) -> dict:
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
    #
    # `rho_base`: ADR-0030'un degismezi `m_i = rho_i * V_p` KORUNMALIDIR.
    # Iki bolgeli duzenekte kutleler zaten `rho0 * V_p` ile uretildigi icin
    # skaler `rho0` TAM dogrudur. Ama GERCEK bir yigina (yigin yogunlugu
    # 2400, katı yogunlugu 2700) skaler `rho0` uygulamak `m/rho != V_p`
    # yapardi — K7'nin ta kendisi, bu kez ucuncu kez. O yuzden cagiran taraf
    # parcacik basina taban yogunlugunu (`m / V_p`) VEREBILIR.
    if rho_base is None:
        rho_taban = np.full(n, float(rho0))
    else:
        rho_taban = np.ascontiguousarray(rho_base, np.float64)
        if rho_taban.shape != (n,):
            raise ValueError(f"rho_base sekli {rho_taban.shape}, ({n},) olmali")
    # DISTANSIYON: gercek cozucude gozenekli malzeme icin `rho_kati = rho*alpha`
    # ve `alpha = rho0_kati/rho_yigin` (ADR-0022/0031). Bunu atlarsak, yigin
    # yogunlugu 2400 olan bir yigina `rho0 = 2700` uygulamak malzemeyi GERILMIS
    # sayar: olculdu, P = +2,6967e+08 yerine **-2,4503e+09** — isaret bile ters.
    # Olculen buyukluk bir ORAN oldugu ve `a ~ P` dogrusal oldugu icin (KAYIT-020
    # §3) yargi degismez; ama basincin sahte olmasi icin bir sebep yok.
    alpha = np.full(n, float(rho0)) / rho_taban
    st = SolidState(x=x.copy(), v=np.zeros_like(x), m=m, u=np.zeros(n), h=h,
                    active=np.ones(n, bool), alpha=alpha,
                    rho=rho_taban * (1.0 + eps))
    evaluate_solid(st, mat, RefParams(cfl=0.2))
    # Alan gercekten DUZGUN mu? Degilse bu olcum baska bir seyi olcer.
    p_yayilim = float(np.ptp(st.P))

    a = np.linalg.norm(st.a, axis=1)
    if interior_mask is None:
        mk = _masks(z, h)
        kenar, arayuz = mk["kenar"], mk["arayuz"]
        derin = kenar & ~arayuz
    else:
        # TEK POPULASYON kipi: iki bolgeli duzenek yok, yalnizca "yuzeyden
        # yeterince uzak ic bolge". Cagiran taraf maskeyi KENDI verir cunku
        # kuresel `r` duzensiz bir cisimde VEKILDIR (K14'un dersi): 88x87x74
        # bir elipsoitte |x| yuzeye uzakligi vermez. Dogrusu mesh'in
        # ISARETLI MESAFESIDIR.
        kenar = np.ascontiguousarray(interior_mask, bool)
        if kenar.shape != (n,):
            raise ValueError(f"interior_mask sekli {kenar.shape}, ({n},) olmali")
        if not kenar.any():
            raise ValueError("interior_mask BOS — olcum hicbir sey olcmez")
        arayuz = kenar
        derin = np.zeros(n, bool)
        mk = {"margin": float("nan")}

    # ISARETLI RADYAL BILESEN. Maksimum tek bir parcacigi gosterir; asil soru
    # hatanin SISTEMATIK mi (arayuzu surukler) yoksa RASTGELE mi (birbirini
    # goturur) oldugudur. Radyal ortalama sifirdan ayrilirsa arayuz kayar.
    r_vec = z["x"]
    r_nrm = np.linalg.norm(r_vec, axis=1)
    guvenli = r_nrm > 1.0e-12
    a_rad = np.zeros(n)
    a_rad[guvenli] = np.einsum(
        "ij,ij->i", st.a[guvenli], r_vec[guvenli] / r_nrm[guvenli, None])

    # Momentum korunumu: SPH'in simetrik kuvvet bicimi ANTISIMETRIKTIR, yani
    # SUM(m_i a_i) TAM SIFIR olmali. Sifir degilse cozucude hata var, arayuzde
    # degil — bu, olcum aracinin kendi kalibrasyonudur.
    net_p = float(np.linalg.norm((m[:, None] * st.a).sum(axis=0)))
    olcek_p = float(np.sum(m * a)) or 1.0

    # Olcek: ayni kurulumda GERCEK bir basinctan dogacak ivme mertebesi.
    # Boylece "buyuk mu" sorusu mutlak degil, KIYASLI yanitlanir.
    # Olcek: uygulanan DUZGUN basincin kendisinden dogacak ivme mertebesi
    # (P / (rho * h)). Boylece "buyuk mu" sorusu mutlak degil, KIYASLI.
    p_uygulanan = float(np.mean(st.P))
    a_ref = abs(p_uygulanan) / (float(np.mean(rho_taban)) * h)
    return {
        "a_max_interface": float(a[arayuz].max()) if arayuz.any() else float("nan"),
        "a_max_deep": float(a[derin].max()) if derin.any() else float("nan"),
        "a_max_all": float(a[kenar].max()) if kenar.any() else float("nan"),
        "P_max_abs": float(np.max(np.abs(st.P))),
        "P_applied": p_uygulanan,
        "P_spread": p_yayilim,
        "field_is_uniform": bool(p_yayilim < 1.0e-6 * max(abs(p_uygulanan), 1.0)),
        # Taban yogunlugu parcacik basina degisiyorsa P de degisir; o zaman
        # "duzgun alan" sinavi ANLAMSIZDIR ve bunu susarak gecmemek gerekir.
        "rho_base_is_uniform": bool(float(np.ptp(rho_taban)) < 1.0e-9),
        "alpha_range": [float(alpha.min()), float(alpha.max())],
        "a_reference_scale": float(a_ref),
        "a_interface_over_reference": (
            float(a[arayuz].max() / a_ref) if arayuz.any() else float("nan")),
        "n_interface": int(arayuz.sum()),
        "n_deep": int(derin.sum()),
        "margin": mk["margin"],
        "single_population_mode": bool(interior_mask is not None),
        # Dagilim: maksimum tek parcacik, medyan/p90 ise arayuzun BUTUNU.
        "a_p50_interface": (
            float(np.median(a[arayuz])) if arayuz.any() else float("nan")),
        "a_p90_interface": (
            float(np.percentile(a[arayuz], 90)) if arayuz.any() else float("nan")),
        "a_rms_interface": (
            float(np.sqrt(np.mean(a[arayuz] ** 2))) if arayuz.any() else float("nan")),
        # Sistematik mi rastgele mi: isaretli radyal ortalama / RMS.
        "a_radial_mean_interface": (
            float(np.mean(a_rad[arayuz])) if arayuz.any() else float("nan")),
        "systematic_ratio": (
            float(abs(np.mean(a_rad[arayuz])) / np.sqrt(np.mean(a[arayuz] ** 2)))
            if arayuz.any() and np.any(a[arayuz]) else 0.0),
        # Olcum aracinin kendi kalibrasyonu (bkz. YONTEM "araci da kalibre et").
        "net_momentum_residual": net_p / olcek_p,
    }
