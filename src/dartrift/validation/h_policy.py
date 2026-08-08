"""`h` **sabit mi kalmalı, yoksa `ρ` ile evrilmeli mi?** (FAZ 4.3b)

## Neden bu ölçüm zorunlu

ADR-0041 §5b'nin kilitlenen sözleşmesinde iki madde **çelişiyor**:

| madde | metin |
|---|---|
| 2 | `Ω` (grad-h) düzeltmesi **uygulanır** |
| 4 | skaler `h` yolu **bit düzeyinde korunur** |

`Ω`'nın türetimi baştan sona bir **zincir kuralıdır**:

```
Ω_i = 1 − (∂h_i/∂ρ_i) · Σ_j m_j ∂W_ij/∂h_i
```

`∂h_i/∂ρ_i` çarpanı **yalnızca** `h_i = η (m_i/ρ_i)^{1/3}` bağıntısından
gelir. Kodda `h` kurulumda bir kez atanıyor ve **hiç evrilmiyor**
(`solver_solid.py:82` — `h_arr` bir kez yazılır, güncellenmez). Sabit `h`
demek `∂h_i/∂ρ_i = 0` demek, o da `Ω_i ≡ 1` demek — **tam olarak**.

Yani mevcut `h` politikasında madde 2 **boştur**. Üstelik `Ω`'yı yine de
sıfırdan farklı hesaplayıp uygulamak madde 4'ü **kırardı**: skaler `h`'de
bile `Ω ≠ 1` çıkar ve basınç terimi değişir.

> **Çelişki gerçek.** Çözümü bir tercih değil, bir **ölçümdür**: sabit `h`
> DART'ın ürettiği yoğunluk salınımında yeterli mi?

## Ölçülen büyüklük: komşu sayısı

Sabit `h` ve sabit parçacık kütlesiyle

```
N_komşu ≈ (4/3)π (2h)³ · ρ/m        ⇒        N_komşu ∝ ρ
```

Şok 4 kat sıkıştırırsa komşu sayısı **4 katına** çıkar; genleşen kuyrukta
onda birine iner. Soru şu: **doğruluk bu aralıkta değişiyor mu?**

## Deneyin kurgusu — `N_komşu`'yu `h`'den **ayırmak**

`h/dx`'i taramak iki şeyi birden değiştirir: komşu sayısını **ve** çözülen
ölçeği. [`resolution_scaling`][dartrift.validation.resolution_scaling] zaten
ölçtü ki platonun **yerini** `h` belirliyor. Dolayısıyla `h/dx` taraması bu
soruyu **yanıtlamaz**.

**`h` sabit tutulup `dx` taranır.** O zaman çözülen ölçek sabittir ve
`N_komşu ∝ (h/dx)³` değişir.

> ### ⚠ Bu tam bir ayrıştırma **değildir**
>
> İlk yazdığımda "yayılım varsa suçlu komşu sayısıdır" dedim. **Yanlış.**
> Sabit `h`'de `dx`'i değiştirmek komşu sayısını **ve** ayrıklaştırma
> hatasını aynı anda değiştirir — ikisi tek düğmedir, ayrılamazlar.
> Ölçülen `n = 40…80` eğrisi (hata `%16,17 → %3,18`, hâlâ **düşüyor**)
> bunu açıkça gösteriyor: sabit-`h` platosuna daha oturulmamış.
>
> **Ama ölçüm yine de sonuç veriyor** — çünkü aradığımız şey bir **üst
> sınır**. Çalışma aralığında (`N_komşu` 268→551) ölçülen toplam yayılım
> hem `dx` yakınsamasını hem komşu sayısını içerir; dolayısıyla komşu
> sayısının **tek başına** payı bundan **küçüktür**. Toplam tolerans
> altındaysa, parça da altındadır.
>
> Bu, ölçümü zayıflatmıyor; **yönünü** düzeltiyor. Yargı "komşu sayısı
> etkisizdir" değil, "**etkisi şu üst sınırın altındadır**".

Bir ikinci sınır daha yazılmalı: deney `N_komşu`'yu **koşular arasında,
tekdüze** değiştiriyor; gerçek bir çarpışmada tek bir parçacığın komşu
sayısı **zaman içinde** salınır. Bu birebir aynı şey değildir. Tekdüze
2 katlık bir değişime duyarsızlık, yerel 2 katlık bir salınımın daha
büyük bir etki yaratmayacağının **kesin kanıtı değil**, makul bir
göstergesidir.

`resolution_scaling`'in sabit-`h` kolu bunu **zaten** yapmıştı ama dar bir
aralıkta: `n = 56…64`, yani `N_komşu` oranı yalnızca `(64/56)³ = 1,49×`.
Bir çarpışmanın ürettiği salınım bundan **çok** büyüktür. Bu modül aralığı
gerçek salınımı **içerecek** kadar açıyor.

> Bu, KAYIT-029'un dersinin doğrudan uygulanmasıdır: *"bir büyüklüğün nasıl
> davrandığını, ilgilenilen çalışma noktasını içermeyen bir aralıkta ölçerek
> söyleyemezsin."* Orada aralık `r_dep/r_şok` idi, KAYIT-033'te
> `r_iç/r_dış`; burada `N_komşu`.
"""
from __future__ import annotations

