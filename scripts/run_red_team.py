"""Kirmizi-takim kontrol listesi kosucusu — DR-RIFT-P0 §12.

Yol Haritasi §7.5: "Her fazin kirmizi-takim kontrol listesi teslimden once
isletilir." Bu betik §12'deki bes maddeyi otomatik olarak sinar ve kanit
uretir. Kapi kosucusundan (run_g0_gate.py) ayridir: kapi "gereksinimler
karsilandi mi" diye sorar, kirmizi takim "bu sistemi nasil kandirabilirim"
diye sorar.

Kullanim:
    python scripts/run_red_team.py [--run-dir DIZIN]

Cikis kodu 0 = bes madde de temiz.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from golden_scenario import build_canonical_state, state_hash  # noqa: E402

from dartrift.config import ConfigError, config_hash, load_config  # noqa: E402
from dartrift.invariants import InvariantViolation, check_invariants  # noqa: E402
from dartrift.io_hdf5 import Hdf5Writer, LayerDisabledError  # noqa: E402
from dartrift.logging_cfg import (  # noqa: E402
    build_manifest,
    config_from_manifest,
    read_manifest,
    write_manifest,
)
from dartrift.particles import ParticleStore  # noqa: E402
from dartrift.rng import sample_uniform, sample_uniform_sharded  # noqa: E402

GOLDEN = REPO / "tests" / "golden" / "p0_canonical_v1.json"


class Check:
    def __init__(self, cid: str, question: str):
        self.cid, self.question = cid, question
        self.clean: bool | None = None
        self.evidence = ""

    def record(self, clean: bool, evidence: str) -> None:
        self.clean, self.evidence = clean, evidence


def rt1_cross_machine_hash() -> Check:
    """Ayni config + tohum iki farkli makinede ayni hash'i veriyor mu?"""
    c = Check("RT1", "Ayni config + tohum iki farkli makinede ayni hash'i veriyor mu?")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    current = state_hash(build_canonical_state())
    this_platform = f"{platform.system()}/CPython {platform.python_version()}"
    verified = golden.get("verified_on", [])
    matches = current == golden["sha256"]
    # Altin dosya baska bir platformda uretilmisti; bu kosu ikinci platformdur.
    others = [p for p in verified if p != this_platform]
    c.record(
        matches and bool(others),
        f"bu platform={this_platform}, hash={'ESLESTI' if matches else 'SAPTI'}; "
        f"daha once dogrulanan platformlar={verified or 'kayit yok'}",
    )
    return c


def rt2_shard_invariance() -> Check:
    """Shard sayisini degistirmek sonucu degistiriyor mu? (Degistirmemeli.)"""
    c = Check("RT2", "Shard sayisini degistirmek sonucu degistiriyor mu?")
    ref = sample_uniform(104729, "particles", 257)
    bad = []
    for n_shards in (1, 2, 3, 4, 5, 8, 16, 64, 257):
        got = sample_uniform_sharded(104729, "particles", 257, n_shards)
        if not np.array_equal(ref, got):
            bad.append(n_shards)
    c.record(not bad, f"denenen shard sayilari 1..257 (9 vaka); sapan={bad or 'yok'}")
    return c


def rt3_invalid_configs_rejected() -> Check:
    """Gecersiz her config gercekten reddediliyor mu, sessizce yutulmuyor mu?"""
    c = Check("RT3", "Gecersiz her config gercekten reddediliyor mu?")
    files = sorted((REPO / "configs" / "invalid").glob("*.yaml"))
    slipped = []
    for f in files:
        try:
            load_config(f)
            slipped.append(f.name)  # kabul edildiyse sema delinmis demektir
        except ConfigError:
            pass
    c.record(
        not slipped and len(files) >= 10,
        f"{len(files)} gecersiz vaka denendi; sessizce kabul edilen={slipped or 'yok'}",
    )
    return c


