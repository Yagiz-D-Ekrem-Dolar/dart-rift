"""Config'in gercekten TUKETILDIGINI kanitlayan testler.

Bu dosyanin varlik nedeni bir kusurdur: ilk uygulamada config semasi
`numerics.precision`, `io.output_layers`, `io.hdf5_compression` ve `domain`
alanlarini dogruluyordu, ama motorun hicbir pargasi bu degerleri OKUMUYORDU.
Sema bir sey vaat ediyor, motor baskasini yapiyordu — ve hicbir test bunu
yakalamiyordu (bir ozelligin ADI, uygulandigi anlamina gelmez).

Buradaki her test, bir config alanini degistirip gozlemlenebilir davranisin
gercekten degistigini dogrular.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from conftest import make_valid_store

from dartrift.config import RunConfig, load_config
from dartrift.invariants import InvariantViolation, check_invariants
from dartrift.io_hdf5 import (
    Hdf5Writer,
    LayerDisabledError,
    read_output_layers,
)
from dartrift.particles import ParticleStore

SMOKE = Path(__file__).resolve().parents[1] / "configs" / "p0_smoke.yaml"


def _cfg(**over) -> RunConfig:
    base = {
        "schema_version": 1,
        "run_id": "W_0001",
        "random_seed": 7,
        "numerics": {"precision": "deterministic_fp64"},
    }
    base.update(over)
    return RunConfig.model_validate(base)


class TestPrecisionWiring:
    """numerics.precision -> ParticleStore bellek yerlesimi."""

    def test_deterministic_fp64_gives_science_store(self):
        cfg = _cfg()
        assert cfg.store_precision == "science"
        store = ParticleStore.from_config(cfg, 8)
        assert store.precision == "science"
        assert store.dtype_of("x") == np.float64

    def test_performance_mixed_gives_fp32_kinematics(self):
        cfg = _cfg(numerics={"precision": "performance_mixed"})
        assert cfg.store_precision == "performance"
        store = ParticleStore.from_config(cfg, 8)
        assert store.dtype_of("x") == np.float32
        assert store.dtype_of("rho") == np.float64  # termodinamik FP64 kalir

    def test_precision_change_actually_changes_layout(self):
        """Asil kusur testi: config degisince yerlesim GERCEKTEN degismeli."""
        a = ParticleStore.from_config(_cfg(), 4)
        b = ParticleStore.from_config(_cfg(numerics={"precision": "performance_mixed"}), 4)
        assert a.dtype_of("vx") != b.dtype_of("vx")

    def test_every_schema_precision_has_a_store_mode(self):
        # Semaya yeni bir hassasiyet eklenirse kopru de guncellenmeli.
        from dartrift.config import _PRECISION_TO_STORE_MODE
        from dartrift.particles import PRECISION_MODES

        schema_values = {"deterministic_fp64", "performance_mixed"}
        assert set(_PRECISION_TO_STORE_MODE) == schema_values
        assert set(_PRECISION_TO_STORE_MODE.values()) <= set(PRECISION_MODES)


class TestOutputLayerWiring:
    """io.output_layers -> HDF5 yaziciysa gercekten katman acar/kapatir."""

    def test_all_layers_by_default(self, tmp_path):
        cfg = load_config(SMOKE)
        p = tmp_path / "full.h5"
        with Hdf5Writer.from_config(cfg, p) as w:
            w.write_snapshot(0, make_valid_store(4), 0, 0.0)
        assert read_output_layers(p) == (
            "scalar_budget",
            "sparse_snapshot",
            "event_catalog",
        )

    def test_disabled_layer_is_not_created(self, tmp_path):
        cfg = _cfg(io={"output_layers": ["scalar_budget"]})
        p = tmp_path / "only_budget.h5"
        with Hdf5Writer.from_config(cfg, p):
            pass
        import h5py

        with h5py.File(p, "r") as f:
            assert "scalar_budget" in f
            assert "sparse_snapshot" not in f
            assert "event_catalog" not in f
        assert read_output_layers(p) == ("scalar_budget",)

    def test_writing_to_disabled_layer_raises(self, tmp_path):
        """Sessiz yok sayma YASAK: kapali katmana yazmak acik hata vermeli."""
        cfg = _cfg(io={"output_layers": ["scalar_budget"]})
        with Hdf5Writer.from_config(cfg, tmp_path / "x.h5") as w:
            with pytest.raises(LayerDisabledError, match="sparse_snapshot"):
                w.write_snapshot(0, make_valid_store(2), 0, 0.0)
            with pytest.raises(LayerDisabledError, match="event_catalog"):
                w.append_event(0, 0.0, "olay")

    def test_disabled_budget_layer_raises(self, tmp_path):
        cfg = _cfg(io={"output_layers": ["event_catalog"]})
        with Hdf5Writer.from_config(cfg, tmp_path / "y.h5") as w:
            with pytest.raises(LayerDisabledError, match="scalar_budget"):
                w.append_scalar_budget(
                    {
                        "step": 0, "time": 0.0, "mass_total": 1.0,
                        "px": 0.0, "py": 0.0, "pz": 0.0, "e_kin": 0.0, "e_int": 0.0,
                    }
                )
            w.append_event(0, 0.0, "olay")  # acik katman calismaya devam eder

    def test_unknown_layer_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="bilinmeyen cikti katmani"):
            Hdf5Writer(tmp_path / "z.h5", layers=("hayali_katman",))

    def test_empty_layers_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="en az bir"):
            Hdf5Writer(tmp_path / "z.h5", layers=())


class TestCompressionWiring:
    """io.hdf5_compression -> yaziciya gercekten uygulanir."""

    @pytest.mark.parametrize("mode", ["gzip", "lzf", "none"])
    def test_compression_from_config_applied(self, tmp_path, mode):
        cfg = _cfg(io={"output_layers": ["sparse_snapshot"], "hdf5_compression": mode})
        p = tmp_path / f"{mode}.h5"
        with Hdf5Writer.from_config(cfg, p) as w:
            w.write_snapshot(0, make_valid_store(256), 0, 0.0)
        import h5py

        with h5py.File(p, "r") as f:
            comp = f["sparse_snapshot/snap_000000/x"].compression
        assert comp == (None if mode == "none" else mode)


class TestDomainWiring:
    """domain -> invariant denetleyicisinin sinir kontrolu."""

    def test_domain_bounds_exposed(self):
        cfg = load_config(SMOKE)
        bounds = cfg.domain_bounds
        assert bounds is not None
        assert bounds[0] == (-1000.0, -1000.0, -1000.0)
        assert bounds[1] == (1000.0, 1000.0, 1000.0)

    def test_no_domain_gives_none(self):
        assert _cfg().domain_bounds is None

    def test_config_domain_catches_escapee(self):
        cfg = _cfg(domain={"min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]})
        store = make_valid_store(8)
        store.x[3] = 500.0
        with pytest.raises(InvariantViolation, match="alan disina"):
            check_invariants(store, level="science", domain=cfg.domain_bounds)

    def test_wider_config_domain_accepts_same_state(self):
        cfg = _cfg(domain={"min": [-1000.0] * 3, "max": [1000.0] * 3})
        store = make_valid_store(8)
        store.x[3] = 500.0
        assert check_invariants(store, level="science", domain=cfg.domain_bounds).ok