import numpy as np

__all__ = ["neighbour_count", "OMEGA_IS_UNITY_WHEN_H_FIXED",
           "measure_density_swing", "run_fixed_h_sweep", "judge"]

#: `h` sabitken `Ω ≡ 1` **tam olarak** — türetim gereği, ölçüm gereği değil.
#: Bu bir yaklaşıklık değil: `∂h/∂ρ = 0` çarpanı terimi **kapatır**.
OMEGA_IS_UNITY_WHEN_H_FIXED = True

#: Wendland C2 desteği `2h` — `kernel_margin.SUPPORT_OVER_H` ile aynı kaynak.
from .kernel_margin import SUPPORT_OVER_H  # noqa: E402


def neighbour_count(rho, h, m) -> np.ndarray:
    """Küresel destek içindeki beklenen komşu sayısı: `(4/3)π(2h)³·ρ/m`.

    Kenar parçacıkları için **fazla** tahmin eder; iç bölgede doğrudur.
    Ölçümlerde yalnızca iç bölge kullanılır (D1 kuralı).
    """
    rho = np.asarray(rho, dtype=np.float64)
    h = np.asarray(h, dtype=np.float64) if not np.isscalar(h) else float(h)
    m = np.asarray(m, dtype=np.float64) if not np.isscalar(m) else float(m)
    hacim = (4.0 / 3.0) * np.pi * (SUPPORT_OVER_H * h) ** 3
    return hacim * rho / m


def measure_density_swing(n_side: int, device: str, t_end: float | None = None,
                          ic_frac: float = 0.6) -> dict:
    """Gerçek bir Sedov koşusunda `ρ` (dolayısıyla `N_komşu`) **ne kadar** salınıyor.

    Bu, deneyin **çalışma noktasını** verir: taramanın hangi aralığı
    kapsaması gerektiğini ölçümden öğreniriz, tahminden değil.

    Kenar dışlanır (`ic_frac`): yüzeydeki eksik komşuluk yapay bir düşük
    yoğunluk üretir ve salınımı olduğundan büyük gösterir.
    """
    from ..cpu_reference.sph_ref import RefParams
    from ..warp_core.solver import WarpSPH3D
    from .sedov import GAMMA, T_END_DEFAULT, build_sedov_ic

    t_end = float(T_END_DEFAULT if t_end is None else t_end)
    ic = build_sedov_ic(n_side)
    h = float(ic["h"])
    m0 = float(np.median(ic["m"]))
    sol = WarpSPH3D(ic["x"], ic["v"], ic["m"], ic["u"], h,
                    RefParams(gamma=GAMMA), device=device)
    # `state_numpy()` yapicidan hemen sonra SIFIR yogunluk dondurur -- rho
    # bir degerlendirme yapilmadan hesaplanmaz. Ilk kosumda bu atlandi ve
    # `rho_ilk_ortanca = 0.0` raporlandi. Sifir bir olcum degildir.
    sol._eval()
    rho0 = sol.state_numpy()["rho"].copy()
    if float(np.median(rho0)) <= 0.0:
        raise RuntimeError("baslangic yogunlugu sifir -- _eval() calismadi")
    diag = sol.run(t_end, max_steps=500_000)
    if diag["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(
            f"t_end'e ULASILAMADI: {diag['t_end']:.6g} < {t_end:.6g}")
    st = sol.state_numpy()
    # Ic bolge: kutu yari-genisliginin ic_frac'i icinde kalanlar.
    yari = float(np.max(np.abs(ic["x"])))
    ic_maske = np.max(np.abs(st["x"]), axis=1) <= ic_frac * yari
    if int(ic_maske.sum()) < 32:
        raise RuntimeError(f"ic bolgede yalnizca {int(ic_maske.sum())} parcacik")
    rho_son = st["rho"][ic_maske]
    n0 = neighbour_count(float(np.median(rho0[ic_maske])), h, m0)
    return {"n_side": n_side, "h": h, "t_end": t_end,
            "n_ic": int(ic_maske.sum()),
            "rho_ilk_ortanca": float(np.median(rho0[ic_maske])),
            "rho_son_en_kucuk": float(np.min(rho_son)),
            "rho_son_en_buyuk": float(np.max(rho_son)),
            "rho_son_p01": float(np.percentile(rho_son, 1.0)),
            "rho_son_p99": float(np.percentile(rho_son, 99.0)),
            "N_komsu_ilk": float(n0),
            "N_komsu_p01": float(neighbour_count(
                float(np.percentile(rho_son, 1.0)), h, m0)),
            "N_komsu_p99": float(neighbour_count(
                float(np.percentile(rho_son, 99.0)), h, m0)),
            "salinim_p99_p01": float(np.percentile(rho_son, 99.0)
                                     / max(np.percentile(rho_son, 1.0), 1e-300))}


