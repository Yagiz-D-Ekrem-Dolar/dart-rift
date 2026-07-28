"""G1 kapisi kosucusu — DR-RIFT-P1 §7'deki 8 kriteri kanitlariyla isletir.

Kullanim:
    python scripts/run_g1_gate.py [--device cuda:0] [--quick] [--run-dir DIZIN]

KRITIK go/no-go kapisi: gecilmezse motor yoktur; proje durur, 1B testlere
donulur, basarisiz config dondurulur (sartname kurali betikte otomatiktir).
Cikti: G1_report.md + g1_metrics.json + grafikler (matplotlib varsa).
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from dartrift.reporting import write_metrics  # noqa: E402  (sys.path yukarida kuruluyor)

SOD_RESOLUTIONS = [64, 128, 256]
SEDOV_SIDES = [32, 48, 64]
SEDOV_SIDES_QUICK = [24, 32, 40]


class Crit:
    def __init__(self, cid: str, title: str):
        self.cid, self.title = cid, title
        self.passed: bool | None = None
        self.evidence = ""

    def record(self, ok: bool, ev: str) -> None:
        self.passed, self.evidence = ok, ev


def _plots(run_dir: Path, sod: dict, sedov: dict) -> list[str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    import numpy as np

    from dartrift.validation.riemann import SOD_LEFT, SOD_RIGHT, sample_profile, solve_riemann

    made = []
    # Sod profili vs analitik
    prof = sod["profile"]
    x = np.array(prof["x"])
    sol = solve_riemann(SOD_LEFT, SOD_RIGHT, 1.4)
    xs = np.linspace(-0.6, 0.6, 1200)
    re, ve, pe = sample_profile(sol, xs, sod["t"])
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    for ax, key, exact, label in (
        (axes[0], "rho", re, "yogunluk"),
        (axes[1], "v", ve, "hiz"),
        (axes[2], "P", pe, "basinc"),
    ):
        ax.plot(xs, exact, "k-", lw=1, label="kesin Riemann")
        ax.plot(x, prof[key], ".", ms=2, label="SPH")
        ax.set_xlim(-0.6, 0.6)
        ax.set_xlabel("x")
        ax.set_title(f"Sod {label} (t={sod['t']})")
        ax.legend(fontsize=7)
    fig.tight_layout()
    p = run_dir / "sod_profile.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    made.append(p.name)
    # Sedov radyal profil
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(sedov["profile"]["r"], sedov["profile"]["rho"], ".", ms=1.5, label="SPH")
    ax.axvline(sedov["shock_radius_exact"], color="k", ls="--", label="benzerlik r_s")
    ax.axvline(sedov["shock_radius_measured"], color="r", ls=":", label="olculen r_s")
    ax.set_xlabel("r")
    ax.set_ylabel("rho")
    ax.set_title(f"Sedov (t={sedov['t_end']}, n={sedov['n_side']}^3)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    p = run_dir / "sedov_profile.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    made.append(p.name)
    return made


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--quick", action="store_true", help="kucuk olcekli yerel on-kontrol")
    ap.add_argument("--run-dir", default=None)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.run_dir) if args.run_dir else REPO / "gate_runs" / f"g1_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    from dartrift.particles import warp_available, warp_devices

    gpu_ok = warp_available() and any(d.startswith("cuda") for d in warp_devices())
    if args.device.startswith("cuda") and not gpu_ok:
        print("HATA: CUDA cihazi yok; G1 kaniti GPU ister (--device cpu yalnizca on-kontrol).",
              file=sys.stderr)
        return 2

    crit = {
        "C1": Crit("C1", "Kutle korunumu ~makine hassasiyeti (P1-VR-01)"),
        "C2": Crit("C2", "Dogrusal momentum goreli hatasi < 1e-6 (P1-VR-02)"),
        "C3": Crit("C3", "Toplam enerji hatasi < %0.5 (P1-VR-03)"),
        "C4": Crit("C4", "Sod post-sok degiskenleri analitik cozume %3-5 (P1-VR-04)"),
        "C5": Crit("C5", "Sedov sok yaricapi benzerlik cozumune ~%5 (P1-VR-05)"),
        "C6": Crit("C6", "Kernel + komsu + CPU<->GPU capraz testleri geciyor"),
        "C7": Crit("C7", "Zaman adimi kisit-yuzdesi logu uretiliyor (P1-FR-07)"),
        "C8": Crit("C8", "G0 determinizm altin hash'leri hala gecerli"),
    }

    t0 = time.perf_counter()

    # --- 1) tam pytest paketi (kernel/komsu/capraz/altin-hash kanitlari) ----
    pytest_cmd = [sys.executable, "-m", "pytest", "tests", "-v",
                  "--cov=dartrift", "--cov-report=term",
                  f"--cov-report=json:{run_dir / 'coverage.json'}"]
    if not gpu_ok:
        pytest_cmd += ["-m", "not gpu"]
    proc = subprocess.run(pytest_cmd, capture_output=True, text=True, cwd=REPO)
    out = proc.stdout + proc.stderr
    (run_dir / "pytest_full.log").write_text(out, encoding="utf-8")
    tests_ok = proc.returncode == 0

    def passed(pattern: str) -> bool:
        return (pattern in out) and (f"FAILED tests/{pattern}" not in out) and tests_ok

    crit["C6"].record(
        passed("test_kernel_fn.py") and passed("test_neighbors.py") and passed("test_sph_cross.py"),
        "tests/test_kernel_fn.py + test_neighbors.py + test_sph_cross.py",
    )
    crit["C8"].record(
        "test_golden_hash_matches PASSED" in out,
        "tests/test_determinism_golden.py::test_golden_hash_matches",
    )

    # --- 2) senaryo merdivenleri ------------------------------------------
    from dartrift.validation.conservation import run_conservation_warp, shear_av_suppression
    from dartrift.validation.plate import run_plate_warp
    from dartrift.validation.sedov import run_sedov_warp
    from dartrift.validation.sod import run_sod_warp

    device = args.device
    sod_ladder = {r: run_sod_warp(r, device) for r in SOD_RESOLUTIONS}
    sod_hi = sod_ladder[max(SOD_RESOLUTIONS)]
    sides = SEDOV_SIDES_QUICK if args.quick else SEDOV_SIDES
    sedov_ladder = {}
    # Enerji hatasinin YAPISAL BIR SIZINTI mi yoksa KESME HATASI mi oldugunu
    # ayirt eden olcum (ADR-0020): CFL yariya inince hata yariya inmeli.
    # Sizinti olsaydi sabit kalir ya da adim sayisiyla buyurdu. "Hata < %0.5"
    # demek, hatanin KONTROL EDILEBILIR oldugunu soylemez; bu oran soyler.
    energy_dt_ratio = None
    if gpu_ok:
        from dartrift.cpu_reference.sph_ref import RefParams as _RP
        from dartrift.validation.sedov import GAMMA as _G

        for s in sides:
            sedov_ladder[s] = run_sedov_warp(s, device)
        n_lo = min(sides)
        half = run_sedov_warp(n_lo, device, params=_RP(gamma=_G, cfl=0.125))
        e_full = sedov_ladder[n_lo]["conservation"]["energy_rel"]
        e_half = half["conservation"]["energy_rel"]
        energy_dt_ratio = e_full / max(e_half, 1.0e-300)
    plate = run_plate_warp(256, device)
    cons_n = 1000 if args.quick else 3000
    cons = run_conservation_warp(cons_n, device, t_end=0.3)
    shear = shear_av_suppression()

    scenarios = {
        "sod": {r: {k: v for k, v in m.items() if k != "profile"} for r, m in sod_ladder.items()},
        "sedov": {
            s: {k: v for k, v in m.items() if k != "profile"}
            for s, m in sedov_ladder.items()
        },
        "plate": plate,
        "conservation_cloud": cons,
        "shear_balsara": shear,
    }

    # --- 3) kriter degerlendirme ------------------------------------------
    # Korunum esikleri IZOLE senaryolarda olculur (P1 §6.3): bulut + Sedov.
    # Sod izole degildir (donmus bantlar duvar); onun butcesi duvar impulsuyla
    # KAPANIS olarak sinanir ve C2 kanitina ek satir olarak girer.
    isolated = [cons] + [m["conservation"] for m in sedov_ladder.values()]
    mass_all = isolated + [m["conservation"] for m in sod_ladder.values()]
    mass_max = max(c["mass_rel"] for c in mass_all)
    mom_max = max(c["momentum_rel"] for c in isolated)
    e_max = max(c["energy_rel"] for c in isolated + [sod_hi["conservation"]])
    sod_closure = max(m["momentum_budget"]["closure_rel_err"] for m in sod_ladder.values())
    # Kanit metni HANGI sartin dustugunu soylemeli: "KALDI / maks kutle sapmasi
    # 0.00e+00" okuyucuyu yaniltir (G1 1426017'de tam bu oldu; asil neden
    # pytest'in kalmasiydi).
    crit["C1"].record(
        tests_ok and mass_max < 1.0e-12,
        f"maks kutle sapmasi {mass_max:.2e}"
        + ("" if tests_ok else "; ANCAK pytest paketi KALDI (bkz. pytest_full.log)"),
    )
    crit["C2"].record(
        mom_max < 1.0e-6 and sod_closure < 0.02,
        f"izole maks {mom_max:.2e}; Sod duvar-impuls kapanisi {sod_closure:.2%}",
    )
    _dt_ev = (
        f"; dt yarilaninca hata/{energy_dt_ratio:.2f} "
        f"(~2 = birinci mertebe KESME hatasi, sizinti DEGIL)"
        if energy_dt_ratio is not None else ""
    )
    crit["C3"].record(e_max < 0.005, f"maks enerji goreli hatasi {e_max:.3%}{_dt_ev}")
    crit["C4"].record(
        sod_hi["max_rel_err"] < 0.05,
        f"res=256: {'; '.join(f'{k}={v:.2%}' for k, v in sod_hi['rel_err'].items())}",
    )
    if sedov_ladder:
        sed_hi = sedov_ladder[max(sedov_ladder)]
        # Kinetik enerji orani ADR-0011 §4'te "ikinci bagimsiz gosterge" olarak
        # RAPORLANACAGI yazildigi halde hicbir yerde okunmuyordu. Artik kanit
        # metnine giriyor. Beklenen deger, sonlu enjeksiyon yaricapi (r_inj =
        # sok yaricapinin ~%32'si) nedeniyle NOKTA patlamasi benzerlik cozumunun
        # 0.28'i DEGIL, ~0.19'dur: ic bolge sicak kalir ve o enerji kinetige
        # donusmez. Esik konmaz — sayi raporlanir ve sapmasi gorulur.
        crit["C5"].record(
            sed_hi["shock_radius_rel_err"] < 0.05,
            f"n={max(sedov_ladder)}^3: r={sed_hi['shock_radius_measured']:.4f} vs "
            f"{sed_hi['shock_radius_exact']:.4f} ({sed_hi['shock_radius_rel_err']:.2%}); "
            f"KE/E={sed_hi['kinetic_fraction']:.3f} "
            f"(sonlu enjeksiyonda ~0.19 beklenir; nokta patlamasi 0.28)",
        )
    else:
        crit["C5"].record(False, "CUDA yok: Sedov kosulamadi -> KANITLANAMADI")
    ts_ok = all(
        m["timestep_summary"]["n_steps"] > 0
        and abs(m["timestep_summary"]["binding_cfl_viscous_pct"]
                + m["timestep_summary"]["binding_acceleration_pct"] - 100.0) < 1e-9
        for m in list(sod_ladder.values()) + list(sedov_ladder.values()) + [cons]
    )
    crit["C7"].record(ts_ok, "her senaryoda kisit-yuzdesi ozeti mevcut ve tutarli")

    # yakinsama (P1-VR-06) — rapora girer
    l1 = [sod_ladder[r]["l1_rho"] for r in SOD_RESOLUTIONS]
    conv_ok = l1[0] > l1[1] > l1[2]

    all_pass = all(c.passed for c in crit.values()) and tests_ok and conv_ok
    plots = _plots(run_dir, sod_hi, sedov_ladder[max(sedov_ladder)]) if sedov_ladder else []

    metrics = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": device,
        "quick": args.quick,
        "scenarios": scenarios,
        "convergence_l1_rho": dict(
            zip([str(r) for r in SOD_RESOLUTIONS], l1, strict=True)
        ),
        "convergence_monotonic": conv_ok,
        "energy_error_dt_halving_ratio": energy_dt_ratio,
        "pytest_exit": proc.returncode,
        "wall_time_s": time.perf_counter() - t0,
    }
    write_metrics(run_dir / "g1_metrics.json", metrics)

    title = "# G1 Kapi Raporu — \"Sok motoru calisiyor\" (KRITIK go/no-go)"
    if not gpu_ok:
        title = "# G1 ON-KONTROL Raporu (KAPI DEGIL) — CUDA yok"
    lines = [
        title, "",
        f"- Tarih (UTC): {metrics['timestamp_utc']}",
        f"- Makine: {platform.node()} / {platform.platform()}",
        f"- Cihaz: {device} {'(quick mod)' if args.quick else ''}",
        f"- pytest: cikis {proc.returncode} (pytest_full.log)",
        "",
        "| # | Kriter | Sonuc | Kanit |",
        "|---|--------|-------|-------|",
    ]
    for c in crit.values():
        if c.passed:
            mark = "GECTI"
        else:
            mark = "KANITLANAMADI" if (not gpu_ok and c.cid == "C5") else "KALDI"
        lines.append(f"| {c.cid} | {c.title} | **{mark}** | {c.evidence} |")
    lines += [
        "",
        f"- Yakinsama (P1-VR-06): L1(rho) {l1[0]:.4g} -> {l1[1]:.4g} -> "
        f"{l1[2]:.4g} ({'monoton azaliyor' if conv_ok else 'MONOTON DEGIL'})",
        f"- Kesme/Balsara: bastirma orani {shear['suppression_ratio']:.3f} (esik < 0.05)",
        "- AV parametreleri: alpha=1.0, beta=2.0 (sartname §2.5 tipik; raporlandi)",
        f"- Grafikler: {', '.join(plots) if plots else 'matplotlib yok'}",
    ]
    if not gpu_ok:
        lines += ["", "## SONUC: G1 DEGERLENDIRILMEDI — bu bir on-kontroldur (CUDA gerekli)"]
    else:
        verdict = (
            "GECTI — FAZ 2 baslayabilir" if all_pass
            else "GECEMEDI — motor yok, proje durur"
        )
        lines += ["", f"## SONUC: G1 {verdict}"]
    lines += ["", "> Gorsel olarak makul krater kanit DEGILDIR; kanit test ve sayidir."]
    (run_dir / "G1_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if not gpu_ok:
        return 2
    if not all_pass:
        # sartname: basarisiz config dondurulur
        from dartrift.config import load_config
        from dartrift.logging_cfg import build_manifest, write_manifest

        cfg = load_config(REPO / "configs" / "p1_sod.yaml")
        manifest = build_manifest(cfg, status="physical_reject",
                                  wall_time=time.perf_counter() - t0)
        write_manifest(manifest, run_dir / "failed_gate_manifest.yaml")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
