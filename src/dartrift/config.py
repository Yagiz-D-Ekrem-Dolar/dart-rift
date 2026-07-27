"""Surumlu YAML config semasi ve dogrulayici (P0-FR-02, P0-DR-01).

Eksik alan, yanlis tip veya aralik disi deger ACIK hata uretir; sessiz yutma yok.
`schema_version` zorunludur ve desteklenen surumle eslesmelidir.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from . import SCHEMA_VERSION

__all__ = [
    "ConfigError",
    "NumericsConfig",
    "IoConfig",
    "DomainConfig",
    "RunConfig",
    "load_config",
    "config_canonical_dict",
    "config_hash",
]

OUTPUT_LAYERS = ("scalar_budget", "sparse_snapshot", "event_catalog")

PrecisionMode = Literal["deterministic_fp64", "performance_mixed"]

# Config'deki hassasiyet adi ile parcacik deposunun mod adi arasindaki TEK
# kopru. Ayri isim uzaylari olmasi bilincli: config bilimsel niyeti
# (deterministik mi, performans mi), depo bellek yerlesimini adlandirir.
# Koprunun tek yerde durmasi, "config bir sey soyluyor ama motor baskasini
# yapiyor" sessiz sapmasini engeller (bkz. tests/test_config_wiring.py).
_PRECISION_TO_STORE_MODE: dict[str, str] = {
    "deterministic_fp64": "science",
    "performance_mixed": "performance",
}


class ConfigError(ValueError):
    """Config dogrulama hatasi — okunur mesajlarla."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class NumericsConfig(_StrictModel):
    """Sayisal cekirdek secenekleri. `kernel` ve `cfl` FAZ 1'de dolar."""

    precision: PrecisionMode
    kernel: str | None = None
    cfl: float | None = Field(default=None, gt=0.0, le=1.0)


class DomainConfig(_StrictModel):
    """Bilim modunda parcacik sinir denetimi icin eksen-hizali kutu [m]."""

    min: list[float] = Field(min_length=3, max_length=3)
    max: list[float] = Field(min_length=3, max_length=3)

    @field_validator("max")
    @classmethod
    def _max_gt_min(cls, v: list[float], info) -> list[float]:
        mn = info.data.get("min")
        if mn is not None and any(hi <= lo for lo, hi in zip(mn, v, strict=True)):
            raise ValueError(
                f"domain.max her eksende domain.min'den buyuk olmali: min={mn} max={v}"
            )
        return v


class IoConfig(_StrictModel):
    """HDF5 cikti katmanlari (P0-FR-07 ile uyumlu)."""

    output_layers: list[Literal["scalar_budget", "sparse_snapshot", "event_catalog"]] = Field(
        default=list(OUTPUT_LAYERS), min_length=1
    )
    hdf5_compression: Literal["gzip", "lzf", "none"] = "gzip"

    @field_validator("output_layers")
    @classmethod
    def _unique_layers(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError(f"output_layers tekrarli katman iceremez: {v}")
        return v


class RunConfig(_StrictModel):
    """Bir kosunun tam tanimi. Ek B ornek iskeletiyle uyumlu."""

    schema_version: int
    run_id: str = Field(pattern=r"^[A-Za-z0-9_\-]{1,64}$")
    random_seed: int = Field(ge=0, lt=2**63)
    numerics: NumericsConfig
    io: IoConfig = Field(default_factory=IoConfig)
    domain: DomainConfig | None = None

    @field_validator("schema_version")
    @classmethod
    def _supported_schema(cls, v: int) -> int:
        if v != SCHEMA_VERSION:
            raise ValueError(
                f"desteklenmeyen schema_version={v}; bu surum yalnizca {SCHEMA_VERSION} destekler"
            )
        return v

    @property
    def store_precision(self) -> str:
        """Parcacik deposunun bekledigi hassasiyet modu ("science"/"performance")."""
        return _PRECISION_TO_STORE_MODE[self.numerics.precision]

    @property
    def domain_bounds(self) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
        """Invariant denetleyicisinin bekledigi (min_xyz, max_xyz) ikilisi; yoksa None."""
        if self.domain is None:
            return None
        return (tuple(self.domain.min), tuple(self.domain.max))  # type: ignore[return-value]


def _format_validation_error(err: ValidationError, source: str) -> str:
    lines = [f"config dogrulama hatasi ({source}): {err.error_count()} sorun"]
    for e in err.errors():
        loc = ".".join(str(p) for p in e["loc"]) or "<kok>"
        lines.append(f"  - {loc}: {e['msg']}")
    return "\n".join(lines)


def load_config(path: str | Path) -> RunConfig:
    """YAML dosyasini yukle ve semaya karsi dogrula; hatada ConfigError firlat."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"config dosyasi bulunamadi: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML ayrisTirma hatasi ({path}): {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(
            f"config bir anahtar-deger haritasi olmali ({path}), {type(raw).__name__} bulundu"
        )
    try:
        return RunConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(exc, str(path))) from exc


def config_canonical_dict(cfg: RunConfig) -> dict:
    """Hash icin kanonik (tamamen cozulmus, varsayilanlar dahil) sozluk."""
    return cfg.model_dump(mode="json")


def config_hash(cfg: RunConfig) -> str:
    """Kanonik JSON uzerinden SHA-256 (manifest'te config kimligi olarak kullanilir)."""
    canon = json.dumps(config_canonical_dict(cfg), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("kullanim: python -m dartrift.config <config.yaml>")
        return 2
    try:
        cfg = load_config(argv[0])
    except ConfigError as exc:
        print(f"GECERSIZ: {exc}")
        return 1
    print(f"GECERLI: run_id={cfg.run_id} schema_version={cfg.schema_version}")
    print(f"config_hash={config_hash(cfg)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_main(sys.argv[1:]))
