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
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

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
    """Sayisal cekirdek secenekleri.

    FAZ 1 (DR-RIFT-P1) alanlari: `kernel` yalnizca wendland_c2 olabilir (kilitli
    karar; kubik spline yalnizca karsilastirma icindir ve config'ten secilemez),
    `alpha_av`/`beta_av` Monaghan yapay viskozite katsayilaridir (§2.5, tipik
    1.0/2.0; benchmark ile ayarlanir ve RAPORLANIR).
    """

    precision: PrecisionMode
    kernel: Literal["wendland_c2"] | None = None
    cfl: float | None = Field(default=None, gt=0.0, le=1.0)
    alpha_av: float = Field(default=1.0, ge=0.0, le=5.0)
    beta_av: float = Field(default=2.0, ge=0.0, le=10.0)


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


class TillotsonConfig(_StrictModel):
    """Tillotson EOS parametreleri (varsayilan: bazalt, Benz & Asphaug 1999)."""

    rho0: float = Field(default=2700.0, gt=0)
    A: float = Field(default=2.67e10, gt=0)
    B: float = Field(default=2.67e10, ge=0)
    a: float = Field(default=0.5, gt=0)
    b: float = Field(default=1.5, ge=0)
    u0: float = Field(default=4.87e8, gt=0)
    u_iv: float = Field(default=4.72e6, gt=0)
    u_cv: float = Field(default=1.82e7, gt=0)
    alpha_t: float = Field(default=5.0, gt=0)
    beta_t: float = Field(default=5.0, gt=0)
    cs_floor_frac: float = Field(default=0.05, gt=0, le=1.0)

    @field_validator("u_cv")
    @classmethod
    def _ucv_gt_uiv(cls, v: float, info) -> float:
        uiv = info.data.get("u_iv")
        if uiv is not None and v <= uiv:
            raise ValueError(f"u_cv > u_iv olmali: u_cv={v}, u_iv={uiv}")
        return v


class StrengthConfig(_StrictModel):
    """Lundborg/Collins dayanim (P2 §2.2). enabled=false -> ablasyon."""

    enabled: bool = True
    Y0: float = Field(default=1.0e5, ge=0)
    mu_f: float = Field(default=0.8, ge=0, le=2.0)
    YM: float = Field(default=1.5e9, gt=0)
    shear_G: float = Field(default=2.27e10, gt=0)
    jaumann: bool = True  # yalnizca objektiflik ablasyonu icin kapatilir


class PorosityConfig(_StrictModel):
    """P-alpha crush-curve (P2 §2.4)."""

    enabled: bool = True
    alpha0: float = Field(default=1.5, ge=1.0, le=5.0)
    Pe: float = Field(default=1.0e6, gt=0)
    Ps: float = Field(default=1.0e8, gt=0)
    n_exp: float = Field(default=2.0, gt=0)

    @field_validator("Ps")
    @classmethod
    def _ps_gt_pe(cls, v: float, info) -> float:
        pe = info.data.get("Pe")
        if pe is not None and v <= pe:
            raise ValueError(f"Ps > Pe olmali: Ps={v}, Pe={pe}")
        return v


class GravityConfig(_StrictModel):
    """Oz-yercekimi (P2 §2.5)."""

    enabled: bool = True
    G: float = Field(default=6.674_30e-11, gt=0)
    eps: float = Field(default=0.0, ge=0)
    mode: Literal["direct", "barnes_hut"] = "direct"
    theta: float = Field(default=0.5, gt=0, le=1.0)


class DamageConfig(_StrictModel):
    """Grady-Kipp hasar + Weibull kusurlari (Benz & Asphaug 1995)."""

    enabled: bool = False
    k_weibull: float = Field(default=1.0e29, gt=0.0)   # [1/m^3]
    m_weibull: float = Field(default=9.0, gt=0.0)
    crack_speed_frac: float = Field(default=0.4, gt=0.0, le=1.0)
    n_flaws_per_particle: float = Field(default=10.0, gt=0.0)


class ArtificialStressConfig(_StrictModel):
    """Monaghan (2000) yapay gerilmesi — cekme kararsizligi (P1/P2 §9)."""

    enabled: bool = False
    eps: float = Field(default=0.3, ge=0.0, le=1.0)
    n_exp: float = Field(default=4.0, gt=0.0, le=8.0)
    dp_over_h: float = Field(default=0.5, gt=0.0, le=1.0)


class PhysicsConfig(_StrictModel):
    """FAZ 2 fizik modulleri; her biri ablasyonla acilir/kapanir (P2-FR-06)."""

    eos: Literal["ideal_gas", "linear", "tillotson"] = "ideal_gas"
    gamma: float = Field(default=1.4, gt=1.0)
    c0: float = Field(default=1.0, gt=0)
    rho0_linear: float = Field(default=1.0, gt=0)
    tillotson: TillotsonConfig = Field(default_factory=TillotsonConfig)
    strength: StrengthConfig = Field(default_factory=lambda: StrengthConfig(enabled=False))
    porosity: PorosityConfig = Field(default_factory=lambda: PorosityConfig(enabled=False))
    gravity: GravityConfig = Field(default_factory=lambda: GravityConfig(enabled=False))
    damage: DamageConfig = Field(default_factory=DamageConfig)
    artificial_stress: ArtificialStressConfig = Field(
        default_factory=ArtificialStressConfig
    )
    # ADR-0015: serbest yuzeyli kati senaryolarinda "continuity" gerekir;
    # summation, yuzeyde rho'yu ~0.39 rho0'a dusurup yapay cekme uretir.
    density_method: Literal["summation", "continuity"] = "summation"


