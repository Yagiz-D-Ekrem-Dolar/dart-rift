"""Basarisiz kosunun dondurulmasi (DR-RIFT-P0 §6.2 son satiri).

Sartname sozde-kodu ihlal durumunda su davranisi zorunlu kilar:

    # ihlal -> kosuyu 'numerical_failure' etiketiyle durdur, config dondur

Ana Plan'in risk tablosu da ayni seyi soyler: "sok motoru kararsiz -> ...
failing config'i dondur". Yani bir invariant ihlali yalnizca istisna
firlatmakla kalmaz; o kosunun TAM baglami diske sabitlenir ki hata sonradan
birebir yeniden uretilebilsin.

Dondurulan paket (`run_dir` altinda):
    manifest.yaml         status=numerical_failure, config gomulu
    failing_config.yaml   kosuyu tetikleyen config'in kendisi
    violation_report.txt  ihlal eden alanlar, kural, parcacik indeksleri

Bu modul FAZ 0'da yazilir cunku FAZ 1'de ilk NaN goruldugunde hazir olmalidir.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .config import RunConfig, config_canonical_dict
from .invariants import InvariantReport
from .logging_cfg import build_manifest, write_manifest

__all__ = ["freeze_failed_run", "FrozenFailure"]

_log = logging.getLogger("dartrift")


class FrozenFailure:
    """Dondurulmus basarisiz kosunun dosya yollari."""

    def __init__(self, run_dir: Path, manifest: Path, config: Path, report: Path):
        self.run_dir, self.manifest, self.config, self.report = run_dir, manifest, config, report

    def __repr__(self) -> str:  # pragma: no cover - tanisal
        return f"FrozenFailure(run_dir={self.run_dir})"


def freeze_failed_run(
    cfg: RunConfig,
    report: InvariantReport,
    run_dir: str | Path,
    status: str = "numerical_failure",
    wall_time: float = 0.0,
) -> FrozenFailure:
    """Kosuyu 'numerical_failure' olarak muhurle ve config'i dondur.

    Basarili kosudan tek farki status alani DEGILDIR: basarisiz kosu da tam
    manifest uretir (Ek A), cunku "neden basarisiz oldu" sorusu ancak ayni
    alanlarla yanitlanabilir. Basarisizligi kaydetmemek, onu gizlemektir.
    """
    if report.ok:
        raise ValueError(
            "freeze_failed_run yalnizca ihlal iceren rapor icin cagrilir; "
            "temiz rapor basarisizlik olarak dondurulamaz"
        )
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(cfg, status=status, wall_time=wall_time)
    manifest_path = write_manifest(manifest, run_dir / "manifest.yaml")

    config_path = run_dir / "failing_config.yaml"
    config_path.write_text(
        yaml.safe_dump(config_canonical_dict(cfg), sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )

    lines = [
        f"run_id: {cfg.run_id}",
        f"status: {status}",
        f"step: {report.step}",
        f"level: {report.level}",
        f"random_seed: {cfg.random_seed}",
        "",
        "ihlaller:",
    ]
    for v in report.violations:
        idx = list(v.first_indices)
        lines.append(f"  - alan={v.field} kural={v.rule} sayi={v.count} ilk={idx}")
    report_path = run_dir / "violation_report.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    _log.error(
        "kosu %s olarak donduruldu (step=%s, %d ihlal): %s",
        status,
        report.step,
        len(report.violations),
        run_dir,
    )
    return FrozenFailure(run_dir, manifest_path, config_path, report_path)