def rt4_manifest_reproduces_run(run_dir: Path) -> Check:
    """Manifest, kosuyu sifirdan yeniden uretmeye yetiyor mu?"""
    c = Check("RT4", "Manifest, kosuyu sifirdan yeniden uretmeye yetiyor mu?")
    cfg = load_config(REPO / "configs" / "p0_smoke.yaml")
    manifest = build_manifest(cfg, status="accepted", wall_time=0.0)
    path = write_manifest(manifest, run_dir / "rt4_manifest.yaml")

    # Orijinal YAML'a hic bakmadan, yalnizca manifestten geri kur:
    recovered = config_from_manifest(read_manifest(path))
    same_hash = config_hash(recovered) == config_hash(cfg)

    # Geri kurulan config gercekten ayni motoru kuruyor mu?
    same_store = (
        ParticleStore.from_config(recovered, 4).precision
        == ParticleStore.from_config(cfg, 4).precision
    )

    # Kurcalama tespiti calisiyor mu?
    tampered = read_manifest(path)
    tampered["config"]["random_seed"] += 1
    try:
        config_from_manifest(tampered)
        detects_tamper = False
    except ValueError:
        detects_tamper = True

    c.record(
        same_hash and same_store and detects_tamper,
        f"config manifestten geri kuruldu (hash {'ayni' if same_hash else 'FARKLI'}), "
        f"ayni depo modu={same_store}, kurcalama tespiti={detects_tamper}",
    )
    return c


def rt5_violation_halts_run() -> Check:
    """Bir invariant ihlali kosuyu durduruyor mu, yoksa devam mi ediyor?"""
    c = Check("RT5", "Bir invariant ihlali kosuyu durduruyor mu?")
    results = []
    injections = [
        ("rho", np.nan), ("rho", -1.0), ("mass", 0.0),
        ("D", 2.0), ("alpha_por", 0.5), ("u", np.inf),
    ]
    for field, value in injections:
        store = ParticleStore(8, "science")
        store.rho[:] = 2600.0
        store.mass[:] = 1.0
        store.as_dict()[field][3] = value
        try:
            check_invariants(store, step=1, level="science")
            results.append(f"{field}={value} KACTI")  # durdurmadiysa kusur
        except InvariantViolation:
            pass
    c.record(
        not results,
        f"{len(injections)} enjeksiyon denendi; yakalanmayan={results or 'yok'}",
    )
    return c


def rt6_disabled_layer_not_silent(run_dir: Path) -> Check:
    """Ek madde: config'de kapatilan bir katmana yazmak sessizce yutuluyor mu?"""
    c = Check("RT6", "Kapatilmis cikti katmanina yazmak sessizce yutuluyor mu?")
    cfg = load_config(REPO / "configs" / "p0_smoke.yaml")
    narrow_io = cfg.io.model_copy(update={"output_layers": ["scalar_budget"]})
    narrowed = cfg.model_copy(update={"io": narrow_io})
    silent = False
    with Hdf5Writer.from_config(narrowed, run_dir / "rt6.h5") as w:
        try:
            w.append_event(0, 0.0, "kapali_katman")
            silent = True  # hata vermediyse sessizce yutmus demektir
        except LayerDisabledError:
            pass
    verdict = "SESSIZCE YUTULDU" if silent else "acik hata verdi"
    c.record(not silent, f"kapali katmana yazma {verdict}")
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=None)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.run_dir) if args.run_dir else REPO / "gate_runs" / f"redteam_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    checks = [
        rt1_cross_machine_hash(),
        rt2_shard_invariance(),
        rt3_invalid_configs_rejected(),
        rt4_manifest_reproduces_run(run_dir),
        rt5_violation_halts_run(),
        rt6_disabled_layer_not_silent(run_dir),
    ]
    all_clean = all(c.clean for c in checks)

    lines = [
        "# Kirmizi-Takim Kontrol Listesi — FAZ 0 (DR-RIFT-P0 §12)",
        "",
        f"- Tarih (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Makine: {platform.node()} / {platform.platform()}",
        f"- Python: {platform.python_version()}",
        "",
        "| # | Soru | Sonuc | Kanit |",
        "|---|------|-------|-------|",
    ]
    for c in checks:
        verdict = "TEMIZ" if c.clean else "KUSUR"
        lines.append(f"| {c.cid} | {c.question} | **{verdict}** | {c.evidence} |")
    summary = "Tum maddeler temiz" if all_clean else "EN AZ BIR KUSUR VAR — teslim edilemez"
    lines += [
        "",
        f"## SONUC: {summary}",
        "",
        "> Kirmizi takim, gereksinimleri degil sistemin kandirilabilirligini sinar.",
    ]
    (run_dir / "red_team_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
