"""SI birim sistemi ve fiziksel sabitler — tek kaynak (P0-FR-01).

Tum ic hesap SI'da (kg, m, s, Pa, J) yapilir. Girdi/ciktida insan-okur birimler
(g/cm^3, km/s, GPa, ...) bu modul uzerinden donusturulur; cekirdek asla karisik
birim gormez. Boyut uyusmazligi `UnitError` uretir (Mars Climate Orbiter dersi).
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "Dimension",
    "Quantity",
    "UnitError",
    "DIMENSIONLESS",
    "MASS",
    "LENGTH",
    "TIME",
    "VELOCITY",
    "ACCELERATION",
    "DENSITY",
    "PRESSURE",
    "ENERGY",
    "SPECIFIC_ENERGY",
    "GRAVITATIONAL_PARAMETER",
    "G",
    "STANDARD_GRAVITY",
    "UNITS",
    "to_si",
    "from_si",
    "convert",
]


class UnitError(ValueError):
    """Boyut/birim uyusmazligi hatasi. Sessizce yutulmaz, acikca firlatilir."""


@dataclass(frozen=True)
class Dimension:
    """SI taban buyukluk uslari: kg^kg * m^m * s^s * K^K * A^A * mol^mol * cd^cd."""

    kg: int = 0
    m: int = 0
    s: int = 0
    K: int = 0
    A: int = 0
    mol: int = 0
    cd: int = 0

    def __mul__(self, other: Dimension) -> Dimension:
        return Dimension(
            self.kg + other.kg,
            self.m + other.m,
            self.s + other.s,
            self.K + other.K,
            self.A + other.A,
            self.mol + other.mol,
            self.cd + other.cd,
        )

    def __truediv__(self, other: Dimension) -> Dimension:
        return Dimension(
            self.kg - other.kg,
            self.m - other.m,
            self.s - other.s,
            self.K - other.K,
            self.A - other.A,
            self.mol - other.mol,
            self.cd - other.cd,
        )

    def __pow__(self, n: int) -> Dimension:
        return Dimension(
            self.kg * n, self.m * n, self.s * n, self.K * n, self.A * n, self.mol * n, self.cd * n
        )

    def __str__(self) -> str:
        parts = []
        for name in ("kg", "m", "s", "K", "A", "mol", "cd"):
            e = getattr(self, name)
            if e == 1:
                parts.append(name)
            elif e != 0:
                parts.append(f"{name}^{e}")
        return " ".join(parts) if parts else "1"


DIMENSIONLESS = Dimension()
MASS = Dimension(kg=1)
LENGTH = Dimension(m=1)
TIME = Dimension(s=1)
VELOCITY = LENGTH / TIME
ACCELERATION = VELOCITY / TIME
DENSITY = MASS / LENGTH**3
PRESSURE = MASS / (LENGTH * TIME**2)
ENERGY = MASS * VELOCITY**2
SPECIFIC_ENERGY = ENERGY / MASS
GRAVITATIONAL_PARAMETER = LENGTH**3 / (MASS * TIME**2)


@dataclass(frozen=True)
class Quantity:
    """Boyut tasiyan skaler. Aritmetik islemler boyut tutarliligini zorlar."""

    value: float
    dim: Dimension

    def _require_same_dim(self, other: Quantity, op: str) -> None:
        if not isinstance(other, Quantity):
            raise UnitError(f"Quantity {op} icin Quantity gerekli, {type(other).__name__} verildi")
        if self.dim != other.dim:
            raise UnitError(f"boyut uyusmazligi: [{self.dim}] {op} [{other.dim}]")

    def __add__(self, other: Quantity) -> Quantity:
        self._require_same_dim(other, "+")
        return Quantity(self.value + other.value, self.dim)

    def __sub__(self, other: Quantity) -> Quantity:
        self._require_same_dim(other, "-")
        return Quantity(self.value - other.value, self.dim)

    def __mul__(self, other: Quantity | float | int) -> Quantity:
        if isinstance(other, Quantity):
            return Quantity(self.value * other.value, self.dim * other.dim)
        return Quantity(self.value * float(other), self.dim)

    __rmul__ = __mul__

    def __truediv__(self, other: Quantity | float | int) -> Quantity:
        if isinstance(other, Quantity):
            return Quantity(self.value / other.value, self.dim / other.dim)
        return Quantity(self.value / float(other), self.dim)

    def __pow__(self, n: int) -> Quantity:
        return Quantity(self.value**n, self.dim**n)


# ---------------------------------------------------------------------------
# Fiziksel sabitler (SI, CODATA 2018)
# ---------------------------------------------------------------------------

G = Quantity(6.674_30e-11, GRAVITATIONAL_PARAMETER)
"""Newton kutlecekim sabiti [m^3 kg^-1 s^-2]."""

STANDARD_GRAVITY = Quantity(9.806_65, ACCELERATION)
"""Standart yercekimi ivmesi g0 [m s^-2]."""


# ---------------------------------------------------------------------------
# Birim kayit tablosu: ad -> (SI'ya carpan, boyut)
# ---------------------------------------------------------------------------

UNITS: dict[str, tuple[float, Dimension]] = {
    # kutle
    "kg": (1.0, MASS),
    "g": (1.0e-3, MASS),
    "t": (1.0e3, MASS),
    # uzunluk
    "m": (1.0, LENGTH),
    "cm": (1.0e-2, LENGTH),
    "km": (1.0e3, LENGTH),
    # zaman
    "s": (1.0, TIME),
    "min": (60.0, TIME),
    "h": (3600.0, TIME),
    # hiz
    "m/s": (1.0, VELOCITY),
    "km/s": (1.0e3, VELOCITY),
    # yogunluk
    "kg/m^3": (1.0, DENSITY),
    "g/cm^3": (1.0e3, DENSITY),
    # basinc
    "Pa": (1.0, PRESSURE),
    "kPa": (1.0e3, PRESSURE),
    "MPa": (1.0e6, PRESSURE),
    "GPa": (1.0e9, PRESSURE),
    # enerji
    "J": (1.0, ENERGY),
    "kJ": (1.0e3, ENERGY),
    "MJ": (1.0e6, ENERGY),
    # ozgul ic enerji
    "J/kg": (1.0, SPECIFIC_ENERGY),
    "MJ/kg": (1.0e6, SPECIFIC_ENERGY),
}


def _lookup(unit: str) -> tuple[float, Dimension]:
    try:
        return UNITS[unit]
    except KeyError:
        raise UnitError(f"bilinmeyen birim: {unit!r} (kayitli birimler: {sorted(UNITS)})") from None


def to_si(value: float, unit: str) -> Quantity:
    """Insan-okur birimden SI Quantity'ye donustur."""
    factor, dim = _lookup(unit)
    return Quantity(float(value) * factor, dim)


def from_si(quantity: Quantity, unit: str) -> float:
    """SI Quantity'den hedef birime donustur; boyut uyusmazligi UnitError."""
    factor, dim = _lookup(unit)
    if quantity.dim != dim:
        raise UnitError(
            f"boyut uyusmazligi: [{quantity.dim}] degeri {unit!r} ([{dim}]) birimine cevrilemez"
        )
    return quantity.value / factor


def convert(value: float, src: str, dst: str) -> float:
    """Iki insan-okur birim arasinda donusum (ayni boyutta olmali)."""
    return from_si(to_si(value, src), dst)
