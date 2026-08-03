"""G3 kapisi kosucusu — DR-RIFT-P3 §7'deki 7 kriteri kanitlariyla isletir.

Kullanim:
    python scripts/run_g3_gate.py [--device cuda:0] [--quick] [--run-dir DIZIN]

Kriterler:
 1. Sekil-mesh hatti: kapali, kenar-manifold, hacim analitikle uyusuyor (P3-FR-01).
 2. Moloz yigini: hedef yogunluk, komsuluk sayisi, blok kesri geri olculuyor
    (P3-FR-02/03/04).
 3. Settling: baslangic KE esigin altinda + denge tanisi (P3-FR-05, P3-VR-01).
 4. Mermi: nokta parcacik degil, >=3 cozunurlukte yakinsak (P3-FR-06/07, P3-VR-02).
 5. Gozlenebilirler: beta bilinen sahnede geri kazaniliyor, duyarlilik
    raporlaniyor, krater yerel/kuresel ayrimi calisiyor (P3-FR-08, P3-VR-03).
 6. Determinizm + regresyon: config'den kurulan sahne yeniden uretilebilir
    (ayni tohum ayni karma, FARKLI tohum FARKLI karma) ve tum paket geciyor.
 7. Veri manifestosu: PDS urun kimlikleri + saglama toplamlari.

C7 NOTU: veri DEPOYA konmaz (100+ MB); depoya giren sey KOKEN KAYDIDIR
(`data_manifest/*.json`: urun kimligi, SHA-256, arsivin resmi MD5'i). Veri
`scripts/fetch_pds_shapemodel.py` ile cekilir. Manifest yoksa ya da bir urun
kimlik/saglama tasimiyorsa kriter "KANITLANAMADI" isaretlenir — GECTI
ISARETLENMEZ. Kanitlanamayan bir kriteri gecmis saymak kapinin kendisini
anlamsizlastirir.
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

from dartrift.reporting import write_metrics  # noqa: E402  (sys.path yukarida)


class Crit:
    def __init__(self, cid: str, title: str):
        self.cid, self.title = cid, title
        self.passed: bool | None = None
        self.provable = True
        self.evidence = ""

    def record(self, ok: bool, ev: str) -> None:
        self.passed, self.evidence = ok, ev

    def unprovable(self, ev: str) -> None:
        self.passed, self.provable, self.evidence = False, False, ev


def _data_manifest_status(run_dir: Path) -> tuple[bool, str]:
    """PDS urun kimlikleri + saglamalar var mi ve TUTUYOR mu?

    Uc kademeli denetim — her biri ayri bir soruyu yanitlar:
      1. Manifest var mi ve her urun kimlik + SHA-256 tasiyor mu?
      2. Her urun ARSIVIN resmi MD5'iyle dogrulanmis mi? (`md5_verified`)
         Kendi karmamiz "diskte ne var" der; arsivinki "dogru dosya mi".
      3. Dosyalar bu makinede VARSA, SHA-256'lari yeniden hesaplanip
         manifestle karsilastirilir. Bayat bir manifestin sessizce gecmesi
         boylece engellenir.
    """
    import hashlib
    import json
    import os

    man = REPO / "data_manifest"
    files = sorted(man.glob("*.json")) if man.is_dir() else []
    if not files:
        return False, (
            f"data_manifest/ bos ya da yok ({man}); gercek PDS urunleri yok. "
            "Urun kimlikleri ve SHA-256 toplamlari olmadan bu kriter "
            "KANITLANAMAZ — gecmis sayilmaz."
        )

    total = with_sum = md5_ok = 0
    checked = mismatched = 0
    kotu: list[str] = []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return False, f"{f.name} okunamadi: {exc}"
        kokler = [Path(p) for p in (
            os.environ.get("DARTRIFT_PDS_DIR"), d.get("data_root"),
            str(REPO / "data" / "pds")) if p]
        for item in d.get("products", []):
            total += 1
            if item.get("sha256") and item.get("product_id"):
                with_sum += 1
            if item.get("md5_verified"):
                md5_ok += 1
            for kok in kokler:
                p = kok / item["filename"]
                if p.is_file():
                    h = hashlib.sha256()
                    with open(p, "rb") as fh:
                        for b in iter(lambda fh=fh: fh.read(1 << 20), b""):
                            h.update(b)
                    checked += 1
                    if h.hexdigest() != item["sha256"]:
                        mismatched += 1
                        kotu.append(item["filename"])
                    break

    (run_dir / "data_manifest_summary.txt").write_text(
        f"dosya={len(files)} urun={total} kimlik+saglama={with_sum} "
        f"resmi_md5={md5_ok} diskte_dogrulanan={checked} uyusmayan={mismatched}\n",
        encoding="utf-8")

    ok = (total > 0 and with_sum == total and md5_ok == total and mismatched == 0)
    ev = (f"{len(files)} manifest, {total} urun; kimlik+SHA-256 {with_sum}/{total}; "
          f"arsivin resmi MD5'iyle dogrulanmis {md5_ok}/{total}; "
          f"diskte yeniden hesaplanip eslesen {checked - mismatched}/{checked}")
    if kotu:
        ev += f"; SAGLAMA UYUSMAYAN: {kotu}"
    if checked == 0:
        ev += " (dosyalar bu makinede yok — yalnizca kayit denetlendi)"
    return ok, ev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--run-dir", default=None)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.run_dir) if args.run_dir else REPO / "gate_runs" / f"g3_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    from dartrift.particles import warp_available, warp_devices

    gpu_ok = warp_available() and any(d.startswith("cuda") for d in warp_devices())
    if args.device.startswith("cuda") and not gpu_ok:
        print("HATA: CUDA yok; G3 kaniti settling icin GPU ister.", file=sys.stderr)
        return 2

    crit = {
        "C1": Crit("C1", "Sekil-mesh hatti kapali/manifold, hacim dogru (P3-FR-01)"),
        "C2": Crit("C2", "Moloz yigini: yogunluk, komsuluk, blok kesri (P3-FR-02/03/04)"),
        "C3": Crit("C3", "Settling: baslangic KE esigin altinda (P3-FR-05, P3-VR-01)"),
        "C4": Crit("C4", "Mermi sonlu boyutlu ve yakinsak (P3-FR-06/07, P3-VR-02)"),
        "C5": Crit("C5", "Gozlenebilirler + duyarlilik (P3-FR-08, P3-VR-03)"),
        "C6": Crit("C6", "Determinizm + tam test paketi (regresyon yok)"),
        "C7": Crit("C7", "Veri manifestosu: PDS kimlikleri + saglamalar"),
    }

    t0 = time.perf_counter()

    # --- 1) tam pytest paketi ---------------------------------------------
    pytest_cmd = [sys.executable, "-m", "pytest", "tests", "-v",
                  "--cov=dartrift", "--cov-report=term",
                  f"--cov-report=json:{run_dir / 'coverage.json'}"]
    if not gpu_ok:
        pytest_cmd += ["-m", "not gpu"]
    proc = subprocess.run(pytest_cmd, capture_output=True, text=True, cwd=REPO)
    out = proc.stdout + proc.stderr
    (run_dir / "pytest_full.log").write_text(out, encoding="utf-8")
    tests_ok = proc.returncode == 0

    # --- 2) senaryolar -----------------------------------------------------
    from dartrift.validation.scene_checks import (
        run_impactor_convergence,
        run_observable_selftest,
        run_rubble_quality,
        run_crater_irregular_selftest,
        run_scene_determinism,
        run_shape_pipeline,
        run_speed_threshold_selftest,
    )

    shape = run_shape_pipeline()
    crit["C1"].record(
        shape["all_manifold"] and shape["volume_converges"]
        and shape["max_volume_rel_err"] < 0.01,
        f"kenar-manifold {shape['all_manifold']}, hacim hatasi maks "
        f"{shape['max_volume_rel_err']:.3%}, bolunmeyle "
        f"{'azaliyor' if shape['volume_converges'] else 'AZALMIYOR'} "
        f"({shape['volume_error_ladder'][0]:.2%}->{shape['volume_error_ladder'][-1]:.3%})",
    )

    rub = run_rubble_quality()
    # Blok kesri DOYMUSSA hedefe ulasilamaz; o durumda kriter "doyma
    # raporlandi mi" olur — sessizce dusuk kesir kabul edilmez.
    boulder_ok = (rub["boulder_fraction_rel_err"] < 0.10) or rub["boulder_saturated"]
    crit["C2"].record(
        rub["bulk_density_rel_err"] < 0.01 and rub["coordination_interior_mean"] >= 11.0
        and boulder_ok and rub["deterministic"]
        and rub["alpha0_distinct"] and rub["Y0_distinct"],
        f"N={rub['n_particles']}, yogunluk sapmasi {rub['bulk_density_rel_err']:.3%}, "
        f"ic komsuluk {rub['coordination_interior_mean']:.2f} (FCC=12), blok kesri "
        f"{rub['boulder_fraction_measured']:.3f} (hedef 0.30"
        f"{', DOYMUS' if rub['boulder_saturated'] else ''}), "
        f"determinizm {rub['deterministic']}, matris/blok malzeme ayri "
        f"{rub['alpha0_distinct'] and rub['Y0_distinct']}",
    )

    # --- 3) settling (GPU) -------------------------------------------------
    settle_m: dict = {}
    if gpu_ok:
        import numpy as np

        from dartrift.cpu_reference.materials import (
            GravityParams,
            MaterialParams,
            PorosityParams,
            StrengthParams,
        )
        from dartrift.setup.rubble_generator import build_rubble_pile
        from dartrift.setup.settling import settle_pile
        from dartrift.setup.shape_mesh import icosphere

        mat = MaterialParams(
            eos="tillotson",
            strength=StrengthParams(enabled=True, Y0=1.0e4, mu_f=0.6, YM=1.5e9,
                                    shear_G=2.27e10, jaumann=True),
            porosity=PorosityParams(enabled=True, alpha0=1.6, Pe=1.0e6,
                                    Ps=1.0e8, n_exp=2.0),
            gravity=GravityParams(enabled=True, G=6.6743e-11, eps=0.0,
                                  mode="barnes_hut", theta=0.5),
            density_method="continuity",
        )
        pile = build_rubble_pile(icosphere(4, 80.0), spacing=7.0, bulk_density=1800.0,
                                 rho0_solid=2700.0,
                                 root_seed=17, model_class="M0")
        res = settle_pile(pile, mat, device=args.device, damping=0.02,
                          max_steps=100 if args.quick else 400, report_every=50)
        d = res.diagnostics
        settle_m = {
            "n_steps": res.n_steps, "t_end": res.t_end,
            "ke_initial": res.ke_initial, "ke_final": res.ke_final,
            "ke_threshold": res.ke_threshold, "binding_energy": res.binding_energy,
            "ke_over_binding_final": d["ke_over_binding_final"],
            "converged": res.converged,
            "a_sph_max_t0": d["a_sph_max_t0"],
            "a_gravity_max_t0": d["a_gravity_max_t0"],
            "free_fall_time": d["free_fall_time"],
            "steps_per_free_fall": d["steps_per_free_fall"],
            "simulated_fraction_of_free_fall": d["simulated_fraction_of_free_fall"],
            "rho_min": d["rho_min"], "rho_max": d["rho_max"],
            "alpha_min": d["alpha_min"], "alpha_max": d["alpha_max"],
        }
        finite = bool(np.isfinite([res.ke_final, d["rho_min"], d["rho_max"]]).all())
        crit["C3"].record(
            res.ke_final < res.ke_threshold and finite and d["a_sph_max_t0"] == 0.0,
            f"KE_son/E_bag = {d['ke_over_binding_final']:.3e} (esik 1e-3); "
            f"t=0 SPH ivmesi {d['a_sph_max_t0']:.1e} (denge), yercekimi "
            f"{d['a_gravity_max_t0']:.2e} m/s^2. Yercekimsel oturma KAPSAM DISI: "
            f"bir t_ff = {d['steps_per_free_fall']:.2e} adim (ADR-0024)",
        )

    imp = run_impactor_convergence()
    crit["C4"].record(
        imp["no_point_particle"] and imp["n_resolutions"] >= 3
        and imp["volume_error_converges"] and imp["max_mass_rel_err"] < 1e-12
        and imp["max_momentum_rel_err"] < 1e-12 and imp["min_particles_across"] >= 5.0
        and imp["starts_outside_target"],
        f"{imp['n_resolutions']} cozunurluk "
        f"(N={[r['n_actual'] for r in imp['resolutions']]}), cap boyunca en az "
        f"{imp['min_particles_across']:.1f} parcacik, kutle hatasi "
        f"{imp['max_mass_rel_err']:.1e}, momentum {imp['max_momentum_rel_err']:.1e}, "
        f"hacim hatasi yakinsiyor {imp['volume_error_converges']}",
    )

    obs = run_observable_selftest()
    # Duyarlilik taramasinin IKI ekseni de gercekten is gormeli. Yalnizca
    # toplam yayilima bakmak yeterli degildi: 1. senaryoda hiz esigi ekseninin
    # yayilimi TAM SIFIR olmasina ragmen kriter geciyordu (butun yayilim
    # yaricap ekseninden geliyordu). Hiz ekseni ayri bir senaryoyla kanitlanir.
    spd = run_speed_threshold_selftest()
    # Krater cikaricinin butun sinavlari KURE uzerindeydi; Dimorphos degil
    # (88x87x65 m). Duzensiz cisim senaryosu artik kriterin parcasi.
    cir = run_crater_irregular_selftest()
    crit["C5"].record(
        obs["beta_recovery_rel_err"] < 1e-6 and obs["momentum_closure"] < 1e-9
        and obs["sensitivity_reported"] and obs["crater_separates_global"]
        and obs["radius_axis_active"] and spd["speed_axis_active"]
        and spd["beta_monotone_in_threshold"] and spd["mass_monotone_in_threshold"]
        and cir["phantom_removed"] and cir["depth_rel_err_true_ref"] < 0.20
        and cir["spherical_flag_reported"]
        and obs["ejecta_power_law_rel_err"] < 0.10 and obs["ejecta_power_law_r2"] > 0.95,
        f"beta geri kazanimi {obs['beta_recovery_rel_err']:.1e} (gercek "
        f"{obs['beta_true']}), momentum defteri {obs['momentum_closure']:.1e}, "
        f"duyarlilik yayilimi {obs['beta_relative_spread']:.2%} "
        f"[{obs['beta_min']:.3f}, {obs['beta_max']:.3f}] — yaricap ekseni "
        f"{obs['beta_spread_radius_axis']:.4f}, hiz ekseni {obs['beta_spread_speed_axis']:.4f} "
        f"(bu senaryoda OLU; ayri senaryoda {spd['beta_spread_speed_axis']:.4f}, "
        f"beta esikle monoton azaliyor {spd['beta_by_speed_factor'][0]:.3f}->"
        f"{spd['beta_by_speed_factor'][-1]:.3f}); ejekta us "
        f"{obs['ejecta_power_law_exponent']:.3f} (gercek "
        f"{obs['ejecta_power_law_exponent_true']}, R^2={obs['ejecta_power_law_r2']:.4f}); "
        f"krater {obs['crater_depth']:.2f} m, kuresel degisim "
        f"{obs['crater_global_change']:.2f} m (ayrisiyor); DUZENSIZ cisim "
        f"(88x87x65 m): kuresel referans kratersiz cisimde "
        f"{cir['phantom_depth_spherical_ref']:.2f} m HAYALI krater uretiyor, "
        f"carpma oncesi referansla {cir['phantom_depth_true_ref']:.1e} m ve "
        f"bilinen {cir['known_depth']:.0f} m cukur "
        f"{cir['measured_depth_true_ref']:.2f} m olculuyor "
        f"(hata %{100 * cir['depth_rel_err_true_ref']:.1f})",
    )

    scn = run_scene_determinism()
    crit["C6"].record(
        tests_ok and "FAILED" not in out
        and rub["deterministic"] and scn["reproducible"] and scn["seed_sensitive"]
        and scn["impactor_outside_target"] and scn["target_at_rest"]
        # ADR-0035: DUZENSIZ cisimde de mermi hedefin disinda olmali.
        # Onceki olcut esdeger-kure yaricapi vekiliydi ve yalnizca kure
        # icin gecerliydi; uretim konfigurasyonu gercek PDS seklini kullaniyor.
        and scn["irregular_all_outside"]
        and scn["impactor_nonporous"] and scn["target_porous"]
        and scn["material_heterogeneous"]
        and scn["impactor_mass_rel_err"] < 1e-12
        and scn["impactor_momentum_rel_err"] < 1e-12,
        f"pytest cikis={proc.returncode}; sahne N={scn['n_total']} "
        f"({scn['n_target']} hedef + {scn['n_impactor']} mermi), karma "
        f"{scn['digest'][:16]}, ayni tohum ayni sahne {scn['reproducible']}, "
        f"farkli tohum farkli sahne {scn['seed_sensitive']}, mermi hedefin "
        f"disinda {scn['impactor_outside_target']}, hedef durgun "
        f"{scn['target_at_rest']}, mermi gozeneksiz/hedef gozenekli "
        f"{scn['impactor_nonporous'] and scn['target_porous']}, "
        f"kutle/momentum hatasi {scn['impactor_mass_rel_err']:.1e}/"
        f"{scn['impactor_momentum_rel_err']:.1e}",
    )

    man_ok, man_ev = _data_manifest_status(run_dir)
    if man_ok:
        crit["C7"].record(True, man_ev)
    else:
        crit["C7"].unprovable(man_ev)

    provable = [c for c in crit.values() if c.provable]
    all_pass = all(c.passed for c in provable)
    unprovable = [c for c in crit.values() if not c.provable]

    metrics = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "quick": args.quick,
        "shape_pipeline": shape,
        "rubble_quality": rub,
        "settling": settle_m,
        "impactor_convergence": imp,
        "observables_selftest": obs,
        "scene_determinism": scn,
        "pytest_exit": proc.returncode,
        "wall_time_s": time.perf_counter() - t0,
    }
    write_metrics(run_dir / "g3_metrics.json", metrics)

    title = '# G3 Kapi Raporu — "Gercek sahne kurulumu"'
    if not gpu_ok:
        title = "# G3 ON-KONTROL Raporu (KAPI DEGIL) — CUDA yok"
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
        if not c.provable:
            mark = "KANITLANAMADI"
        elif c.passed:
            mark = "GECTI"
        else:
            mark = "KALDI"
        lines.append(f"| {c.cid} | {c.title} | **{mark}** | {c.evidence} |")

    if not gpu_ok:
        lines += ["", "## SONUC: G3 DEGERLENDIRILMEDI — on-kontrol (CUDA gerekli)"]
    else:
        if unprovable:
            ids = ", ".join(c.cid for c in unprovable)
            verdict = (
                f"KISMI — kanitlanabilir kriterlerin hepsi gecti, ancak {ids} "
                "KANITLANAMADI (veri yok). FAZ 4 bu eksik acikca tasinarak baslar."
                if all_pass else
                "GECEMEDI — kanitlanabilir kriterlerden en az biri kaldi"
            )
        else:
            verdict = "GECTI — FAZ 4 baslayabilir" if all_pass else "GECEMEDI"
        lines += ["", f"## SONUC: G3 {verdict}"]

    lines += [
        "",
        "> Kanitlanamayan kriter GECMIS SAYILMAZ. Iddia daraltilir ama "
        "bilim bukulmez.",
    ]
    (run_dir / "G3_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if not gpu_ok:
        return 2
    if not all_pass:
        return 1
    return 3 if unprovable else 0


if __name__ == "__main__":
    raise SystemExit(main())
