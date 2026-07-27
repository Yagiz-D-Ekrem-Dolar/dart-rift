"""P0-FR-03: SoA parcacik deposu + CPU<->GPU roundtrip (bit-esit)."""

import numpy as np
import pytest
from conftest import make_valid_store

from dartrift.particles import (
    FIELD_GROUPS,
    ParticleStore,
    roundtrip_via_warp,
    warp_available,
    warp_devices,
)

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp-lang kurulu/init degil")


class TestAllocation:
    def test_all_spec_fields_present(self):
        store = ParticleStore(4)
        for group, names in FIELD_GROUPS.items():
            for name in names:
                assert name in store.field_names, f"{group}/{name} eksik"

    def test_science_dtypes(self):
        s = ParticleStore(4, "science")
        assert s.dtype_of("x") == np.float64
        assert s.dtype_of("vx") == np.float64
        assert s.dtype_of("rho") == np.float64
        assert s.dtype_of("Sxy") == np.float64
        assert s.dtype_of("mat_id") == np.int32
        assert s.dtype_of("id") == np.int64
        assert s.dtype_of("active") == np.uint8
        assert s.dtype_of("phase_flag") == np.int8

    def test_performance_dtypes(self):
        s = ParticleStore(4, "performance")
        assert s.dtype_of("x") == np.float32  # kinematik FP32
        assert s.dtype_of("rho") == np.float64  # termodinamik FP64 kalir

    def test_physical_defaults(self):
        s = ParticleStore(8)
        assert np.all(s.alpha_por == 1.0)  # distansiyon >= 1
        assert np.all(s.active == 1)
        assert np.array_equal(s.id, np.arange(8))

    def test_zero_particles_ok(self):
        s = ParticleStore(0)
        assert s.x.size == 0

    def test_negative_n_raises(self):
        with pytest.raises(ValueError, match="negatif"):
            ParticleStore(-1)

    def test_unknown_precision_raises(self):
        with pytest.raises(ValueError, match="hassasiyet"):
            ParticleStore(4, "quantum")

    def test_soa_arrays_are_separate_and_contiguous(self):
        s = ParticleStore(100)
        assert s.x.flags["C_CONTIGUOUS"]
        assert s.x.base is None or s.x.base is not s.y.base


class TestAccess:
    def test_unknown_field_attribute_raises(self):
        with pytest.raises(AttributeError, match="alani degil"):
            _ = ParticleStore(2).qqq

    def test_field_rebind_is_blocked(self):
        s = ParticleStore(2)
        with pytest.raises(AttributeError, match="yeniden baglanamaz"):
            s.x = np.zeros(2)

    def test_as_dict_is_view_not_copy(self):
        s = ParticleStore(3)
        s.as_dict()["rho"][0] = 42.0
        assert s.rho[0] == 42.0

    def test_copy_is_independent(self):
        a = make_valid_store(5)
        b = a.copy()
        assert a.equal_bitwise(b)
        b.rho[0] += 1.0
        assert not a.equal_bitwise(b)

    def test_equal_bitwise_detects_nan_payloads(self):
        a = make_valid_store(4)
        b = a.copy()
        a.u[1] = np.nan
        b.u[1] = np.nan
        assert a.equal_bitwise(b)  # ayni NaN bit deseni esittir

    def test_equal_bitwise_precision_mismatch(self):
        assert not ParticleStore(2, "science").equal_bitwise(ParticleStore(2, "performance"))


@needs_warp
class TestWarpBridgeCpu:
    """Kopru dogrulugu — CPU cihazinda (GPU'suz ortamda da kosar)."""

    def test_roundtrip_bitwise_cpu(self):
        store = make_valid_store(64)
        store.u[3] = np.nan  # NaN bit deseni bile korunmali
        back = roundtrip_via_warp(store, "cpu")
        assert store.equal_bitwise(back)

    def test_roundtrip_preserves_dtypes_cpu(self):
        store = ParticleStore(16, "performance")
        back = roundtrip_via_warp(store, "cpu")
        for name in store.field_names:
            assert back.dtype_of(name) == store.dtype_of(name)


@needs_warp
@pytest.mark.gpu
class TestWarpBridgeGpu:
    """G0 kaniti: CPU -> GPU -> CPU bit-esit (TRUBA GPU dugumunde kosar)."""

    @pytest.fixture(autouse=True)
    def _require_cuda(self):
        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA cihazi yok")

    def test_roundtrip_bitwise_gpu_science(self):
        store = make_valid_store(4096, "science")
        back = roundtrip_via_warp(store, "cuda:0")
        assert store.equal_bitwise(back)

    def test_roundtrip_bitwise_gpu_performance(self):
        store = make_valid_store(4096, "performance")
        back = roundtrip_via_warp(store, "cuda:0")
        assert store.equal_bitwise(back)

    def test_roundtrip_bitwise_gpu_extreme_values(self):
        store = make_valid_store(256, "science")
        store.x[0] = np.finfo(np.float64).max
        store.x[1] = -np.finfo(np.float64).tiny
        store.u[0] = np.inf
        store.u[1] = np.nan
        back = roundtrip_via_warp(store, "cuda:0")
        assert store.equal_bitwise(back)