def run_fixed_h_sweep(h_absolute: float, n_sides, device: str,
                      t_end: float | None = None) -> list[dict]:
    """`h` **sabit**, `dx` taranıyor: çözülen ölçek sabit, `N_komşu` değişiyor.

    Her satır bir `n_side`. `N_komşu ∝ (h/dx)³` olduğu için `n_side`
    iki katına çıktığında komşu sayısı **8 katına** çıkar.
    """
    from .resolution_scaling import run_single
    from .sedov import T_END_DEFAULT

    t_end = float(T_END_DEFAULT if t_end is None else t_end)
    satirlar = []
    for n in n_sides:
        r = run_single(int(n), float(h_absolute), device, t_end=t_end)
        # Tekduze kafeste ortalama yogunluk ~ m/dx^3 -> N_komsu = (4/3)pi(2h/dx)^3
        r["N_komsu"] = float((4.0 / 3.0) * np.pi
                             * (SUPPORT_OVER_H * r["h"] / r["dx"]) ** 3)
        r["hata"] = abs(r["r_measured"] - r["r_exact"]) / r["r_exact"]
        satirlar.append(r)
    return satirlar


def judge(satirlar: list[dict], swing: dict | None = None,
          tol: float = 0.02) -> dict:
    """Plato `N_komşu` ile **kayıyor mu**?

    Ölçüt: **yalnızca çalışma aralığındaki** noktaların göreli yayılımı.
    Aralık dışındaki noktalar (`N_komşu < p01`) eğriyi görmek için
    koşulur ama yargıya **girmez** — orada baskın olan `dx` yakınsaması,
    çalışma noktasında olmayan bir hatadır.

    Yayılım bir **üst sınırdır**: `dx` yakınsaması ile komşu sayısı bu
    deneyde ayrılamaz (modül başlığındaki uyarı). Toplam tolerans
    altındaysa komşu sayısının payı da altındadır.

    `swing` verilirse, taramanın gerçek salınımı **kapsayıp kapsamadığı**
    da raporlanır — kapsamıyorsa yargı `belirsiz`dir (KAYIT-029/033'ün
    dersi: çalışma noktasını içermeyen aralıkta yargı kurulmaz).
    """
    if len(satirlar) < 3:
        return {"karar": "belirsiz", "neden": "en az 3 nokta gerekir"}
    r = np.array([s["r_measured"] for s in satirlar], dtype=np.float64)
    nk = np.array([s["N_komsu"] for s in satirlar], dtype=np.float64)
    sonuc = {"N_komsu_min": float(nk.min()), "N_komsu_max": float(nk.max()),
             "N_komsu_orani": float(nk.max() / nk.min()),
             "tum_yayilim": float((r.max() - r.min()) / np.median(r)),
             "tol": float(tol)}
    if swing is None:
        sonuc["r_yayilim"] = sonuc["tum_yayilim"]
        sonuc["karar"] = ("sabit_h_yeterli" if sonuc["r_yayilim"] < tol
                          else "uyarlamali_h_gerekli")
        sonuc["sabit_h_yeterli"] = bool(sonuc["r_yayilim"] < tol)
        return sonuc

    alt, ust = float(swing["N_komsu_p01"]), float(swing["N_komsu_p99"])
    kapsiyor = (nk.min() <= alt) and (nk.max() >= ust)
    sonuc["gereken_N_komsu"] = [alt, ust]
    sonuc["aralik_kapsiyor"] = bool(kapsiyor)
    if not kapsiyor:
        sonuc["karar"] = "belirsiz"
        sonuc["neden"] = ("tarama gercek salinimi KAPSAMIYOR; "
                          "calisma noktasi disinda yargi kurulmaz")
        return sonuc

    # Yargi YALNIZCA calisma araligindaki noktalardan kurulur.
    ic = (nk >= alt) & (nk <= ust)
    if int(ic.sum()) < 2:
        sonuc["karar"] = "belirsiz"
        sonuc["neden"] = (f"calisma araliginda yalnizca {int(ic.sum())} nokta "
                          f"var; en az 2 gerekir")
        return sonuc
    r_ic = r[ic]
    yayilim = float((r_ic.max() - r_ic.min()) / np.median(r_ic))
    sonuc["calisma_nokta_sayisi"] = int(ic.sum())
    sonuc["r_yayilim"] = yayilim
    sonuc["sabit_h_yeterli"] = bool(yayilim < tol)
    sonuc["karar"] = "sabit_h_yeterli" if yayilim < tol else "uyarlamali_h_gerekli"
    return sonuc
