"""SoA parcacik deposu ve CPU<->GPU (Warp) koprusu (P0-FR-03).

Parcacik alanlari GPU'da coalesced erisim icin ayri diziler halinde tutulur
(Structure-of-Arrays). Bu faz alanlari TANIMLAR ve TAHSIS eder; fizik sonraki
fazlarda doldurur. Kopru kayipsizdir: CPU -> GPU -> CPU roundtrip bit-esittir.

Iki hassasiyet modu (DR-RIFT-P0 §5.3):
- "science":     kinematik alanlar FP64 (dogrulama, yayin, nihai tahmin zorunlu).
- "performance": kinematik alanlar FP32 (yalnizca bilim moduyla capraz kontrol sonrasi).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "PRECISION_MODES",
    "FIELD_GROUPS",
    "ParticleStore",
    "warp_available",
    "warp_devices",
    "roundtrip_via_warp",
]

PRECISION_MODES = ("science", "performance")

# Alan gruplari (DR-RIFT-P0 §5.2). Kinematik dtype hassasiyet moduna baglidir.
_KINEMATIC = ("x", "y", "z", "vx", "vy", "vz", "ax", "ay", "az")
_THERMO = ("rho", "u", "P", "cs")
_MATERIAL_FLOAT = ("h", "mass", "alpha_por", "D")
_SOLID = ("Sxx", "Syy", "Szz", "Sxy", "Sxz", "Syz")

FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "kinematic": _KINEMATIC,
    "thermo": _THERMO,
    "material": ("mat_id",) + _MATERIAL_FLOAT,
    "solid": _SOLID,
    "system": ("id", "active", "phase_flag"),
}

# faz bayragi degerleri (FAZ 2+ icin rezerve; burada yalnizca tanim)
PHASE_SPH = 0
PHASE_FRAGMENT = 1
PHASE_DEM = 2


def _dtype_map(precision: str) -> dict[str, np.dtype]:
    if precision not in PRECISION_MODES:
        raise ValueError(f"bilinmeyen hassasiyet modu: {precision!r} (gecerli: {PRECISION_MODES})")
    kin = np.dtype(np.float64) if precision == "science" else np.dtype(np.float32)
    m: dict[str, np.dtype] = {}
    for name in _KINEMATIC:
        m[name] = kin
    for name in _THERMO + _MATERIAL_FLOAT + _SOLID:
        m[name] = np.dtype(np.float64)
    m["mat_id"] = np.dtype(np.int32)
    m["id"] = np.dtype(np.int64)
    m["active"] = np.dtype(np.uint8)
    m["phase_flag"] = np.dtype(np.int8)
    return m


@dataclass
class ParticleStore:
    """SoA parcacik deposu. Alanlar `store.x`, `store.rho`, ... olarak erisilir."""

    n: int
    precision: str = "science"
    _fields: dict[str, np.ndarray] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.n < 0:
            raise ValueError(f"parcacik sayisi negatif olamaz: {self.n}")
        dtypes = _dtype_map(self.precision)
        for name, dt in dtypes.items():
            self._fields[name] = np.zeros(self.n, dtype=dt)
        # fiziksel olarak anlamli varsayilanlar
        self._fields["alpha_por"].fill(1.0)  # distansiyon >= 1
        self._fields["active"].fill(1)
        self._fields["id"][:] = np.arange(self.n, dtype=np.int64)

    # -- alan erisimi ------------------------------------------------------
    def __setattr__(self, name: str, value) -> None:
        # alan dizilerinin yanlislikla yeniden baglanmasini (shadowing) engelle:
        # dogru kullanim `store.x[:] = ...`
        fields = self.__dict__.get("_fields")
        if fields is not None and name in fields:
            raise AttributeError(
                f"alan dizisi yeniden baglanamaz: {name!r}; yerine store.{name}[:] = ... kullanin"
            )
        object.__setattr__(self, name, value)

    def __getattr__(self, name: str) -> np.ndarray:
        fields = object.__getattribute__(self, "_fields")
        if name in fields:
            return fields[name]
        raise AttributeError(f"ParticleStore alani degil: {name!r}")

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(self._fields)

    def dtype_of(self, name: str) -> np.dtype:
        return self._fields[name].dtype

    def as_dict(self) -> dict[str, np.ndarray]:
        """Alan adlarindan dizilere gorunum (kopya degil)."""
        return dict(self._fields)

    def copy(self) -> ParticleStore:
        out = ParticleStore(self.n, self.precision)
        for name, arr in self._fields.items():
            out._fields[name][...] = arr
        return out

    def equal_bitwise(self, other: ParticleStore) -> bool:
        """Tum alanlar bit duzeyinde esit mi? (roundtrip kaniti)"""
        if self.n != other.n or self.precision != other.precision:
            return False
        for name, arr in self._fields.items():
            b = other._fields[name]
            if arr.dtype != b.dtype or not np.array_equal(
                arr.view(np.uint8), b.view(np.uint8)
            ):
                return False
        return True


# ---------------------------------------------------------------------------
# Warp koprusu (yalnizca dogruluk odakli; performans optimizasyonu FAZ 1+)
# ---------------------------------------------------------------------------

_WARP_INITIALIZED = False


def _init_warp():
    """Warp'i tembel yukle; kernel onbellegini DARTRIFT_WARP_CACHE'e yonlendir."""
    global _WARP_INITIALIZED
    import warp as wp

    if not _WARP_INITIALIZED:
        cache = os.environ.get("DARTRIFT_WARP_CACHE")
        if cache:
            wp.config.kernel_cache_dir = cache
        wp.init()
        _WARP_INITIALIZED = True
    return wp


def warp_available() -> bool:
    """warp-lang import edilebilir ve init olabilir mi?"""
    try:
        _init_warp()
        return True
    except Exception:
        return False


def warp_devices() -> list[str]:
    """Kullanilabilir Warp cihaz adlari (or. ['cpu', 'cuda:0'])."""
    if not warp_available():
        return []
    wp = _init_warp()
    return [str(d) for d in wp.get_devices()]


_WP_DTYPES = {
    np.dtype(np.float64): "float64",
    np.dtype(np.float32): "float32",
    np.dtype(np.int64): "int64",
    np.dtype(np.int32): "int32",
    np.dtype(np.int8): "int8",
    np.dtype(np.uint8): "uint8",
}


def to_warp(store: ParticleStore, device: str) -> dict:
    """Depoyu verilen Warp cihazina kopyala (alan adi -> wp.array)."""
    wp = _init_warp()
    out = {}
    for name, arr in store.as_dict().items():
        wp_dtype = getattr(wp, _WP_DTYPES[arr.dtype])
        out[name] = wp.array(arr, dtype=wp_dtype, device=device)
    return out


def from_warp(warp_fields: dict, n: int, precision: str) -> ParticleStore:
    """Warp dizilerinden CPU deposuna geri kopyala."""
    out = ParticleStore(n, precision)
    for name, warr in warp_fields.items():
        host = warr.numpy()
        expected = out._fields[name].dtype
        if host.dtype != expected:
            raise TypeError(f"kopru dtype bozdu: {name} {host.dtype} != {expected}")
        out._fields[name][...] = host
    return out


def roundtrip_via_warp(store: ParticleStore, device: str) -> ParticleStore:
    """CPU -> device -> CPU tam tur; sonuc bit-esit olmalidir (P0-FR-03)."""
    return from_warp(to_warp(store, device), store.n, store.precision)
