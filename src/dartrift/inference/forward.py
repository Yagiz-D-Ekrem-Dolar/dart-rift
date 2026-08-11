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

`ileri_kosu` (tek aşamalı) GPU'da **koşulmadı**. Yapısı
`scripts/faz44_dart_yakinsama.py`'deki koşulmuş döngüyle aynı tutuldu
ama bu bir kanıt değildir.

`ileri_kosu_ikiasama` **koştu** (2026-08-10, FAZ 4.11/4.12): iki kez
9 nokta, `0/9` düşen. Yani iki aşamalı yol artık kanıtlı.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sahne_parametreleri", "gozlenebilirleri_cikar", "ileri_kosu",
           "ileri_kosu_ikiasama",
           "GOZLENEBILIRLER"]

#: Gözlenebilir adları — `gozlenebilirleri_cikar` bu **sırada** döner.
#:
#: ## `krater_capi` → `krater_derinlik` (2026-08-10, ADR-0045 §8/§10)
#:
#: Çap **ölçümle ölü** çıktı: FAZ 4.11'in dokuz köşesinde de `0`, ve
#: `faz48_v2`'nin 82 örneğinde yalnızca **iki değer** (`6,93` / `12,00`).
#: Ölçtüğü şey çap değil, `depth_threshold` geçişi.
#:
#: Derinlik ise `kutulama = "eksen"` düzeltmesinden sonra **yaşıyor**:
#: bağıl yayılım `%20,7` (çap `0`, `β` `%2,0`) ve sentetik kraterde
#: `2/5/10 m → 2,015/4,882/9,660`.
#:
#: > Ölü bir sütun sessiz bir arıza: `fit_surrogate` onu `sabit` diye
#: > işaretler, `guvenilir=False` döner ve koşucu **DURDURULDU** der.
#: > Yani çapı bırakmak FAZ 4.6'yı hiç koşturmamak demekti.
GOZLENEBILIRLER = ("beta", "krater_derinlik", "ejekta_kutle_kesri")


