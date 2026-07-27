"""Yapilandirilmis loglama ve kosu manifesti uretimi (P0-FR-06, P0-DR-02, Ek A).

Her kosu; kod SHA'si, config hash'i, donanim bilgisi ve zaman damgasi iceren bir
`manifest.yaml` uretir. Manifest, kosuyu sifirdan yeniden uretmeye yetecek her
alani icermek ZORUNDADIR (Ek A). Eksik alan `validate_manifest` ile yakalanir.
"""

from __future__ import annotations

import json
import logging
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

from .config import RunConfig, config_hash

__all__ = [
    "setup_logging",
    "get_git_sha",
    "detect_hardware",
    "build_manifest",
    "validate_manifest",
    "write_manifest",
    "read_manifest",
    "REQUIRED_MANIFEST_FIELDS",
    "MANIFEST_STATUSES",
]

MANIFEST_STATUSES = ("accepted", "numerical_failure", "physical_reject")

# Ek A — zorunlu alanlar (noktali yol gosterimi)
REQUIRED_MANIFEST_FIELDS = (
    "run_id",
    "git_sha",
    "build.compiler",
    "build.cuda",
    "build.flags",
    "hardware.gpu",
    "hardware.driver",
    "physics",
    "numerics.kernel",
    "numerics.cfl",
    "numerics.precision",
    "random_seed",
    "data",
    "outputs.checkpoint_sha256",
    "outputs.observables_sha256",
    "status",
    "wall_time",
    "timestamp_utc",
)


class _JsonLineFormatter(logging.Formatter):
    """Bir satir = bir JSON kaydi (denetlenebilir log)."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def setup_logging(
    run_dir: str | Path | None = None,
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    """'dartrift' kok loglayicisini kur; run_dir verilirse JSONL dosyasina da yaz."""
    logger = logging.getLogger("dartrift")
    logger.setLevel(level)
    logger.handlers.clear()
    if console:
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(sh)
    if run_dir is not None:
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(run_dir / "run.log.jsonl", encoding="utf-8")
        fh.setFormatter(_JsonLineFormatter())
        logger.addHandler(fh)
    return logger


def get_git_sha(strict: bool = False) -> str:
    """Depo HEAD SHA'sini dondur; repo yoksa DARTRIFT_GIT_SHA ortam degiskeni.

    strict=True (bilim modu) iken SHA bulunamazsa hata — kaynagi belirsiz kosu
    manifesti kabul edilmez.
    """
    import os

    env = os.environ.get("DARTRIFT_GIT_SHA")
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).resolve().parent,
        )
        if out.returncode == 0:
            sha = out.stdout.strip()
            dirty = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=Path(__file__).resolve().parent,
            )
            if dirty.returncode == 0 and dirty.stdout.strip():
                sha += "-dirty"
            return sha
    except (OSError, subprocess.TimeoutExpired):
        pass
    if env:
        return env
    if strict:
        raise RuntimeError(
            "git SHA belirlenemedi (repo yok ve DARTRIFT_GIT_SHA tanimsiz); "
            "bilim modunda kaynagi belirsiz kosu kabul edilmez"
        )
    return "unknown"


def detect_hardware() -> dict:
    """GPU adi ve surucu surumunu tespit et (nvidia-smi; yoksa 'none')."""
    gpu, driver = "none", "none"
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if out.returncode == 0 and out.stdout.strip():
            first = out.stdout.strip().splitlines()[0]
            parts = [p.strip() for p in first.split(",")]
            if len(parts) >= 2:
                gpu, driver = parts[0], parts[1]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {"gpu": gpu, "driver": driver, "cpu": platform.processor() or platform.machine()}


def _cuda_runtime_version() -> str:
    try:
        import warp as wp  # noqa: F401

        ver = getattr(wp.config, "cuda_toolkit_version", None) or getattr(
            wp, "get_cuda_toolkit_version", lambda: None
        )()
        if ver:
            return str(ver)
    except Exception:
        pass
    return "none"


def build_manifest(
    cfg: RunConfig,
    status: str = "accepted",
    wall_time: float = 0.0,
    checkpoint_sha256: str = "",
    observables_sha256: str = "",
    physics: dict | None = None,
    data: dict | None = None,
    strict_git: bool = False,
) -> dict:
    """Ek A'daki TUM zorunlu alanlari iceren manifest sozlugu kur."""
    if status not in MANIFEST_STATUSES:
        raise ValueError(f"gecersiz status: {status!r} (gecerli: {MANIFEST_STATUSES})")
    manifest = {
        "run_id": cfg.run_id,
        "git_sha": get_git_sha(strict=strict_git),
        "config_hash": config_hash(cfg),
        "schema_version": cfg.schema_version,
        "build": {
            "compiler": f"cpython-{platform.python_version()}",
            "cuda": _cuda_runtime_version(),
            "flags": f"numpy-{np.__version__};precision={cfg.numerics.precision}",
        },
        "hardware": detect_hardware(),
        "physics": (
            physics if physics is not None else {"enabled": False, "note": "FAZ 0: fizik yok"}
        ),
        "numerics": {
            "kernel": cfg.numerics.kernel,
            "cfl": cfg.numerics.cfl,
            "precision": cfg.numerics.precision,
        },
        "random_seed": cfg.random_seed,
        "data": data if data is not None else {},
        "outputs": {
            "checkpoint_sha256": checkpoint_sha256,
            "observables_sha256": observables_sha256,
        },
        "status": status,
        "wall_time": float(wall_time),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    return manifest


def _get_dotted(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def validate_manifest(manifest: dict) -> list[str]:
    """Ek A alan tamligini denetle; eksik alanlarin listesini dondur (bos = tam)."""
    missing = []
    for dotted in REQUIRED_MANIFEST_FIELDS:
        try:
            _get_dotted(manifest, dotted)
        except KeyError:
            missing.append(dotted)
    status = manifest.get("status")
    if status is not None and status not in MANIFEST_STATUSES:
        missing.append(f"status(gecersiz deger: {status!r})")
    return missing


def write_manifest(manifest: dict, path: str | Path) -> Path:
    """Manifesti YAML olarak yaz; oncesinde alan tamligini zorla."""
    missing = validate_manifest(manifest)
    if missing:
        raise ValueError(f"manifest eksik/gecersiz alanlar iceriyor: {missing}")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(manifest, sort_keys=True, allow_unicode=True), encoding="utf-8"
    )
    return path


def read_manifest(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


class Stopwatch:
    """wall_time olcumu icin kucuk yardimci."""

    def __enter__(self) -> Stopwatch:
        self._t0 = time.perf_counter()
        self.elapsed = 0.0
        return self

    def __exit__(self, *exc) -> None:
        self.elapsed = time.perf_counter() - self._t0
