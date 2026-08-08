"""İleri model — parametre noktası → gözlenebilirler.

## Neden üç parçaya ayrıldı

Tek bir `ileri_kosu(θ) -> y` fonksiyonu yazmak kolay olurdu ama **hiç
sınanamazdı**: içinde GPU koşusu var. Oysa o fonksiyonun yaptığı işin
çoğu GPU'suz sınanabilir:

| parça | ne yapar | GPU'suz sınanır mı |
|---|---|---|
| `sahne_parametreleri` | `θ` → `build_scene` argümanları | **evet** |
| `gozlenebilirleri_cikar` | son durum → üç sayı | **evet** |
| `ileri_kosu` | ikisini bağlar + çözücüyü koşturur | hayır |

Ortadaki iki parça yanlışsa — örneğin `Y₀` yanlış alana yazılırsa —
bütün tasarım **aynı** sahneyi koşturur ve vekil sabit bir yüzey öğrenir.
Posterior o zaman önseli döndürür ve C2 düşer; ama **nedenini** anlamak
saatler alırdı. Bu ayrım o hatayı saniyede yakalar.

> Bu, S9'un dersinin uygulanmasıdır: doğrulanamayan bir kod yolu
> mümkün olduğunca **küçültülür**.

## Doğrulanmamış olan

`ileri_kosu`'nun GPU kısmı **koşulmadı** — TRUBA kotası dolu
(`7.200.096 / 7.200.000 cpu-dk`; 1 dakikalık `echo` işi bile
`AssocGrpCPUMinutesLimit` ile bloke). Yapısı
`scripts/faz44_dart_yakinsama.py`'deki **koşulmuş** döngüyle aynı
tutuldu, ama bu bir kanıt değildir ve öyle sunulmuyor.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sahne_parametreleri", "gozlenebilirleri_cikar", "ileri_kosu",
           "GOZLENEBILIRLER"]

#: Gözlenebilir adları — `gozlenebilirleri_cikar` bu **sırada** döner.
GOZLENEBILIRLER = ("beta", "krater_capi", "ejekta_kutle_kesri")


def sahne_parametreleri(theta, taban: dict | None = None) -> dict:
    """`θ = (α₀, Y₀, f_boulder)` → `build_scene` argümanları.

    `α₀` ve `Y₀` **matris** malzemesine uygulanır; kaya blokları
    (boulder) FAZ 3'te ayrı parametrelerle tanımlıdır ve **çıkarımın
    parçası değildir** — onları da serbest bırakmak parametre sayısını
    beşe çıkarırdı ve ızgara posterior o boyutta pahalılaşır.
    """
    theta = np.asarray(theta, dtype=np.float64).ravel()
    if theta.shape != (3,):
        raise ValueError(f"theta (3,) olmalı, {theta.shape} geldi")
    a0, y0, fb = float(theta[0]), float(theta[1]), float(theta[2])
    if not (1.0 <= a0):
        raise ValueError(f"alpha0 >= 1 olmalı, {a0} geldi")
    if y0 <= 0.0:
        raise ValueError(f"Y0 pozitif olmalı, {y0} geldi")
    if not (0.0 <= fb <= 1.0):
        raise ValueError(f"f_boulder [0,1] içinde olmalı, {fb} geldi")
    kw = dict(taban or {})
    kw.update(matrix_alpha0=a0, matrix_Y0=y0, f_boulder=fb)
    return kw


def gozlenebilirleri_cikar(st: dict, *, impactor_momentum, target_mass,
                           target_radius, is_impactor, impact_direction,
                           x_reference) -> np.ndarray:
    """Son durumdan üç gözlenebilir — `GOZLENEBILIRLER` sırasında.

    Patlamış bir koşu **sessizce** sayı döndürmez: `nan` görünürse
    `RuntimeError`. S4'ün dersi — donmuş/özdeş değerler NaN'ın imzasıydı
    ve fark edilmesi uzun sürmüştü.

    ## `x_reference` **zorunludur** — R4 kapanıyor

    `DURUM-DEGERLENDIRMESI` §3'ün R4 riski: *"krater çıkarımı gerçek
    koşuya bağlanınca `x_reference` zorunlu yapılmalı."* Verilmezse
    `crater_profile` cismi **küre** varsayar ve şekli krater diye ölçer —
    kratersiz bir Dimorphos elipsoidinde `66,76 m` çap ölçülmüştü.
    Burada isteğe bağlı bırakmıyorum: `None` gelirse **hata**.
    """
    from ..observables.crater_shape import crater_profile
    from ..observables.momentum_transfer import escape_speed, momentum_transfer

    if x_reference is None:
        raise ValueError(
            "x_reference ZORUNLU (R4): verilmezse crater_profile cismi kure "
            "varsayar ve SEKLI krater diye olcer")
    for ad in ("x", "v", "m", "rho"):
        if not np.all(np.isfinite(st[ad])):
            raise RuntimeError(
                f"kosu PATLADI: `{ad}` sonlu degil "
                f"({int(np.count_nonzero(~np.isfinite(st[ad])))} parcacik)")

    hedef = ~np.asarray(is_impactor, dtype=bool)
    v_kacis = escape_speed(float(target_mass), float(target_radius))
    mt = momentum_transfer(st["x"], st["v"], st["m"],
                           impactor_momentum=impactor_momentum,
                           center=np.zeros(3), target_mass=float(target_mass),
                           target_radius=float(target_radius),
                           control_radius=2.0 * float(target_radius),
                           speed_threshold=v_kacis)

    kr = crater_profile(
        st["x"][hedef], center=np.zeros(3),
        impact_direction=np.asarray(impact_direction, dtype=np.float64),
        reference_radius=float(target_radius),
        x_reference=np.asarray(x_reference, dtype=np.float64)[hedef])
    y = np.array([float(mt.beta), float(kr.diameter),
                  float(mt.ejecta_fraction)], dtype=np.float64)
    if not np.all(np.isfinite(y)):
        raise RuntimeError(
            f"gozlenebilirlerden biri sonlu degil: "
            f"{dict(zip(GOZLENEBILIRLER, y))}")
    return y


def ileri_kosu(x, *, material, device: str, steps: int, r_ince: float,
               spacing: float, lam: int, sahne_taban: dict,
               ilerleme=None) -> np.ndarray:
    """Tasarımın her noktası için bir GPU koşusu.

    .. warning::
       **Bu fonksiyonun GPU kısmı koşulmadı.** TRUBA kotası dolu olduğu
       için tek bir gerçek koşuyla bile doğrulanamadı. Yapısı
       `faz44_dart_yakinsama.py`'deki koşulmuş döngüyle aynı tutuldu ama
       bu bir kanıt değildir.

       Patlayan bir nokta **atlanmaz**: satır `nan` yazılır ve çağıran
       taraf onu görür. Sessizce düşürmek tasarımı seyreltir ve vekil
       farkına varmaz.
    """
    from ..cpu_reference.sph_ref import RefParams
    from ..setup.refine import refine_scene
    from ..setup.scene import build_scene
    from ..warp_core.solver_solid import WarpSolid3D

    x = np.atleast_2d(np.asarray(x, dtype=np.float64))
    Y = np.full((len(x), len(GOZLENEBILIRLER)), np.nan)
    for i, th in enumerate(x):
        kw = sahne_parametreleri(th, sahne_taban)
        try:
            kaba = build_scene(spacing=spacing, device="cpu", **kw)
            ince = build_scene(spacing=spacing / lam, device="cpu", **kw)
            rs = refine_scene(kaba, ince, r_ince=r_ince)
            # CARPMA ONCESI konumlar -- krater icin ZORUNLU (R4).
            x0 = np.array(rs.x, dtype=np.float64, copy=True)
            sol = WarpSolid3D(
                np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
                np.ascontiguousarray(rs.m), np.zeros(rs.n), rs.h, material,
                RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
                Y0=np.ascontiguousarray(rs.Y0), device=device,
                check_every=10 ** 9)
            for _ in range(steps):
                sol.step(sol.compute_dt())
            Y[i] = gozlenebilirleri_cikar(
                sol.state_numpy(), impactor_momentum=rs.impactor_momentum,
                target_mass=rs.target_mass, target_radius=rs.target_radius,
                is_impactor=rs.is_impactor,
                impact_direction=rs.impact_direction, x_reference=x0)
        except (RuntimeError, ValueError) as e:
            if ilerleme:
                ilerleme(i, len(x), f"DUSTU: {e}")
            continue
        if ilerleme:
            ilerleme(i, len(x), " ".join(
                f"{a}={v:.5g}" for a, v in zip(GOZLENEBILIRLER, Y[i])))
    return Y
