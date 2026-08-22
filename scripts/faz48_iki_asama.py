"""FAZ 4.8 — **iki aşamalı koşu**: `A1`'i geçirmenin tek yolu.

G4 kapısının düşen **tek** ölçütü `A1 = 0,215` (eşik `2,0`): mermi
çözülmemiş. Tek çözüm `λ ≈ 19` ve tek uygulanabilir yol ADR-0043'ün
iki aşamalı şeması.

```
aşama-1   λ=19, r_iç=3 m    0 → t₁ = 4,767e-3 s     A1 = 2,04 ✔
   ↓      Lagrange'cı kabalaştırma (ADR-0043 §4d)
aşama-2   λ=2,  r_iç=25 m   t₁ → t_end              ensemble bedeli
```

## Ne ölçülüyor

| | |
|---|---|
| `A1` | **aşama-1'den** — mermi orada çözülmüş olmalı |
| `β` | **aşama-2'nin sonundan** |
| kütle/momentum/enerji | aktarımda korunuyor mu |
| komşu sağlığı | aşama-2 aktarılanları SPH ile ilerletebiliyor mu |

## Tek aşamalı kontrol kolu **zorunlu**

`--tek-asama` aynı `t_end`'e `λ=2` ile tek başına gider. İki koşunun
`β`'sı karşılaştırılmadan iki aşamanın *"işe yaradığı"* söylenemez —
yalnızca *"koştuğu"* söylenebilir.

> Beklenti: `β` **değişmeli**. Değişmezse mermiyi çözmek `β`'yı
> etkilemiyor demektir ve o zaman `A1` eşiğinin kendisi sorgulanmalı
> (ADR-0026'ya geri dönülür).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402
from dartrift.observables.momentum_transfer import escape_speed, momentum_transfer  # noqa: E402
from dartrift.setup.refine import refine_scene_local, refine_scene_ucseviye  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402
from dartrift.setup.two_stage import asama2_sahnesi_ucseviye  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402

#: FAZ 4.5'in ölçtüğü bağlanma süresi (`faz43c`, ADR-0043 §4a).
T1_OLCULEN = 4.767e-3


def _mat(gozeneksiz: bool = False, yercekimli: bool = False,
         hasarli: bool = False):
    """Malzeme; `gozeneksiz` ise **P-α kapalı**.

    Tanı amaçlı: gözeneklilik şok enerjisini **gözenek çökmesine**
    yutuyorsa krater kazılmaz. Kapatınca krater oluşuyorsa hipotez
    doğrulanır. Bu bir model değişikliği **değil**, ayırt edici bir
    kontrol koludur.

    ## Tek başına YETMEZ — `_sahne_kolu` ile birlikte kullanılmalı

    Süreklilik yönteminde başlangıç yoğunluğu `rho0 / alpha0`'dır
    (`solver_solid.py:133`) ve bu **gözeneklilik kapalıyken de** öyle
    kalır. Yani `alpha0 = 1,30`'luk bir sahnede P-α'yı kapatmak cismi
    `rho = 2077`'de, yani **genişlemiş** halde bırakır. Ölçüldü:

    | `alpha0` | `P` gözenekli | `P` **gözeneksiz** |
    |---|---|---|
    | 1,15 | `0` | **`-3,03e9` Pa** |
    | 1,30 | `0` | **`-4,74e9` Pa** |

    `-4,7 GPa` gerilme cismi daha `t = 0`'da parçalar. O kol ejekta
    üretseydi *"gözeneklilik enerjiyi yutuyormuş"* diye okunurdu — oysa
    cisim yalnızca kendi başlangıç gerilmesinden patlamış olurdu.

    `_sahne_kolu` sahneyi **katı** kurarak bunu çözer; oradaki tabloya
    bakın (yalnızca `alpha0 = 1` demek de yetmiyor).
    """
    import dataclasses
    m = _malzeme()
    if yercekimli:
        # ADR-0028 yercekimini FIZIK yuzunden degil MALIYET yuzunden
        # kapatmisti: enerji hatasi birebir ayni (1,4558e-02), ama kosu
        # 15,7 kat yavas. Rapor A17 gosterdi ki bedeli agir: `beta`
        # "cisimden ne kadar momentum ayrildi" diye soruyor ve
        # yercekimsiz bir cisimde AYRILMA tanimsiz -- `v_kacis` simule
        # EDILMEYEN bir fizigin esigi. t = 20 s'de ic dolasim net
        # momentumun 250 KATI ve kinetik enerjinin %100'u ic hareket.
        m = dataclasses.replace(
            m, gravity=dataclasses.replace(m.gravity, enabled=True))
    if hasarli:
        # ADR-0027 kendi metninde soyle diyor: "`D = 0` birakmak,
        # malzemenin cekmede sinirsiz dayanikli oldugunu varsaymak
        # demekti -- krater hacmini ve dolayisiyla ejekta kutlesini,
        # yani `beta`'yi SISTEMATIK olarak kuculturdu."
        #
        # FAZ 4 boyunca `_malzeme()` hasari KAPALI tuttu, oysa
        # `configs/p3_dimorphos.yaml` `damage.enabled: true` diyor.
        # Bu bayrak ADR'nin ongordugu kolu acar; parametreler o
        # config'ten (ve `DamageParams` varsayilanlarindan) gelir.
        m = dataclasses.replace(
            m, damage=dataclasses.replace(m.damage, enabled=True))
    if not gozeneksiz:
        return m
    return dataclasses.replace(
        m, porosity=dataclasses.replace(m.porosity, enabled=False))


#: Katı bazalt yoğunluğu — gözeneksiz kolun yığın yoğunluğu.
RHO0_KATI = 2700.0


def _sahne_n_mermi(kw: dict, n_mermi: int | None) -> dict:
    """`--n-mermi` verilirse mermi parcacik sayisini ez.

    Semanin `>= 8` sarti korunur (nokta parcacik YASAK, `p3_scene.yaml`).
    """
    if n_mermi is None:
        return kw
    if n_mermi < 8:
        raise ValueError(f"n_mermi en az 8 olmali, {n_mermi} geldi")
    return {**kw, "n_impactor": int(n_mermi)}


def _sahne_kolu(gozeneksiz: bool) -> dict:
    """Gözeneksiz kolda sahne de **katı** kurulmalı; yalnızca `alpha0 = 1`
    demek YETMEZ.

    ## Neden

    Parçacık kütlesi yığın yoğunluğundan gelir (`m = rho_yigin · V`) ama
    süreklilik yönteminde `rho` **bağımsız** bir durum değişkenidir ve
    `rho0 / alpha0` ile kurulur (`solver_solid.py:133`). İkisi ayrı ayrı
    ayarlanınca uyuşmazlar:

    | kol | `m / V` | `rho` başlangıç | uyum |
    |---|---|---|---|
    | gözenekli | 1800 | 1800 | ✔ |
    | *yalnızca* `alpha0 = 1` | **1800** | **2700** | ✘ `%50` |
    | katı sahne (**bu**) | 2700 | 2700 | ✔ |

    `%50`'lik bir `ρ`–`m` uyuşmazlığı SPH'de hacim elemanını (`m/ρ`)
    bozar: parçacıklar uzayı doldurmaz ve basınç gradyanı yanlış ölçeklenir.
    İlk düzeltmem (yalnızca `alpha0 = 1`) tam bunu yapıyordu — bir tuzağı
    başkasıyla değiştirmiş oluyordu.

    ## `boulder_alpha0` da `1` olmalı

    `matrix_alpha0_for_bulk_density(2700, 2700, 1.05, 0.25)` **çözülmüyor**
    (matris distansiyonu `0,9844 < 1` çıkıyor): gözenekli bloklarla katı
    yığın yoğunluğuna ulaşılamaz. `boulder_alpha0 = 1,0` ile
    `matris_alpha0 = 1,0` tam çıkıyor.

    > Kol yine de **tek değişkenli değil**: hedef `%50` daha ağır. Bu,
    > "gözeneksiz Dimorphos"un kaçınılmaz sonucu. Karşılaştırma bu farkı
    > **belirterek** okunmalı (rapor A14).
    """
    if not gozeneksiz:
        return dict(SAHNE)
    return {**SAHNE, "bulk_density": RHO0_KATI, "boulder_alpha0": 1.0}


def _sahne_Y0(kw: dict, Y0: float | None,
              boulder_Y0: float | None = None) -> dict:
    """`--Y0` matris, `--boulder-Y0` blok mukavemetini ezer.

    ## Blok kolu neden eklendi

    Bu islev daha once YALNIZCA `matrix_Y0`'i eziyordu. `build_scene`in
    `boulder_Y0` varsayilani `1e7 Pa` ve `SAHNE` onu hic vermiyor, yani
    hedefin kutlece `%36,3`'u butun FAZ 4 boyunca -- eleme kosulari ve
    cikarim uzayinin `Y0` ekseni dahil -- `1e7 Pa`'da SABIT kaldi.

    Krater bolgesinde blok kutle payi `%7,4` ama kutle agirlikli `Y0`
    matrisin `75` kati; is `1506779`'un `1/10/100 Pa` kollari bolgenin
    ortalama mukavemetini `1,0001` kat oynatiyordu (KAYIT-050).

    Kol TRUBA'da kosuldu (is `1515196`): `matrix_Y0 = boulder_Y0 = 1 Pa`
    ve yercekimi acikken `beta` `1,05e-5` oynadi, kacan hedef kutlesi
    yine `0` (KAYIT-052).
    """
    out = dict(kw)
    if Y0 is not None:
        if Y0 <= 0.0:
            raise ValueError(f"Y0 pozitif olmali, {Y0} geldi")
        out["matrix_Y0"] = float(Y0)
    if boulder_Y0 is not None:
        if boulder_Y0 <= 0.0:
            raise ValueError(
                f"boulder_Y0 pozitif olmali, {boulder_Y0} geldi")
        out["boulder_Y0"] = float(boulder_Y0)
    return out


def _alpha0_denetle(alpha0, gozeneksiz: bool):
    """Gözeneksiz kolda sahne gerçekten katı mı — sessizce geçmesin."""
    a = np.asarray(alpha0, dtype=np.float64)
    if gozeneksiz and not np.allclose(a, 1.0, atol=1e-9):
        raise ValueError(
            f"gozeneksiz kol ama alpha0 != 1 (min {a.min():.4f}, "
            f"max {a.max():.4f}) — sahne KATI kurulmamis, cisim t=0'da "
            f"gerilmede baslar (rapor A14)")
    return a


def _cozucu(x, v, m, u, h, alpha0, Y0, device, mat=None, D0=None,
            cfl: float = 0.25):
    # Kusur tohumlamasi sahneyle AYNI koke baglanir; boylece hasarli kol
    # da yeniden uretilebilir ve "hangi tohum" sorusu tek yerde yanitlanir.
    from dartrift.warp_core.solver_solid import WarpSolid3D
    return WarpSolid3D(
        np.ascontiguousarray(x), np.ascontiguousarray(v),
        np.ascontiguousarray(m), np.ascontiguousarray(u),
        np.ascontiguousarray(h),
        mat if mat is not None else _malzeme(), RefParams(cfl=cfl),
        alpha0=np.ascontiguousarray(alpha0), Y0=np.ascontiguousarray(Y0),
        device=device, check_every=10 ** 9,
        damage_seed=int(SAHNE["root_seed"]), D0=D0)


def _kos(sol, t_bas: float, t_end: float, azami: int, etiket: str,
         ornekle=None, her: int = 0) -> float:
    """`t_end`'e kadar ilerlet; son adım **kırpılır**.

    `ornekle(adim, t, st)` verilirse her `her` adımda çağrılır.
    """
    t = float(t_bas)
    for adim in range(1, azami + 1):
        dt = sol.compute_dt()
        if t + dt > t_end:
            dt = t_end - t
        sol.step(dt)
        t += dt
        son = t >= t_end * (1.0 - 1e-12)
        if ornekle is not None and her > 0 and (adim % her == 0 or son):
            st = sol.state_numpy()
            if not np.all(np.isfinite(st["v"])):
                raise RuntimeError(f"{etiket} PATLADI (adim {adim})")
            ornekle(adim, t, st)
        elif adim % 500 == 0:
            print(f"    {etiket} adim {adim:6d}  t={t:.5e}", flush=True)
        if son:
            break
    if not np.all(np.isfinite(sol.state_numpy()["v"])):
        raise RuntimeError(f"{etiket} PATLADI (t={t:.4e})")
    # ADIM SINIRI SESSIZ KESIYORDU. Olculdu (is 1515364): `t_end = 20 s`
    # istenen kosu `azami_adim = 200000`'de durdu, `t_sim = 7,72 s` ile
    # `rc = 0` dondu ve cikti dosyasinin adi hala `_t20` idi. Yani kisa
    # kalmis bir kosu, TAM kosmus gibi kaydediliyordu.
    if t < t_end * (1.0 - 1e-9):
        raise RuntimeError(
            f"{etiket} ADIM SINIRINA TAKILDI: t = {t:.6e} s istenen "
            f"{t_end:.6e} s'nin {100 * t / t_end:.1f}%'i (azami {azami} "
            f"adim). Sessizce kisa donmek yerine duruyorum; "
            f"--azami-adim'i buyutun.")
    return t


def _iz_ornegi(st, *, hedef, R, v_esc, ehat, p_imp, x0) -> dict:
    """Krater + **balistik** `β` — `2R`'ye varis BEKLENMEDEN.

    `momentum_transfer`'in ejekta olcutu `d > 2R` istiyor ve hedef
    maddesinin oraya varmasi `~795 s` suruyor (rapor A12). Yercekimi
    kapali oldugu icin `r > R` ve `v_r > v_kacis` yeterli: o parcacik
    bir daha yavaslamaz.

    ## `n_hedef_ejekta` NASIL OKUNUR

    Aktarimdan sonra birlesik sahnede `is_impactor` **hicbir parcacikta
    yok**: mermi maddesi cekirdekle birlikte kabalastirildi ve artik
    hedeften ayirt edilmiyor (`two_stage` bunu bilerek yapiyor).

    O yuzden `n_hedef_ejekta` = **kacan HER parcacik**. Baslangicta bu
    sayi aktarilan cekirdek parcacik sayisini (`n_aktarilan`, olculen
    **32**) gecemez, cunku kacan sey merminin kendisi.

    > **Okuma olcutu: `n_hedef_ejekta > n_aktarilan` olursa GERCEK
    > hedef ejektasi baslamistir.** Altinda kaldigi surece hala
    > merminin kirintisi sayiliyor.

    ## `n_bekleyen` NEDEN BURADA

    `n_hedef_ejekta` sabit kalinca tek basina hicbir sey soylemiyor:
    "kazi suruyor, madde yolda" ile "kazi hic olmuyor" ayni sayiyi
    verir. Ikisini ayiran olcum, ICERIDE disari dogru giden madde olup
    olmadigi (`kacis_bekleyenler`). Beklemekle ogrenilemez, ama her
    ornekte bedavaya olculur — o yuzden ize KONULDU.
    """
    from dartrift.inference.forward import KRATER_AYARLARI_DART
    from dartrift.observables.crater_shape import crater_profile
    from dartrift.observables.momentum_transfer import balistik_beta, kacis_bekleyenler
    x, v, m = st["x"], st["v"], st["m"]
    # Olcut BURADA YAZILMIYOR: tek kaynak `balistik_beta`. Onceden bu
    # satirlar `faz410_firlatma_suresi.py`de de vardi ve iki kopya
    # sessizce kayabilirdi.
    d = balistik_beta(x, v, m, hedef=hedef, R=R, v_esc=v_esc,
                      ehat=ehat, p_imp=p_imp)
    kb = kacis_bekleyenler(x, v, m, hedef=hedef, R=R, v_esc=v_esc)
    d.update(n_bekleyen=kb["n_bekleyen"],
             bekleyen_kutle_kesri=kb["bekleyen_kutle_kesri"],
             t_gecis_medyan=kb["t_gecis_medyan"],
             t_gecis_min=kb["t_gecis_min"])
    try:
        # DUZELTILMIS AYARLAR (rapor A13). Varsayilan kutulama bu
        # geometride krateri OLCEMIYOR: kutup kutusu 14,36 deg, krater
        # yari-acisi 7 deg. Uzun kosuda derinlik 4,3 s boyunca ~0,1
        # okudu, sonra TEK ORNEKTE 5,33'e sicradi -- fizik degil, bir
        # kutunun gecerli hale gelmesi.
        kr = crater_profile(x[hedef], center=np.zeros(3),
                            impact_direction=ehat, reference_radius=R,
                            x_reference=x0[hedef], **KRATER_AYARLARI_DART)
        d["krater_derinlik"] = float(kr.depth)
        d["krater_cap"] = float(kr.diameter)
    except Exception as e:                                 # noqa: BLE001
        d["krater_derinlik"] = float("nan")
        d["krater_cap"] = float("nan")
        d["krater_hata"] = str(e)[:80]
    return d


def _beta(st, sahne_gibi, p_imp, m_hedef, R) -> dict:
    mt = momentum_transfer(
        st["x"], st["v"], st["m"], impactor_momentum=p_imp,
        center=np.zeros(3), target_mass=m_hedef, target_radius=R,
        control_radius=2.0 * R, speed_threshold=escape_speed(m_hedef, R))
    return {"beta": float(mt.beta), "beta_bound": float(mt.beta_from_bound),
            "n_ejekta": int(mt.n_ejecta),
            "momentum_kapanis": float(mt.momentum_closure)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--lam1", type=float, default=19.0)
    ap.add_argument("--r-ince1", type=float, default=3.0)
    ap.add_argument("--lam2", type=float, default=2.0)
    ap.add_argument("--r-ince2", type=float, default=25.0)
    ap.add_argument("--t1", type=float, default=T1_OLCULEN)
    ap.add_argument("--t-end", type=float, default=0.20)
    ap.add_argument("--azami-adim", type=int, default=200000)
    ap.add_argument("--tek-asama", action="store_true",
                    help="kontrol kolu: lam=2 ile TEK BASINA t_end'e git")
    ap.add_argument("--out", default=str(REPO.parent / "faz48_sonuc.json"))
    # IZLEME: asama-2 boyunca krater + balistik beta ornekle. FAZ 4.6'nin
    # gozlenebilirleri `t = 0,2 s`'de OLU (rapor A11/A12); ne zaman
    # canlandiklari COZULMUS mermiyle olculmeli.
    ap.add_argument("--iz-every", type=int, default=0,
                    help="asama-2'de her N adimda krater+balistik beta ornekle")
    # HIPOTEZ SINAVI: gozeneklilik enerjiyi KAZMA yerine SIKISTIRMAYA
    # goturuyor olabilir. Bu bayrak P-alpha'yi kapatir; krater o zaman
    # olusuyorsa hipotez dogrulanir (tani amacli, ADR-0043 disi).
    # ADR-0046'nin 2. eksik olcumu: Y0 hangi `t`'de gorunur olur?
    # FAZ 4.11/4.12 t = 0,2 s'de Y0'i GORMEDI (dort mertebe -> beta 0,001,
    # derinlik 0,077 m). Mukavemet kraterin GEC evresinde belirleyici
    # oldugu icin uzun kosuda gorunebilir; bu bayrak onu sinamak icin.
    ap.add_argument("--Y0", type=float, default=None,
                    help="matris Y0'i ez (Pa); ADR-0046 olcumu icin")
    # KAYIT-050: bloklarin mukavemeti FAZ 4 boyunca hic taranmadi.
    ap.add_argument("--boulder-Y0", type=float, default=None,
                    help="blok Y0'i ez (Pa); varsayilan 1e7 ve FAZ 4 "
                         "boyunca hic taranmadi (rapor A17 / KAYIT-050)")
    ap.add_argument("--yercekimli", action="store_true",
                    help="yercekimini AC (ADR-0028 maliyet yuzunden "
                         "kapatmisti; rapor A17)")
    # AYRIKLASTIRMA DUGMELERI. Bunlar "tani bayragi" degil, yakinsama
    # denetiminin taradigi eksenler: her biri BAGIMSIZ olarak sinanmali
    # (rapor A17/EK-3: yakinsama lam2'de olculup lam1'de sinanmamisti).
    ap.add_argument("--spacing", type=float, default=7.0,
                    help="kaba izgara araligi (uretim 7,0 m)")
    ap.add_argument("--cfl", type=float, default=0.25,
                    help="CFL sayisi (uretim 0,25)")
    ap.add_argument("--n-mermi", type=int, default=None,
                    help="mermi parcacik sayisi (uretim 800)")
    ap.add_argument("--gozeneksiz", action="store_true",
                    help="P-alpha gozenekliligi KAPAT (tani kontrol kolu)")
    # A17: `_malzeme()` hasari KAPALI tutuyor ama config `true` diyor ve
    # ADR-0027 bunun `beta`'yi kucultecegini ONCEDEN yazmisti. Bu bayrak
    # o kolu acar.
    ap.add_argument("--hasarli", action="store_true",
                    help="Grady-Kipp hasari AC (ADR-0027; rapor A17)")
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.8 — IKI ASAMALI KOSU (ADR-0043)", flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=a.spacing, device="cpu",
                       **_sahne_n_mermi(
                           _sahne_Y0(_sahne_kolu(a.gozeneksiz), a.Y0,
                                     a.boulder_Y0), a.n_mermi))
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    R = float(kaba.target_radius)
    t0 = time.perf_counter()

    a2 = refine_scene_local(kaba, mesh, r_ince=a.r_ince2, lam=a.lam2)
    p_imp = a2.impactor_momentum
    m_hedef = a2.target_mass

    # ---------------------------------------------------- KONTROL KOLU
    if a.tek_asama:
        print(f"\nKONTROL KOLU: tek asama, lam={a.lam2}, N={a2.n}", flush=True)
        sol = _cozucu(a2.x, a2.v, a2.m, np.zeros(a2.n), a2.h,
                      _alpha0_denetle(a2.alpha0, a.gozeneksiz), a2.Y0, a.device,
                      cfl=a.cfl,
                      mat=_mat(a.gozeneksiz, a.yercekimli, a.hasarli))
        t = _kos(sol, 0.0, a.t_end, a.azami_adim, "tek")
        st_tek = sol.state_numpy()
        b = _beta(st_tek, a2, p_imp, m_hedef, R)
        # HASAR TANISI kontrol kolunda da yaziliyor: hasar kapali kolda
        # `D` sifir dizisi doner, yani iki kol AYNI sekille okunur.
        Dt = np.asarray(st_tek["D"], dtype=np.float64)
        hasar_tek = {"acik": bool(a.hasarli), "D_ort": float(Dt.mean()),
                     "D_max": float(Dt.max()),
                     "n_tam_kirik": int(np.count_nonzero(Dt >= 0.999))}
        print(f"\n  t_sim = {t:.5e}  beta = {b['beta']:.6f}", flush=True)
        print(f"  hasar = {'ACIK' if a.hasarli else 'kapali'}  "
              f"D_ort {hasar_tek['D_ort']:.4e}  "
              f"D_max {hasar_tek['D_max']:.4f}  "
              f"tam kirik {hasar_tek['n_tam_kirik']}", flush=True)
        # SON DURUM: tek asamali kolda da post-hoc tani yapilabilsin.
        v_esc_t = escape_speed(m_hedef, R)
        ehat_t = np.asarray(p_imp) / float(np.linalg.norm(p_imp))
        np.savez_compressed(
            Path(a.out).with_suffix(".son_durum.npz"),
            x=st_tek["x"], v=st_tek["v"], m=st_tek["m"],
            x_referans=np.asarray(a2.x, dtype=np.float64),
            hedef=~np.asarray(a2.is_impactor, bool),
            mermi_kesri=np.asarray(a2.is_impactor, bool).astype(np.float64),
            R=R, v_esc=v_esc_t, ehat=ehat_t,
            p_imp=float(np.linalg.norm(p_imp)), t=t, D=Dt,
            # `u` ve `rho`: kacan maddenin SOKLANMIS olup olmadigi
            # ancak ic enerjiyle yanitlanir (olcut EK-2).
            u=st_tek["u"], rho=st_tek["rho"])
        Path(a.out).write_text(json.dumps(
            {"kip": "tek_asama", "lam": a.lam2, "N": a2.n, "t_sim": t,
             "hasar": hasar_tek,
             "duvar_s": time.perf_counter() - t0, **b}, indent=2))
        print(f"\nyazildi: {a.out}", flush=True)
        return 0

    # ---------------------------------------------------------- ASAMA 1
    # UC SEVIYELI (ADR-0043 §4f). Iki seviyelide t1'de momentumun %69'u
    # ince bolgenin DISINDA kaliyor ve aktarimda ATILIYORDU
    # (momentum kapanisi 0.690 OLCULDU).
    a1 = refine_scene_ucseviye(kaba, mesh, r1=a.r_ince1, lam1=a.lam1,
                               r2=a.r_ince2, lam2=a.lam2)
    ince1 = np.asarray(a1.is_fine, dtype=bool)
    mermi = np.asarray(a1.is_impactor, dtype=bool)
    cap = 2.0 * float(np.max(np.linalg.norm(
        a1.x[mermi] - a1.x[mermi].mean(axis=0)[None, :], axis=1)))
    A1 = cap / a1.spacing_fine
    print(f"\nASAMA-1: lam={a.lam1}, r_ic={a.r_ince1} m, N={a1.n} "
          f"(ince {int(ince1.sum())})", flush=True)
    print(f"  s_ince = {a1.spacing_fine:.4f} m", flush=True)
    print(f"  A1 = {A1:.4f}  ({'COZULMUS' if A1 >= 2.0 else 'COZULMEMIS'}) "
          f"-- esik 2.0", flush=True)

    sol1 = _cozucu(a1.x, a1.v, a1.m, np.zeros(a1.n), a1.h,
                   _alpha0_denetle(a1.alpha0, a.gozeneksiz), a1.Y0, a.device,
                   cfl=a.cfl,
                   mat=_mat(a.gozeneksiz, a.yercekimli, a.hasarli))
    t = _kos(sol1, 0.0, a.t1, a.azami_adim, "a1")
    print(f"  asama-1 bitti: t = {t:.5e} s "
          f"({time.perf_counter() - t0:.1f} s duvar)", flush=True)
    st1 = sol1.state_numpy()

    # ------------------------------------------------------ KABALASTIR
    sahne = asama2_sahnesi_ucseviye(a1, st1)
    d = sahne.diagnostics
    print("\nAKTARIM (Lagrange'ci, UC SEVIYELI):", flush=True)
    print(f"  {d['n_asama1_ince']} cekirdek -> {d['n_aktarilan']} parcacik",
          flush=True)
    print(f"  birebir kopyalanan = {d['n_kopyalanan']}   "
          f"atilan = {d['n_asama2_atilan']}", flush=True)
    print(f"  SAHNE momentum hatasi = {d['sahne_momentum_hatasi']:.3e}  "
          f"kutle = {d['sahne_kutle_hatasi']:.3e}", flush=True)
    print(f"  toplam N = {d['n_toplam']}", flush=True)
    if "hasar_max" in d:
        print(f"  HASAR tasindi: max {d['hasar_max']:.4f}  "
              f"kutle agirlikli {d['hasar_kutle_agirlikli']:.4e}  "
              f"defter hatasi {d['hasar_kutle_hatasi']:.3e}", flush=True)
    print(f"  korunum: kutle {d['kutle_hata']:.2e}  "
          f"momentum {d['momentum_hata']:.2e}  enerji {d['enerji_hata']:.2e}",
          flush=True)
    print(f"  atama mesafesi = {d['atama_mesafe_max'] / d['s_asama2']:.3f} "
          f"hucre", flush=True)
    print(f"  isiya donen = {100 * d['ice_donen_kinetik_oran']:.3f}%",
          flush=True)
    print(f"  komsu medyan = {d['komsu']['komsu_medyan']:.0f}  "
          f"(<30 orani {d['komsu']['yalniz_oran']:.3f})", flush=True)

    # ---------------------------------------------------------- ASAMA 2
    print(f"\nASAMA-2: lam={a.lam2}, N={sahne.n}, t {t:.4e} -> {a.t_end}",
          flush=True)
    # ASAMA-1'IN HASARI DEVRALINIYOR. Devralinmazsa `t1`'de silinir;
    # olculdu (2026-08-21): asama-1'de `D_max = 0,060`, aktarimdan
    # sonra cozucu `D = 0` ile basliyordu ve `--hasarli` kolu hasarsiz
    # kolla ayni `beta`yi veriyordu.
    sol2 = _cozucu(sahne.x, sahne.v, sahne.m, sahne.e, sahne.h,
                   _alpha0_denetle(sahne.alpha0, a.gozeneksiz), sahne.Y0, a.device,
                   cfl=a.cfl, mat=_mat(a.gozeneksiz, a.yercekimli, a.hasarli),
                   D0=sahne.hasar if a.hasarli else None)
    izler = []
    # Aktarimdan sonra parcacik kimlikleri degisti; krater referansi
    # ASAMA-1'in baslangic konumlarindan ALINAMAZ. Bu yuzden aktarim
    # SONRASI konumlar referans aliniyor ve bunun ne oldugu yaziliyor:
    # "t1'den t_end'e olan degisim", mutlak krater DEGIL.
    x_ref2 = np.array(sahne.x, dtype=np.float64, copy=True)
    # HEDEF MASKESI artik MERMI KESRINDEN kuruluyor.
    #
    # Eskiden `~sahne.is_impactor` yaziliyordu ve aktarimdan sonra
    # `is_impactor` HICBIR parcacikta korunmadigi icin maske her yerde
    # `True` oluyordu. Sonuc: kacan 28 parcacik "hedef ejektasi"
    # etiketleniyordu, oysa toplam kutleleri 579,40 kg -- merminin
    # kendisi -- ve parcacik kutleleri 0,72-55,75 kg iken hedef
    # parcaciklarinin medyani 3,73e5 kg (rapor A17).
    #
    # `mermi_kesri` kutle-agirlikli tasindigi icin karisim siteleri de
    # dogru: kesri 0,5'in altinda olan parcacik KUTLECE cogunlukla
    # hedeftir.
    f_mermi2 = np.asarray(sahne.mermi_kesri, dtype=np.float64)
    hedef2 = f_mermi2 < 0.5
    print(f"  mermi kesri: kutle {float((sahne.m * f_mermi2).sum()):.4f} kg, "
          f"kesri>0,5 olan {int((~hedef2).sum())} parcacik, "
          f"tasima hatasi {d.get('mermi_kutle_hatasi', float('nan')):.3e}",
          flush=True)
    v_esc = escape_speed(m_hedef, R)
    ehat = np.asarray(p_imp) / float(np.linalg.norm(p_imp))
    P = float(np.linalg.norm(p_imp))

    def _ornek(adim, tt, st):
        d = _iz_ornegi(st, hedef=hedef2, R=R, v_esc=v_esc, ehat=ehat,
                       p_imp=P, x0=x_ref2)
        d.update(adim=adim, t=tt)
        izler.append(d)
        with iz_yolu.open("a", encoding="utf-8") as f:
            f.write(json.dumps(d) + "\n")
        tg = d["t_gecis_medyan"]
        print(f"    a2 {adim:6d} t={tt:.4e} beta_bal={d['beta_bal']:.5f} "
              f"hedef_ej={d['n_hedef_ejekta']:5d} "
              f"bekleyen={d['n_bekleyen']:5d} "
              f"t_gecis={'--' if tg != tg else f'{tg:.2f}s':>8} "
              f"derinlik={d['krater_derinlik']:.4f}", flush=True)

    iz_yolu = Path(a.out).with_suffix(".izler.jsonl")
    iz_yolu.parent.mkdir(parents=True, exist_ok=True)
    if iz_yolu.exists():
        iz_yolu.unlink()
    t2 = _kos(sol2, t, a.t_end, a.azami_adim, "a2",
              ornekle=_ornek if a.iz_every > 0 else None, her=a.iz_every)
    st_son = sol2.state_numpy()
    b = _beta(st_son, sahne, p_imp, m_hedef, R)

    # SON DURUM DISKE YAZILIR. Bugun iki kez post-hoc tani yapmak istedim
    # ve elimde yalnizca ozet JSON vardi; her seferinde saatlerce yeniden
    # kosmak gerekiyordu. Diziler kucuk (~1 MB), kosu ise saatler.
    durum_yolu = Path(a.out).with_suffix(".son_durum.npz")
    np.savez_compressed(
        durum_yolu, x=st_son["x"], v=st_son["v"], m=st_son["m"],
        x_referans=x_ref2, hedef=hedef2, mermi_kesri=f_mermi2,
        R=R, v_esc=v_esc, ehat=ehat, p_imp=P, t=t2,
        # Hasar alani: kapali kolda sifir dizisi doner (state_numpy),
        # yani iki kol AYNI sekille okunur ve karsilastirma post-hoc
        # yapilabilir.
        D=st_son["D"], u=st_son["u"], rho=st_son["rho"])
    print(f"\nson durum yazildi: {durum_yolu}", flush=True)

    print(f"\nSONUC ({time.perf_counter() - t0:.1f} s duvar)", flush=True)
    print(f"  A1        = {A1:.4f}  "
          f"({'GECTI' if A1 >= 2.0 else 'DUSTU'})", flush=True)
    print(f"  t_sim     = {t2:.5e} s", flush=True)
    print(f"  beta      = {b['beta']:.6f}", flush=True)
    print(f"  n_ejekta  = {b['n_ejekta']}", flush=True)
    print(f"  momentum kapanisi = {b['momentum_kapanis']:.3e}", flush=True)
    # KRATER SEKLI son durumda da olculuyor. `--iz-every` verilmeden
    # kosulan kollarda derinlik/cap JSON'a hic girmiyordu ve dis kiyas
    # (pi-olcekleme, derinlik/cap bandi) yapilamiyordu.
    try:
        from dartrift.inference.forward import KRATER_AYARLARI_DART
        from dartrift.observables.crater_shape import crater_profile
        _kr = crater_profile(st_son["x"][hedef2], center=np.zeros(3),
                             impact_direction=ehat, reference_radius=R,
                             x_reference=x_ref2[hedef2],
                             **KRATER_AYARLARI_DART)
        krater = {"derinlik_m": float(_kr.depth), "cap_m": float(_kr.diameter),
                  "derinlik_cap": (float(_kr.depth) / float(_kr.diameter)
                                   if _kr.diameter > 0 else float("nan"))}
    except Exception as e:                                  # noqa: BLE001
        krater = {"derinlik_m": float("nan"), "cap_m": float("nan"),
                  "derinlik_cap": float("nan"), "hata": str(e)[:80]}
    print(f"  krater    = derinlik {krater['derinlik_m']:.4f} m, "
          f"cap {krater['cap_m']:.4f} m, "
          f"d/D {krater['derinlik_cap']:.4f}  "
          f"(literatur bandi 0,15-0,30)", flush=True)

    D = np.asarray(st_son["D"], dtype=np.float64)
    hasar = {"acik": bool(a.hasarli), "D_ort": float(D.mean()),
             "D_max": float(D.max()),
             "n_tam_kirik": int(np.count_nonzero(D >= 0.999)),
             "hedef_D_ort": float(D[hedef2].mean())}
    print(f"  hasar     = {'ACIK' if a.hasarli else 'kapali'}  "
          f"D_ort {hasar['D_ort']:.4f}  D_max {hasar['D_max']:.4f}  "
          f"tam kirik {hasar['n_tam_kirik']}", flush=True)
    print("\n  KARSILASTIRMA icin: --tek-asama kolunu da kos.", flush=True)

    Path(a.out).write_text(json.dumps(
        {"kip": "iki_asama", "lam1": a.lam1, "r_ince1": a.r_ince1,
         "lam2": a.lam2, "r_ince2": a.r_ince2, "t1": a.t1, "t_sim": t2,
         "A1": A1, "A1_gecti": bool(A1 >= 2.0),
         "N_asama1": a1.n, "N_asama2": sahne.n,
         "aktarim": {k: v for k, v in d.items() if k != "atama"},
         "hasar": hasar, "krater": krater,
         "izler": izler,
         "duvar_s": time.perf_counter() - t0, **b}, indent=2, default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
