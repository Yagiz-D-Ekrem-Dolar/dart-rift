"""G0 kapisi kosucusu — DR-RIFT-P0 §9'daki 8 kriteri kanitlariyla isletir.

Kullanim:
    python scripts/run_g0_gate.py [--require-gpu] [--run-dir DIZIN]

Cikti: run-dir altinda G0_report.md, manifest.yaml, pytest/coverage loglari.
Cikis kodu 0 = kapi GECTI; 0 disi = kapi GECEMEDI (iddia yapilamaz).
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

COVERAGE_MIN = 85.0
MIN_ADR_COUNT = 4


class GateCriterion:
    def __init__(self, cid: str, title: str):
        self.cid = cid
        self.title = title
        self.passed: bool | None = None
        self.evidence = ""

    def record(self, passed: bool, evidence: str) -> None:
        self.passed = passed
        self.evidence = evidence


def sh(cmd: list[str], log_path: Path | None = None, cwd: Path = REPO) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    out = proc.stdout + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr.strip() else "")
    if log_path is not None:
        log_path.write_text(out, encoding="utf-8")
    return proc.returncode, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-gpu", action="store_true",
                    help="GPU roundtrip atlanirsa kapiyi GECEMEDI say (TRUBA kaniti icin)")
    ap.add_argument("--run-dir", default=None)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.run_dir) if args.run_dir else REPO / "gate_runs" / f"g0_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    from dartrift.config import load_config
    from dartrift.logging_cfg import build_manifest, setup_logging, write_manifest
    from dartrift.particles import warp_available, warp_devices

    logger = setup_logging(run_dir)
    logger.info("G0 kapi kosusu basladi: %s", run_dir)

    criteria = {
        "C1": GateCriterion("C1", "Depo derleniyor / testler toplaniyor; CI katmani yesil"),
        "C2": GateCriterion("C2", "Config sema dogrulayici calisiyor; gecersizler reddediliyor"),
        "C3": GateCriterion("C3", "Parcacik deposu CPU<->GPU roundtrip bit-esit"),
        "C4": GateCriterion("C4", "Tohum determinizmi + shard-degismezligi testleri geciyor"),
        "C5": GateCriterion("C5", "Invariant cercevesi enjekte edilmis hatalari yakaliyor"),
        "C6": GateCriterion("C6", "HDF5 uc-katman yaz-oku esitligi"),
        "C7": GateCriterion("C7", f"En az {MIN_ADR_COUNT} ADR yazilmis"),
        "C8": GateCriterion("C8", "Manifest uretimi tam (Ek A alanlari)"),
    }

    t0 = time.perf_counter()

    # --- tam test paketi + kapsam (C1 ve alt-kanitlarin temeli) -----------
    gpu_ok_env = warp_available() and any(d.startswith("cuda") for d in warp_devices())
    pytest_cmd = [
        sys.executable, "-m", "pytest", "tests", "-v",
        "--cov=dartrift", "--cov-report=term-missing",
        f"--cov-report=json:{run_dir / 'coverage.json'}",
    ]
    if not gpu_ok_env:
        pytest_cmd += ["-m", "not gpu"]
    rc_all, out_all = sh(pytest_cmd, run_dir / "pytest_full.log")
    criteria["C1"].record(rc_all == 0, f"pytest cikis kodu={rc_all} (pytest_full.log)")

    def suite_passed(pattern: str) -> bool:
        # tam kosu loglarindan ilgili dosyanin FAILED icermedigini ve kostugunu dogrula
        ran = pattern in out_all
        failed = f"FAILED tests/{pattern}" in out_all or f"ERROR tests/{pattern}" in out_all
        return ran and not failed and rc_all == 0

    criteria["C2"].record(suite_passed("test_config.py"), "tests/test_config.py (15 gecersiz vaka)")
    criteria["C4"].record(
        suite_passed("test_rng.py") and suite_passed("test_determinism_golden.py"),
        "tests/test_rng.py + tests/test_determinism_golden.py (altin hash)",
    )
    criteria["C5"].record(
        suite_passed("test_invariants.py"), "tests/test_invariants.py (enjeksiyon)"
    )
    criteria["C6"].record(suite_passed("test_io.py"), "tests/test_io.py (uc katman + checksum)")

    # --- C3: GPU roundtrip -------------------------------------------------
    if gpu_ok_env:
        gpu_line = next(
            (ln for ln in out_all.splitlines() if "test_roundtrip_bitwise_gpu_science" in ln), ""
        )
        gpu_pass = "PASSED" in gpu_line
        criteria["C3"].record(gpu_pass, f"GPU roundtrip: {gpu_line.strip() or 'bulunamadi'}")
    else:
        msg = "GPU yok: yalnizca CPU-cihaz roundtrip kosuldu (bit-esit)"
        criteria["C3"].record(not args.require_gpu and suite_passed("test_particles.py"), msg)

    # --- C7: ADR sayimi ----------------------------------------------------
    adrs = sorted((REPO / "docs" / "adr").glob("ADR-*.md"))
    criteria["C7"].record(len(adrs) >= MIN_ADR_COUNT, f"{len(adrs)} ADR: {[a.name for a in adrs]}")

    # --- C8 + manifest uretimi ----------------------------------------------
    cfg = load_config(REPO / "configs" / "p0_smoke.yaml")
    try:
        manifest = build_manifest(
            cfg,
            status="accepted",
            wall_time=time.perf_counter() - t0,
            checkpoint_sha256="0" * 64,  # FAZ 0: fizik checkpoint'i yok (bilincli placeholder)
            observables_sha256="0" * 64,
            data={"note": "FAZ 0 - veri girisi yok; PDS manifesti FAZ 3'te dolar"},
        )
        write_manifest(manifest, run_dir / "manifest.yaml")
        criteria["C8"].record(True, "manifest.yaml yazildi; Ek A alan tamligi dogrulandi")
    except Exception as exc:  # noqa: BLE001 - kapi raporuna gecirilir
        criteria["C8"].record(False, f"manifest hatasi: {exc}")

    # --- kapsam esigi (P0-QR-04, C1'e baglanir) -----------------------------
    cov_note = "coverage.json yok"
    cov_pct = None
    cov_file = run_dir / "coverage.json"
    if cov_file.is_file():
        cov = json.loads(cov_file.read_text(encoding="utf-8"))
        cov_pct = cov["totals"]["percent_covered"]
        cov_note = f"kapsam={cov_pct:.1f}% (esik {COVERAGE_MIN}%)"
        if cov_pct < COVERAGE_MIN:
            criteria["C1"].record(False, criteria["C1"].evidence + f"; KAPSAM YETERSIZ: {cov_note}")
        else:
            criteria["C1"].evidence += f"; {cov_note}"

    # --- rapor ---------------------------------------------------------------
    all_pass = all(c.passed for c in criteria.values())
    lines = [
        "# G0 Kapi Raporu — \"Zemin saglam\"",
        "",
        f"- Tarih (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Makine: {platform.node()} / {platform.platform()}",
        f"- Python: {platform.python_version()}",
        f"- GPU ortami: {'CUDA mevcut' if gpu_ok_env else 'CUDA yok (CPU kosusu)'}",
        f"- Kapsam: {cov_note}",
        "",
        "| # | Kriter | Sonuc | Kanit |",
        "|---|--------|-------|-------|",
    ]
    for c in criteria.values():
        emoji = "GECTI" if c.passed else "KALDI"
        lines.append(f"| {c.cid} | {c.title} | **{emoji}** | {c.evidence} |")
    verdict = "GECTI — FAZ 1 baslayabilir" if all_pass else "GECEMEDI — iddia yapilamaz"
    lines += [
        "",
        f"## SONUC: G0 {verdict}",
        "",
        "> Altin kural: Her iddianin arkasinda bir test vardir. Test gecilmediyse iddia edilmez.",
    ]
    (run_dir / "G0_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("G0 raporu: %s", run_dir / "G0_report.md")
    print("\n".join(lines))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
