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
from dartrift.observables.momentum_transfer import (  # noqa: E402
    escape_speed, momentum_transfer)
from dartrift.setup.refine import (refine_scene_local,  # noqa: E402
                                   refine_scene_ucseviye)
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402
from dartrift.setup.two_stage import (  # noqa: E402
    asama2_sahnesi_ucseviye)

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402

#: FAZ 4.5'in ölçtüğü bağlanma süresi (`faz43c`, ADR-0043 §4a).
T1_OLCULEN = 4.767e-3


def _mat(gozeneksiz: bool = False):
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
    m = _malzeme()
    if not gozeneksiz:
        return m
    import dataclasses
    return dataclasses.replace(
        m, porosity=dataclasses.replace(m.porosity, enabled=False))


#: Katı bazalt yoğunluğu — gözeneksiz kolun yığın yoğunluğu.
RHO0_KATI = 2700.0


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


def _alpha0_denetle(alpha0, gozeneksiz: bool):
    """Gözeneksiz kolda sahne gerçekten katı mı — sessizce geçmesin."""
    a = np.asarray(alpha0, dtype=np.float64)
    if gozeneksiz and not np.allclose(a, 1.0, atol=1e-9):
        raise ValueError(
            f"gozeneksiz kol ama alpha0 != 1 (min {a.min():.4f}, "
            f"max {a.max():.4f}) — sahne KATI kurulmamis, cisim t=0'da "
            f"gerilmede baslar (rapor A14)")
    return a


def _cozucu(x, v, m, u, h, alpha0, Y0, device, mat=None):
    from dartrift.warp_core.solver_solid import WarpSolid3D
    return WarpSolid3D(
        np.ascontiguousarray(x), np.ascontiguousarray(v),
        np.ascontiguousarray(m), np.ascontiguousarray(u),
        np.ascontiguousarray(h),
        mat if mat is not None else _malzeme(), RefParams(cfl=0.25),
        alpha0=np.ascontiguousarray(alpha0), Y0=np.ascontiguousarray(Y0),
        device=device, check_every=10 ** 9)


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
    from dartrift.observables.momentum_transfer import (balistik_beta,
                                                        kacis_bekleyenler)
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
    ap.add_argument("--gozeneksiz", action="store_true",
                    help="P-alpha gozenekliligi KAPAT (tani kontrol kolu)")
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.8 — IKI ASAMALI KOSU (ADR-0043)", flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=7.0, device="cpu",
                       **_sahne_kolu(a.gozeneksiz))
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
                      mat=_mat(a.gozeneksiz))
        t = _kos(sol, 0.0, a.t_end, a.azami_adim, "tek")
        b = _beta(sol.state_numpy(), a2, p_imp, m_hedef, R)
        print(f"\n  t_sim = {t:.5e}  beta = {b['beta']:.6f}", flush=True)
        Path(a.out).write_text(json.dumps(
            {"kip": "tek_asama", "lam": a.lam2, "N": a2.n, "t_sim": t,
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
                   mat=_mat(a.gozeneksiz))
    t = _kos(sol1, 0.0, a.t1, a.azami_adim, "a1")
    print(f"  asama-1 bitti: t = {t:.5e} s "
          f"({time.perf_counter() - t0:.1f} s duvar)", flush=True)
    st1 = sol1.state_numpy()

    # ------------------------------------------------------ KABALASTIR
    sahne = asama2_sahnesi_ucseviye(a1, st1)
    d = sahne.diagnostics
    print(f"\nAKTARIM (Lagrange'ci, UC SEVIYELI):", flush=True)
    print(f"  {d['n_asama1_ince']} cekirdek -> {d['n_aktarilan']} parcacik",
          flush=True)
    print(f"  birebir kopyalanan = {d['n_kopyalanan']}   "
          f"atilan = {d['n_asama2_atilan']}", flush=True)
    print(f"  SAHNE momentum hatasi = {d['sahne_momentum_hatasi']:.3e}  "
          f"kutle = {d['sahne_kutle_hatasi']:.3e}", flush=True)
    print(f"  toplam N = {d['n_toplam']}", flush=True)
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
    sol2 = _cozucu(sahne.x, sahne.v, sahne.m, sahne.e, sahne.h,
                   _alpha0_denetle(sahne.alpha0, a.gozeneksiz), sahne.Y0, a.device,
                   mat=_mat(a.gozeneksiz))
    izler = []
    x0_h = np.array(a1.x, dtype=np.float64, copy=True)   # CARPMA ONCESI (R4)
    # Aktarimdan sonra parcacik kimlikleri degisti; krater referansi
    # ASAMA-1'in baslangic konumlarindan ALINAMAZ. Bu yuzden aktarim
    # SONRASI konumlar referans aliniyor ve bunun ne oldugu yaziliyor:
    # "t1'den t_end'e olan degisim", mutlak krater DEGIL.
    x_ref2 = np.array(sahne.x, dtype=np.float64, copy=True)
    hedef2 = ~np.asarray(sahne.is_impactor, dtype=bool)
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
        x_referans=x_ref2, hedef=hedef2, R=R, v_esc=v_esc, ehat=ehat,
        p_imp=P, t=t2)
    print(f"\nson durum yazildi: {durum_yolu}", flush=True)

    print(f"\nSONUC ({time.perf_counter() - t0:.1f} s duvar)", flush=True)
    print(f"  A1        = {A1:.4f}  "
          f"({'GECTI' if A1 >= 2.0 else 'DUSTU'})", flush=True)
    print(f"  t_sim     = {t2:.5e} s", flush=True)
    print(f"  beta      = {b['beta']:.6f}", flush=True)
    print(f"  n_ejekta  = {b['n_ejekta']}", flush=True)
    print(f"  momentum kapanisi = {b['momentum_kapanis']:.3e}", flush=True)
    print("\n  KARSILASTIRMA icin: --tek-asama kolunu da kos.", flush=True)

    Path(a.out).write_text(json.dumps(
        {"kip": "iki_asama", "lam1": a.lam1, "r_ince1": a.r_ince1,
         "lam2": a.lam2, "r_ince2": a.r_ince2, "t1": a.t1, "t_sim": t2,
         "A1": A1, "A1_gecti": bool(A1 >= 2.0),
         "N_asama1": a1.n, "N_asama2": sahne.n,
         "aktarim": {k: v for k, v in d.items() if k != "atama"},
         "izler": izler,
         "duvar_s": time.perf_counter() - t0, **b}, indent=2, default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
