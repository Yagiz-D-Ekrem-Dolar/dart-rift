"""FAZ 4.4 (asıl) — DART kurulumunda **çözünürlük yakınsaması**

Plan şunu istiyor:

> 4.4 | DART kurulumunda **çözünürlük yakınsaması** | krater çapı ve β'nın
> `N`'e duyarlılığı

Bu betik A′'yı (ADR-0041, KAYIT-037) **gerçek DART sahnesine** bağlayıp
β'nın çözünürlükle nasıl davrandığını ölçüyor.

## İki kol, kasıtlı

| kol | `h` | ne gösterir |
|---|---|---|
| **A′** | parçacık başına (ince bölge `2·s/λ`) | seçilen yaklaşım |
| **tek `h`** | hepsi `2·s` | A′'nın katkısını yalıtan kontrol |

KAYIT-037 küp geometrisinde ölçtü ki A′ incelme kazancının `%67,1`'ini,
tek `h` yalnızca `%9,1`'ini veriyor. Bu betik aynı karşılaştırmayı
**DART geometrisinde** yapıyor — ADR-0041'in ve ADR-0042'nin "koşullu"
kalan kısmı tam olarak buydu.

## Ölçülen

`β(t)` izlenir; yakınsama ölçütü **son değer** değil, çözünürlükler
arası **fark**. Ayrıca ADR-0026'nın tanısı (merminin hedef aralığına
göre kaç parçacık olduğu) her kolda raporlanır.
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

# Cikti UTF-8'e sabitleniyor: baslıklarda `—` ve `A′` geciyor ve bir
# raporlama betiginin UnicodeEncodeError ile dusmesi raporu yok eder.
# SLURM isi PYTHONIOENCODING=utf-8 veriyor ama betik ELLE de kosulabilir.
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


from dartrift.cpu_reference.materials import (  # noqa: E402
    DamageParams, GravityParams, MaterialParams, PorosityParams,
    StrengthParams)
from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402
from dartrift.observables.momentum_transfer import (  # noqa: E402
    escape_speed, momentum_transfer)
from dartrift.setup.refine import refine_scene  # noqa: E402
from dartrift.setup.scene import build_scene  # noqa: E402

SAHNE = dict(radius=82.0, bulk_density=1800.0, root_seed=20260801,
             model_class="M1", f_boulder=0.25, q=3.0, n_impactor=800,
             r_min=14.0, r_max=42.0)


def _malzeme() -> MaterialParams:
    return MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e4, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=True, alpha0=1.6, Pe=1.0e6,
                                Ps=1.0e8, n_exp=2.0),
        gravity=GravityParams(enabled=False),
        damage=DamageParams(enabled=False),
        density_method="continuity")


def _mermi_yaricapi(x, is_imp) -> float:
    xi = x[is_imp]
    return float(np.max(np.linalg.norm(xi - xi.mean(axis=0)[None, :], axis=1)))


def _kos(rs, mat, device: str, steps: int, every: int, etiket: str,
         tek_h: bool, t_end: float | None = None) -> dict:
    """Bir kolu koştur.

    `t_end` verilirse **eşit simüle süreye** kadar koşulur ve `steps`
    yalnızca üst sınırdır.

    ## Neden `t_end` zorunlu oldu

    İlk sürüm yalnızca `--steps` alıyordu. Kolların `dt`'si farklı
    (`h` farklı) olduğu için **farklı `t_sim`**'e ulaşıyorlardı:
    ölçüldü, `s7_λ2` A′ `0,342 s`, tek `h` `0,694 s`.

    > Farklı `t`'deki `β`'ları kıyaslamak **yakınsama ölçmez**.
    > B1 ve B3 bu yüzden hesaplanamamıştı (sıkıntı A6).
    """
    from dartrift.warp_core.solver_solid import WarpSolid3D

    h = float(2.0 * rs.spacing_coarse) if tek_h else rs.h
    n = rs.n
    sol = WarpSolid3D(
        np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
        np.ascontiguousarray(rs.m), np.zeros(n), h, mat, RefParams(cfl=0.25),
        alpha0=np.ascontiguousarray(rs.alpha0),
        Y0=np.ascontiguousarray(rs.Y0), device=device, check_every=10 ** 9)

    p_imp = rs.impactor_momentum
    m_hedef = rs.target_mass
    v_kacis = escape_speed(m_hedef, rs.target_radius)
    mermi_capi = 2.0 * _mermi_yaricapi(rs.x, rs.is_impactor)
    print(f"    {etiket}: N={n} (ince {rs.diagnostics['n_ince']}, "
          f"kaba {rs.diagnostics['n_kaba']}, mermi {rs.diagnostics['n_mermi']}), "
          f"h={'TEK ' + format(h, '.1f') if tek_h else 'parcacik basina'}",
          flush=True)
    # ADR-0026 TANISI: mermi, BULUNDUGU BOLGENIN araligina gore kac parcacik?
    s_yerel = rs.spacing_fine
    print(f"      mermi capi {mermi_capi:.3f} m; yerel aralik {s_yerel:.3f} m "
          f"-> {mermi_capi / s_yerel:.3f} parcacik/cap "
          f"({'COZULMUS' if mermi_capi / s_yerel >= 2.0 else 'COZULMEMIS'})",
          flush=True)

    izler, t_sim, t0 = [], 0.0, time.perf_counter()
    adim = 0
    while adim < steps:
        adim += 1
        dt = sol.compute_dt()
        # SON ADIM KIRPILIR: t_end'i tam yakala, asma.
        if t_end is not None and t_sim + dt > t_end:
            dt = t_end - t_sim
        sol.step(dt)
        t_sim += dt
        son_mu = (adim == steps) or (t_end is not None
                                     and t_sim >= t_end * (1.0 - 1e-12))
        if adim % every == 0 or son_mu:
            st = sol.state_numpy()
            if not np.all(np.isfinite(st["v"])):
                print(f"      PATLADI adim {adim}", flush=True)
                return {"etiket": etiket, "durum": "patladi", "adim": adim}
            try:
                mt = momentum_transfer(
                    st["x"], st["v"], st["m"], impactor_momentum=p_imp,
                    center=np.zeros(3), target_mass=m_hedef,
                    target_radius=rs.target_radius,
                    control_radius=2.0 * rs.target_radius,
                    speed_threshold=v_kacis)
                beta = float(mt.beta)
            except Exception as e:                       # noqa: BLE001
                beta = float("nan")
                if adim == every:
                    print(f"      beta okunamadi: {e}", flush=True)
            izler.append({"adim": adim, "t": t_sim, "beta": beta})
        if son_mu:
            break
    sure = time.perf_counter() - t0
    # T_END'E ULASILAMADIYSA SESSIZ GECMEZ: kismi kosunun beta'si
    # sistematik olarak yanlis olur ve tam da "yakinsamiyor" gibi gorunur
    # (ADR-0011 §3'un dersi).
    ulasti = t_end is None or t_sim >= t_end * (1.0 - 1e-9)
    if not ulasti:
        print(f"      T_END'E ULASILAMADI: {t_sim:.6e} < {t_end:.6e} "
              f"({adim} adim) -- bu kol YAKINSAMA YARGISINA GIRMEZ",
              flush=True)
    son = [z["beta"] for z in izler[-3:] if np.isfinite(z["beta"])]
    print(f"      beta(son) = {son[-1] if son else float('nan'):.6f}  "
          f"t_sim = {t_sim:.4e} s  ({sure:.1f} s duvar)", flush=True)
    return {"etiket": etiket, "durum": "tamam" if ulasti else "kismi",
            "N": n, "t_sim": t_sim, "t_end_hedef": t_end,
            "beta_son": son[-1] if son else float("nan"),
            "mermi_parcacik_cap": mermi_capi / s_yerel,
            "tasarruf": rs.diagnostics["tasarruf"],
            "izler": izler, "duvar_s": sure}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--every", type=int, default=250)
    ap.add_argument("--t-end", type=float, default=None,
                    help="EŞIT simüle süre [s]. Verilmezse --steps kullanılır "
                         "ve kollar farklı t_sim'e ulaşır (B1/B3 hesaplanamaz).")
    ap.add_argument("--r-ince", type=float, default=25.0)
    ap.add_argument("--out",
                    default=str(REPO.parent / "faz44_sonuc.json"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.4 — DART KURULUMUNDA COZUNURLUK YAKINSAMASI", flush=True)
    print("=" * 78, flush=True)
    mat = _malzeme()
    sonuclar = {}
    # A2/A3 kurulumdan gelir; butun kollarin EN KOTUSU tutulur (kapi en
    # zayif halkadan gecer).
    a2_carpani = float("inf")
    a3_sapma = 0.0
    # TANILAR (olcut DEGIL, kapi raporunda ayrica listelenir): dikisin
    # EN KOTU orani ve tasarrufun EN KOTUSU.
    dikis_oran = float("inf")
    tasarruf_min = float("inf")

    for s_kaba, lam in ((7.0, 2), (7.0, 3), (5.0, 2)):
        s_ince = s_kaba / lam
        ad = f"s{s_kaba:g}_lam{lam}"
        print(f"\n[{ad}] kaba={s_kaba} m, ince={s_ince:.3f} m, lam={lam}",
              flush=True)
        kaba = build_scene(spacing=s_kaba, device="cpu", **SAHNE)
        ince = build_scene(spacing=s_ince, device="cpu", **SAHNE)
        rs = refine_scene(kaba, ince, r_ince=a.r_ince)
        # A2: ince bolge mermiyi KAPSIYOR mu -> r_ince / R_mermi
        r_mermi = _mermi_yaricapi(rs.x, rs.is_impactor)
        a2_carpani = min(a2_carpani, a.r_ince / max(r_mermi, 1e-300))
        a3_sapma = max(a3_sapma, rs.diagnostics["hedef_kutle_sapmasi"])
        dikis_oran = min(dikis_oran, rs.diagnostics["dikis_en_yakin_oran"])
        tasarruf_min = min(tasarruf_min, rs.diagnostics["tasarruf"])
        print(f"    tasarruf {rs.diagnostics['tasarruf']:.2f}x, "
              f"kutle sapmasi {rs.diagnostics['hedef_kutle_sapmasi']:.3e}, "
              f"r_ince/R_mermi {a.r_ince / max(r_mermi, 1e-300):.2f}",
              flush=True)
        sonuclar[ad + "_Aprime"] = _kos(rs, mat, a.device, a.steps, a.every,
                                        ad + " A'", tek_h=False,
                                        t_end=a.t_end)
        sonuclar[ad + "_tek_h"] = _kos(rs, mat, a.device, a.steps, a.every,
                                       ad + " tek h", tek_h=True,
                                       t_end=a.t_end)

    # G4 anahtarlarini AYNI dosyaya yaz -- kapi betigi bu dosyayi dogrudan
    # okuyabilsin diye. Ceviri mantigi validation/g4_ozet.py'de ve SINANIYOR
    # (measure_longrun'daki gomulu plato mantiginin hatasini tekrarlamamak icin).
    from dartrift.validation.g4_ozet import faz44_ozet

    ham = {"r_ince": a.r_ince, "steps": a.steps,
           "A2_r_ince_carpani": a2_carpani,
           "A3_kutle_sapmasi": a3_sapma,
           "dikis_en_yakin_oran": dikis_oran,
           "tasarruf": tasarruf_min,
           "sonuclar": sonuclar}
    ham.update(faz44_ozet(ham))
    Path(a.out).write_text(json.dumps(ham, indent=2))
    print(f"\nyazildi: {a.out}", flush=True)
    print("\nG4 ANAHTARLARI", flush=True)
    for k in ("A1_mermi_parcacik_cap", "A2_r_ince_carpani", "A3_kutle_sapmasi",
              "B1_beta_farki", "B3_Aprime_daha_yakin",
              "dikis_en_yakin_oran", "tasarruf"):
        print(f"    {k:26s} = {ham.get(k, 'KOSULMADI')}", flush=True)

    print("\nOZET", flush=True)
    print(f"    {'kol':22s} {'N':>8s} {'beta':>10s} {'mermi p/cap':>12s}",
          flush=True)
    for ad, y in sonuclar.items():
        if y["durum"] != "tamam":
            print(f"    {ad:22s} {y['durum']}", flush=True)
            continue
        print(f"    {ad:22s} {y['N']:>8d} {y['beta_son']:>10.6f} "
              f"{y['mermi_parcacik_cap']:>12.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
