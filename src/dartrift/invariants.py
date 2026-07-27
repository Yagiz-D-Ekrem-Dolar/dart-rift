"""Degismez (invariant) ve korunum denetim cercevesi (P0-FR-05).

Her adimda cagrilabilir: NaN/Inf, negatif kutle/yogunluk, hasar araligi,
distansiyon alt siniri ve (bilim modunda) parcacik sinir ihlali denetlenir.
Ihlal durumunda kosu 'numerical_failure' etiketiyle DURDURULUR — sessiz devam yok.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .particles import ParticleStore

__all__ = [
    "InvariantViolation",
    "Violation",
    "InvariantReport",
    "check_invariants",
]

_MAX_REPORT_INDICES = 8


class InvariantViolation(RuntimeError):
    """En az bir invariant ihlal edildi; kosu durdurulmalidir."""

    def __init__(self, report: InvariantReport):
        self.report = report
        super().__init__(str(report))


@dataclass(frozen=True)
class Violation:
    field: str
    rule: str
    count: int
    first_indices: tuple[int, ...]

    def __str__(self) -> str:
        idx = list(self.first_indices)
        return f"{self.field}: {self.rule} ({self.count} parcacik; ilk indeksler {idx})"


@dataclass
class InvariantReport:
    step: int
    level: str
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def __str__(self) -> str:
        if self.ok:
            return f"invariants OK (step={self.step}, level={self.level})"
        lines = [f"INVARIANT IHLALI (step={self.step}, level={self.level}):"]
        lines += [f"  - {v}" for v in self.violations]
        return "\n".join(lines)


def _record(report: InvariantReport, mask: np.ndarray, fieldname: str, rule: str) -> None:
    if mask.any():
        idx = np.flatnonzero(mask)
        report.violations.append(
            Violation(
                field=fieldname,
                rule=rule,
                count=int(idx.size),
                first_indices=tuple(int(i) for i in idx[:_MAX_REPORT_INDICES]),
            )
        )


def check_invariants(
    store: ParticleStore,
    step: int = 0,
    level: str = "science",
    domain: tuple[np.ndarray, np.ndarray] | None = None,
    raise_on_violation: bool = True,
) -> InvariantReport:
    """Depoyu denetle; ihlalde InvariantViolation firlat (veya raporu dondur).

    domain: (min_xyz, max_xyz) — yalnizca level="science" ve domain verilmisse
    parcacik konum siniri denetlenir (DR-RIFT-P0 §6.2).
    """
    if level not in ("science", "performance"):
        raise ValueError(f"bilinmeyen denetim seviyesi: {level!r}")

    report = InvariantReport(step=step, level=level)
    active = store.active.astype(bool)

    rho = store.rho
    _record(report, active & ~np.isfinite(rho), "rho", "yogunluk NaN/Inf")
    _record(report, active & np.isfinite(rho) & (rho <= 0.0), "rho", "yogunluk <= 0")

    _record(report, active & ~np.isfinite(store.u), "u", "ic enerji NaN/Inf")

    mass = store.mass
    _record(report, active & ~np.isfinite(mass), "mass", "kutle NaN/Inf")
    _record(report, active & np.isfinite(mass) & (mass <= 0.0), "mass", "kutle <= 0")

    D = store.D
    _record(report, active & (~np.isfinite(D) | (D < 0.0) | (D > 1.0)), "D", "hasar [0,1] disi")

    ap = store.alpha_por
    _record(
        report, active & (~np.isfinite(ap) | (ap < 1.0)), "alpha_por", "distansiyon < 1"
    )

    for name in ("x", "y", "z", "vx", "vy", "vz"):
        _record(report, active & ~np.isfinite(getattr(store, name)), name, "kinematik NaN/Inf")

    if level == "science" and domain is not None:
        mn, mx = np.asarray(domain[0], dtype=np.float64), np.asarray(domain[1], dtype=np.float64)
        pos_ok = (
            (store.x >= mn[0]) & (store.x <= mx[0])
            & (store.y >= mn[1]) & (store.y <= mx[1])
            & (store.z >= mn[2]) & (store.z <= mx[2])
        )
        _record(report, active & ~pos_ok, "x/y/z", "parcacik alan disina kacti")

    if not report.ok and raise_on_violation:
        raise InvariantViolation(report)
    return report
