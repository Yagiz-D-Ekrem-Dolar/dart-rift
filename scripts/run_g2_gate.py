"""G2 kapisi kosucusu — DR-RIFT-P2 §7'deki 7 kriteri kanitlariyla isletir.

Kullanim:
    python scripts/run_g2_gate.py [--device cuda:0] [--quick] [--run-dir DIZIN]

Kriterler:
 1. Rijit donme yapay gerilme uretmiyor (objektiflik).
 2. Taylor bar + elastik dalga benchmark'a yakin.
 3. Crush curve fiziksel: alpha>=1, is dogru, geri genlesme yok.
 4. Iki-cisim + duzgun kure yercekimi dogrulandi; drift sinirli.
 5. Global korunum (yercekimi dahil): momentum <1e-6, enerji <%0.5-1.
 6. Her modul ablasyonla acilip kapanabiliyor.
 7. G0/G1 onceki testler hala geciyor (regresyon yok).
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))


class Crit:
    def __init__(self, cid: str, title: str):
        self.cid, self.title = cid, title
        self.passed: bool | None = None
        self.evidence = ""

    def record(self, ok: bool, ev: str) -> None:
        self.passed, self.evidence = ok, ev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--run-dir", default=None)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.run_dir) if args.run_dir else REPO / "gate_runs" / f"g2_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    from dartrift.particles import warp_available, warp_devices

    gpu_ok = warp_available() and any(d.startswith("cuda") for d in warp_devices())
    if args.device.startswith("cuda") and not gpu_ok:
        print("HATA: CUDA yok; G2 kaniti GPU ister (Taylor bar).", file=sys.stderr)
        return 2

    crit = {
        "C1": Crit("C1", "Rijit donme yapay gerilme uretmiyor (P2-VR-01)"),
        "C2": Crit("C2", "Taylor bar + elastik dalga benchmark'a yakin (P2-VR-02/03)"),
        "C3": Crit("C3", "Crush curve fiziksel; alpha>=1; geri genlesme yok (P2-VR-04)"),
        "C4": Crit("C4", "Iki-cisim + duzgun kure yercekimi; drift sinirli (P2-VR-05)"),
        "C5": Crit("C5", "Global korunum yercekimi dahil (P2-VR-06)"),
        "C6": Crit("C6", "Her modul ablasyonla acilip kapanabiliyor (P2-FR-06)"),
        "C7": Crit("C7", "G0/G1 testleri hala geciyor (regresyon yok)"),
    }

    t0 = time.perf_counter()

    # --- 1) tam pytest paketi (G0+G1+G2 regresyon kaniti) ------------------
    pytest_cmd = [sys.executable, "-m", "pytest", "tests", "-v",
                  "--cov=dartrift", "--cov-report=term",
                  f"--cov-report=json:{run_dir / 'coverage.json'}"]
    if not gpu_ok:
        pytest_cmd += ["-m", "not gpu"]
    proc = subprocess.run(pytest_cmd, capture_output=True, text=True, cwd=REPO)
    out = proc.stdout + proc.stderr
    (run_dir / "pytest_full.log").write_text(out, encoding="utf-8")
    tests_ok = proc.returncode == 0
    crit["C7"].record(
        tests_ok and "test_golden_hash_matches PASSED" in out
        and "test_sod.py" in out and "FAILED" not in out,
        f"pytest cikis={proc.returncode}; G0 altin hash + G1 sok testleri dahil tum paket",
    )

    # --- 2) senaryolar -----------------------------------------------------
    from dartrift.validation.ablation import run_ablation_matrix
    from dartrift.validation.gravity import run_cold_collapse, run_two_body, run_uniform_sphere
    from dartrift.validation.porous import run_crush_cycle, run_porous_plate
    from dartrift.validation.solids import run_elastic_wave, run_rigid_rotation, run_taylor_bar

    rot_on = run_rigid_rotation(jaumann=True)
    rot_off = run_rigid_rotation(jaumann=False)
    crit["C1"].record(
        rot_on["rel_err_vs_rotated"] < 0.03 and rot_on["vm_drift_rel"] < 0.02
        and rot_off["rel_err_vs_rotated"] > 0.5,
        f"S es-donme hatasi {rot_on['rel_err_vs_rotated']:.2%}, vm drift "
        f"{rot_on['vm_drift_rel']:.2%}; Jaumann kapaliyken {rot_off['rel_err_vs_rotated']:.0%}",
    )

    wave = run_elastic_wave()
    taylor = {}
    taylor_ok = False
    if gpu_ok:
        nx = 7 if args.quick else 9
        taylor = run_taylor_bar(args.device, v_impact=200.0, Y0=4.0e8, nx=nx)
        taylor_stiff = run_taylor_bar(args.device, v_impact=200.0, Y0=8.0e8, nx=nx)
        taylor["stiff_L_over_L0"] = taylor_stiff["L_over_L0"]
        taylor_ok = (
            0.60 <= taylor["L_over_L0"] <= 0.80
            and taylor["mushroom_ratio"] > 1.15
            and taylor["plastic_cum"] > 0
            and taylor["energy_rel_err"] < 0.015
            and taylor_stiff["L_over_L0"] > taylor["L_over_L0"]
        )
    crit["C2"].record(
        wave["rel_err"] < 0.03 and wave["distinguishes_bulk"] and taylor_ok,
        f"elastik dalga {wave['speed_measured']:.0f} m/s vs teorik "
        f"{wave['c_long_theory']:.0f} ({wave['rel_err']:.2%}); Taylor L/L0="
        f"{taylor.get('L_over_L0', float('nan')):.3f} (bant 0.60-0.80), "
        f"Y0 2x -> {taylor.get('stiff_L_over_L0', float('nan')):.3f}",
    )

    cycle = run_crush_cycle()
    pl_por = run_porous_plate(porous=True)
    pl_sol = run_porous_plate(porous=False)
    crush_ok = (
        cycle["monotonic_loading"] and cycle["alpha_min"] >= 1.0
        and cycle["no_reexpansion"] and cycle["compaction_work_positive"]
        and pl_por["p_peak_core"] < 0.85 * pl_sol["p_peak_core"]
        and pl_por["alpha_all_ge_1"]
    )
    crit["C3"].record(
        crush_ok,
        f"cevrim: monoton+geri-genlesme-yok+is>=0; SPH: P_tepe porozlu/kati = "
        f"{pl_por['p_peak_core'] / pl_sol['p_peak_core']:.2f}, alpha_min={pl_por['alpha_min']:.3f}",
    )

    two = run_two_body()
    sphere = run_uniform_sphere()
    grav_ok = (
        two["energy_max_rel_err"] < 5e-4 and two["radius_drift_rel"] < 1e-3
        and sphere["bh_vs_direct_median_rel"] < 0.005
        and sphere["shell_mean_rel_err_max"] < 0.05
    )
    crit["C4"].record(
        grav_ok,
        f"iki-cisim 20 yorunge: E hatasi {two['energy_max_rel_err']:.1e}, yaricap "
        f"drifti {two['radius_drift_rel']:.1e}; kure: BH-direct medyan "
        f"{sphere['bh_vs_direct_median_rel']:.2%}, kabuk hata maks "
        f"{sphere['shell_mean_rel_err_max']:.2%}",
    )

    collapse = run_cold_collapse()
    crit["C5"].record(
        collapse["energy_rel_err_vs_pot"] < 0.01 and collapse["momentum_rel"] < 1e-6
        and collapse["collapse_happened"],
        f"soguk collapse: enerji {collapse['energy_rel_err_vs_pot']:.2%} "
        f"(pot olcegine), momentum {collapse['momentum_rel']:.1e}",
    )

    matrix = run_ablation_matrix()
    crit["C6"].record(
        matrix["all_expected"],
        "; ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in matrix["checks"].items()),
    )

    all_pass = all(c.passed for c in crit.values())

    metrics = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "quick": args.quick,
        "rigid_rotation": {"jaumann_on": rot_on, "jaumann_off": rot_off},
        "elastic_wave": wave,
        "taylor_bar": taylor,
        "crush_cycle": {k: v for k, v in cycle.items() if k != "alpha_load"},
        "porous_plate": {"porous": pl_por, "solid": pl_sol},
        "two_body": two,
        "uniform_sphere": sphere,
        "cold_collapse": collapse,
        "ablation_checks": matrix["checks"],
        "pytest_exit": proc.returncode,
        "wall_time_s": time.perf_counter() - t0,
    }
    (run_dir / "g2_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    title = '# G2 Kapi Raporu — "Gercek malzeme fizigi"'
    if not gpu_ok:
        title = "# G2 ON-KONTROL Raporu (KAPI DEGIL) — CUDA yok"
    lines = [
        title, "",
        f"- Tarih (UTC): {metrics['timestamp_utc']}",
        f"- Makine: {platform.node()} / {platform.platform()}",
        f"- Cihaz: {args.device} {'(quick)' if args.quick else ''}",
        f"- pytest: cikis {proc.returncode}",
        "",
        "| # | Kriter | Sonuc | Kanit |",
        "|---|--------|-------|-------|",
    ]
    for c in crit.values():
        if c.passed:
            mark = "GECTI"
        else:
            mark = "KANITLANAMADI" if (not gpu_ok and c.cid == "C2") else "KALDI"
        lines.append(f"| {c.cid} | {c.title} | **{mark}** | {c.evidence} |")
    if not gpu_ok:
        lines += ["", "## SONUC: G2 DEGERLENDIRILMEDI — on-kontrol (CUDA gerekli)"]
    else:
        verdict = "GECTI — FAZ 3 baslayabilir" if all_pass else (
            "GECEMEDI — ilgili modulun iddiasi yapilamaz (Ana Plan Karar 3)"
        )
        lines += ["", f"## SONUC: G2 {verdict}"]
    lines += [
        "",
        "> Benchmark gecmeyen modulun iddiasi yapilmaz; "
        "iddia daraltilir ama bilim bukulmez.",
    ]
    (run_dir / "G2_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if not gpu_ok:
        return 2
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