SCENARIOS = ("sod_shock_tube", "sedov_blast", "plate_impact", "conservation_cloud")


class TargetConfig(_StrictModel):
    """Hedef cisim: sekil + moloz yigini (FAZ 3, P3-FR-01..04)."""

    shape: Literal["icosphere", "ellipsoid", "obj"] = "icosphere"
    obj_path: str | None = None            # shape="obj" ise zorunlu
    # PDS'in DART sekil modelleri KILOMETRE cinsindendir. Varsayilan "m"
    # birakildi ki sessiz bir donusum olmasin: gercek PDS dosyasi kullanan
    # config'in "km" YAZMASI gerekir. Metre saymak cismi 1000 kat kucultur.
    obj_units: Literal["m", "km"] = "m"
    radius: float | None = Field(default=None, gt=0.0)          # icosphere
    semi_axes: list[float] | None = Field(default=None, min_length=3, max_length=3)
    subdiv: int = Field(default=4, ge=0, le=7)
    spacing: float = Field(gt=0.0)
    bulk_density: float = Field(gt=0.0)
    model_class: Literal["M0", "M1"] = "M0"
    matrix_alpha0: float = Field(default=1.6, ge=1.0)
    matrix_Y0: float = Field(default=1.0e4, gt=0.0)
    boulder_alpha0: float = Field(default=1.05, ge=1.0)
    boulder_Y0: float = Field(default=1.0e7, gt=0.0)
    f_boulder: float = Field(default=0.0, ge=0.0, lt=1.0)
    q: float = Field(default=3.0, gt=0.0)
    r_min: float | None = Field(default=None, gt=0.0)
    r_max: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def _shape_args_present(self) -> TargetConfig:
        if self.shape == "icosphere" and self.radius is None:
            raise ValueError("shape=icosphere icin radius zorunlu")
        if self.shape == "ellipsoid" and self.semi_axes is None:
            raise ValueError("shape=ellipsoid icin semi_axes zorunlu")
        if self.shape == "obj" and not self.obj_path:
            raise ValueError("shape=obj icin obj_path zorunlu")
        if self.model_class == "M1" and self.f_boulder <= 0.0:
            raise ValueError("model_class=M1 icin f_boulder > 0 olmali")
        if self.r_min is not None and self.r_max is not None and self.r_min >= self.r_max:
            raise ValueError(f"r_min < r_max olmali ({self.r_min} >= {self.r_max})")
        return self


class ImpactorConfig(_StrictModel):
    """Mermi ve carpma geometrisi (FAZ 3, P3-FR-06/07).

    `n_particles` >= 8: nokta parcacik P3-FR-06 ile YASAKTIR ve sema bunu
    kabul etmez — yasagi yalnizca kodda birakmak, bir config ile atlanabilir
    olmasi demekti.
    """

    n_particles: int = Field(ge=8)
    mass: float = Field(default=579.4, gt=0.0)
    speed: float = Field(default=6144.9, gt=0.0)
    density: float = Field(default=2700.0, gt=0.0)
    aim: list[float] = Field(default=[0.0, 0.0, 1.0], min_length=3, max_length=3)
    angle_deg: float = Field(default=0.0, ge=0.0, lt=90.0)
    azimuth_deg: float = Field(default=0.0, ge=0.0, lt=360.0)
    standoff: float | None = Field(default=None, gt=0.0)


class SettlingConfig(_StrictModel):
    """Denge sinamasi penceresi (FAZ 3, P3-FR-05; kapsam icin ADR-0024)."""

    enabled: bool = True
    damping: float = Field(default=0.02, ge=0.0, lt=1.0)
    max_steps: int = Field(default=400, ge=1)
    ke_frac: float = Field(default=1.0e-3, gt=0.0)
    gravity_rebuild_every: int = Field(default=1, ge=1)
    gravity_drift_tol: float = Field(default=0.25, gt=0.0)


class SceneConfig(_StrictModel):
    """FAZ 3 sahnesi: hedef + settling + mermi."""

    target: TargetConfig
    impactor: ImpactorConfig
    settling: SettlingConfig = Field(default_factory=SettlingConfig)


class RunConfig(_StrictModel):
    """Bir kosunun tam tanimi. FAZ 0 Ek B + FAZ 1 Ek A iskeletleriyle uyumlu."""

    schema_version: int
    run_id: str = Field(pattern=r"^[A-Za-z0-9_\-]{1,64}$")
    random_seed: int = Field(ge=0, lt=2**63)
    numerics: NumericsConfig
    io: IoConfig = Field(default_factory=IoConfig)
    domain: DomainConfig | None = None
    physics: PhysicsConfig = Field(default_factory=PhysicsConfig)
    # FAZ 1 Ek A: dogrulama senaryosu ve cozunurluk merdiveni
    test: Literal["sod_shock_tube", "sedov_blast", "plate_impact", "conservation_cloud"] | None = (
        None
    )
    resolution: list[int] | None = Field(default=None, min_length=1)
    # FAZ 3 Ek A: sahne kurulumu (hedef + settling + mermi)
    scene: SceneConfig | None = None

    @field_validator("resolution")
    @classmethod
    def _positive_resolutions(cls, v: list[int] | None) -> list[int] | None:
        if v is not None and any(r < 8 for r in v):
            raise ValueError(f"cozunurluk >= 8 olmali: {v}")
        return v

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