def sahne_parametreleri(theta, taban: dict | None = None, *,
                        secenek3: bool = True) -> dict:
    """`θ = (α₀, Y₀, f_boulder)` → `build_scene` argümanları.

    `α₀` ve `Y₀` **matris** malzemesine uygulanır; kaya blokları
    (boulder) FAZ 3'te ayrı parametrelerle tanımlıdır ve **çıkarımın
    parçası değildir** — onları da serbest bırakmak parametre sayısını
    beşe çıkarırdı ve ızgara posterior o boyutta pahalılaşır.

    .. note::
       **ADR-0044 (KABUL EDİLDİ) sonrası varsayılan Seçenek 3'tür.**
       `θ₀` artık `boulder_alpha0`; `matrix_alpha0` **verilmez** ve
       üretici onu `ρ_yığın`dan türetir.

       Eski eşleme (`secenek3=False`) `ρ_yığın` ile **tutarsızdı**:
       serbest `matrix_alpha0` verilince üretici hedef yoğunluğu
       tutturamadığı için **reddediyordu** — FAZ 4.6 duman testinde
       `29/29` nokta bu yüzden düştü. Yol **silinmedi** ki karar geri
       alınabilsin.

    Parameters
    ----------
    secenek3
        `False` verilirse ADR-0044 **öncesi** eşleme kullanılır
        (`θ₀ → matrix_alpha0`). Yalnızca karşılaştırma/gerileme için.
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
    if secenek3:
        # ADR-0044 SECENEK 3 (ONERI, kilitli DEGIL): birinci bilesen
        # `boulder_alpha0`. `matrix_alpha0` VERILMIYOR -> uretici onu
        # `ρ_yigin`dan turetiyor, boylece ADR-0030 kisiti bozulmuyor.
        kw = dict(taban or {})
        kw.update(boulder_alpha0=a0, matrix_Y0=y0, f_boulder=fb)
        kw.pop("matrix_alpha0", None)
        return kw
    kw = dict(taban or {})
    kw.update(matrix_alpha0=a0, matrix_Y0=y0, f_boulder=fb)
    return kw


#: DART geometrisi icin krater cikarici ayarlari.
#:
#: ## Iki kez yanlis yazdim; ucuncusu OLCUMLE dogrulandi
#:
#: **1. surum** `n_theta = 64`: `surface_particles` `cos(theta)`da esit
#: kutular kullanir, kutup kutusu `14,36 deg` ve `D = 20 m` kraterin
#: yari-acisi `7,00 deg` -- krater TEK KUTUYA sigiyordu. Gercek derinlik
#: `2 -> 12 m` degisirken olculen **sabit `1,1975`** (rapor A13).
#:
#: **2. surum** `n_theta = 1024`: kutup kutusu `3,58 deg` oldu ama izgara
#: (`131 072`) parcacik sayisini (`10 410`) GECTI. Olculdu (A16):
#:
#:     n_theta =   16 -> "yuzey" 512/10410,  medyan r = 81,26 (gercek 81,94)
#:     n_theta = 1024 -> "yuzey" 9970/10410, medyan r = 66,91, p10 = 39,34
#:
#: Her parcacik kendi kutusunun "en disi" olur ve **yuzey = butun cisim**.
#: Krateri "goruyor" ama olctugu sey yuzey DEGIL. Kabuk testlerimde
#: gecmesinin sebebi kabukta her parcacigin zaten yuzeyde olmasiydi.
#:
#: Iki gereksinim CELISIYOR ve `10 410` parcacikla ayni anda saglanamaz:
#: kutup kutusu `< 7 deg` icin `n_theta > 256`, kutu basina `~12`
#: parcacik icin `n_theta ~ 20`.
#:
#: **3. surum (bu)** `kutulama = "eksen"`: kuresel izgara HIC
#: kullanilmiyor; parcaciklar carpma ekseninden aciya gore esit acili
#: halkalara bolunuyor. Uretim sahnesinde olculdu (`lam = 2`, ek maliyet
#: YOK; kuresel kip ayni sahnede dokuz ayarin hepsinde REDDEDIYORDU):
#:
#:     gercek   nb=4    nb=6    nb=8
#:     2 m     1,844   1,977   2,015
#:     5 m     4,340   4,793   4,882
#:    10 m     8,499   9,486   9,660
#:
#: Kutu sayisi arttikca gercege TEK DUZE yaklasiyor. Gurultu tabani
#: `0,25 m` (yuzey gurultusu `0,2 m` iken).
#:
#: `n_theta`/`n_phi` ARTIK VERILMIYOR: eksen kipinde kullanilmiyorlar ve
#: birakmak "ayarlanmis" izlenimi verirdi.
#:
#: > Cap bu ayarlarla da OLU: olculen sey esik gecisi, cap degil
#: > (ADR-0045 §5). Yasayan gozlenebilir DERINLIK.
KRATER_AYARLARI_DART = {"outer_angle_deg": 12.0, "n_bins": 8,
                        "kutulama": "eksen", "yuzdelik": 95.0,
                        "ejekta_yaricap_carpani": 1.05}

#: A13'un (yanlis) gerekcesinin olcusu — testler `n_theta = 64`'un neden
#: yetmedigini kilitliyor. Eksen kipinde bu esik ARTIK BAGLAYICI DEGIL.
KRATER_KUTUP_KUTUSU_ESIGI_DEG = 7.0


def gozlenebilirleri_cikar(st: dict, *, impactor_momentum, target_mass,
                           target_radius, is_impactor, impact_direction,
                           x_reference, krater_ayarlari=None) -> np.ndarray:
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
        x_reference=np.asarray(x_reference, dtype=np.float64)[hedef],
        **(krater_ayarlari or {}))
    y = np.array([float(mt.beta), float(kr.depth),
                  float(mt.ejecta_fraction)], dtype=np.float64)
    if not np.all(np.isfinite(y)):
        raise RuntimeError(
            f"gozlenebilirlerden biri sonlu degil: "
            f"{dict(zip(GOZLENEBILIRLER, y))}")
    return y


def ileri_kosu(x, *, material, device: str, steps: int, r_ince: float,
               spacing: float, lam: int, sahne_taban: dict,
               ilerleme=None,
               krater_ayarlari=KRATER_AYARLARI_DART) -> np.ndarray:
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
            # ERKEN IPTAL: patlamayi kosu SONUNDA anlamak, her noktasi
            # pahali olan bir tasarimda bosa GPU demektir. 100 adimda bir
            # sonluluk sinaniyor; patlarsa o nokta nan kalir ve SIRADAKI
            # noktaya gecilir.
            kontrol = max(1, steps // 30)
            for adim in range(1, steps + 1):
                sol.step(sol.compute_dt())
                if adim % kontrol == 0:
                    if not np.all(np.isfinite(sol.state_numpy()["v"])):
                        raise RuntimeError(
                            f"kosu PATLADI adim {adim}/{steps} -- kalan "
                            f"{steps - adim} adim BOSA harcanmadi")
            Y[i] = gozlenebilirleri_cikar(
                sol.state_numpy(), impactor_momentum=rs.impactor_momentum,
                target_mass=rs.target_mass, target_radius=rs.target_radius,
                is_impactor=rs.is_impactor,
                impact_direction=rs.impact_direction, x_reference=x0,
                krater_ayarlari=krater_ayarlari)
        except (RuntimeError, ValueError) as e:
            if ilerleme:
                ilerleme(i, len(x), f"DUSTU: {e}")
            continue
        if ilerleme:
            ilerleme(i, len(x), " ".join(
                f"{a}={v:.5g}" for a, v in zip(GOZLENEBILIRLER, Y[i])))
    return Y


def ileri_kosu_ikiasama(x, *, material, device: str, t1: float, t_end: float,
                        r1: float, lam1: float, r2: float, lam2: float,
                        spacing: float, sahne_taban: dict,
                        azami_adim: int = 200000, ilerleme=None,
                        krater_ayarlari=KRATER_AYARLARI_DART,
                        durum_kaydi=None) -> np.ndarray:
    """İki aşamalı ileri model — **çözülmüş mermiyle**.

    ## Neden gerekli

    Tek aşamalı (`λ=2`) ileri modelde mermi çözülmemiş (`A1 = 0,215`,
    `h`/çap `= 9,32`) ve ölçüldü ki bu **niteliksel** bir fark yaratıyor:

    | | `λ = 2` | iki aşama (`A1 = 2,04`) |
    |---|---|---|
    | `n_ejekta` | **803** = merminin tamamı | **28** |
    | `β` | 1,617583 | 1,411216 |

    `803`, mermi parçacıklarının **tümü**: çözülmemiş mermi **tamamen
    sekiyor**. Çözülmüşte gömülüyor. Yani tek aşamalı ileri model
    **başka bir problemi** çözüyor (ADR-0043 §4g).

    ## Aşama-1 **üç seviyeli** olmak zorunda

    İki seviyelide `t₁`'de momentumun `%69`'u ince bölgenin dışında
    kalıyor ve aktarımda atılıyordu (`momentum_kapanis = 0,690`).
    Üç seviyelide `5,10e-15` (ADR-0043 §4f).

    > Düşen nokta **atlanmaz**: `nan` döner ve çağıran taraf sayar.

    ## `durum_kaydi` neden var

    `durum_kaydi(i, theta, st, sahne, x_referans, a1)` verilirse her noktanın
    **son durumu** çağırana geçer. Bu bir kolaylık değil, ölçülmüş bir
    ihtiyaç: bu turda **üç kez** kaydedilmiş bir duruma ihtiyaç duydum
    (`kacis_bekleyenler`, krater çıkarıcı sınırları, `Y0` duyarlılığı) ve
    elimde yalnızca özet vardı — her seferinde saatlerce yeniden koşmak
    gerekti. Diziler `~1 MB`, koşu saatler.

    > Yeni bir gözlenebilir sorusu **koşu gerektirmemeli**.
    """
    from ..cpu_reference.sph_ref import RefParams
    from ..setup.refine import refine_scene_ucseviye
    from ..setup.scene import _build_mesh, build_scene
    from ..setup.two_stage import asama2_sahnesi_ucseviye
    from ..warp_core.solver_solid import WarpSolid3D

    x = np.atleast_2d(np.asarray(x, dtype=np.float64))
    Y = np.full((len(x), len(GOZLENEBILIRLER)), np.nan)
    if not (0.0 < t1 < t_end):
        raise ValueError(f"0 < t1 < t_end gerekir; t1={t1}, t_end={t_end}")

    def _ilerlet(sol, t_bas, t_hedef, etiket):
        t = float(t_bas)
        kontrol = max(1, azami_adim // 200)
        for adim in range(1, azami_adim + 1):
            dt = sol.compute_dt()
            if t + dt > t_hedef:
                dt = t_hedef - t
            sol.step(dt)
            t += dt
            if adim % kontrol == 0 and not np.all(
                    np.isfinite(sol.state_numpy()["v"])):
                raise RuntimeError(f"{etiket} PATLADI (adim {adim})")
            if t >= t_hedef * (1.0 - 1e-12):
                return t
        raise RuntimeError(f"{etiket}: {azami_adim} adimda {t_hedef}'e "
                           f"varilamadi (t={t:.4e})")

    for i, th in enumerate(x):
        kw = sahne_parametreleri(th, sahne_taban)
        try:
            kaba = build_scene(spacing=spacing, device="cpu", **kw)
            mesh = _build_mesh("icosphere",
                               radius=float(sahne_taban["radius"]), subdiv=4)
            a1 = refine_scene_ucseviye(kaba, mesh, r1=r1, lam1=lam1,
                                       r2=r2, lam2=lam2)
            sol1 = WarpSolid3D(
                np.ascontiguousarray(a1.x), np.ascontiguousarray(a1.v),
                np.ascontiguousarray(a1.m), np.zeros(a1.n), a1.h, material,
                RefParams(cfl=0.25), alpha0=np.ascontiguousarray(a1.alpha0),
                Y0=np.ascontiguousarray(a1.Y0), device=device,
                check_every=10 ** 9)
            _ilerlet(sol1, 0.0, t1, "asama-1")
            sahne = asama2_sahnesi_ucseviye(a1, sol1.state_numpy())
            # KRATER REFERANSI: aktarim sonrasi konumlar. Aktarim parcacik
            # kimliklerini degistirdigi icin asama-1'in t=0 konumlari
            # KULLANILAMAZ; olculen sey "t1 -> t_end degisimi".
            x0 = np.array(sahne.x, dtype=np.float64, copy=True)
            sol2 = WarpSolid3D(
                np.ascontiguousarray(sahne.x), np.ascontiguousarray(sahne.v),
                np.ascontiguousarray(sahne.m), np.ascontiguousarray(sahne.e),
                sahne.h, material, RefParams(cfl=0.25),
                alpha0=np.ascontiguousarray(sahne.alpha0),
                Y0=np.ascontiguousarray(sahne.Y0), device=device,
                check_every=10 ** 9)
            _ilerlet(sol2, t1, t_end, "asama-2")
            st_son = sol2.state_numpy()
            if durum_kaydi is not None:
                durum_kaydi(i, th, st_son, sahne, x0, a1)
            Y[i] = gozlenebilirleri_cikar(
                st_son, impactor_momentum=a1.impactor_momentum,
                target_mass=a1.target_mass, target_radius=a1.target_radius,
                is_impactor=sahne.is_impactor,
                impact_direction=a1.impact_direction, x_reference=x0,
                krater_ayarlari=krater_ayarlari)
            if ilerleme:
                ilerleme(i, len(x), f"tamam (A1 gecti, N={sahne.n})")
        except (RuntimeError, ValueError, KeyError) as e:
            if ilerleme:
                ilerleme(i, len(x), f"DUSTU: {e}")
    return Y
