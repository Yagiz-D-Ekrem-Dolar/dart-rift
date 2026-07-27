"""P0-FR-07: uc katmanli HDF5 yaz-oku esitligi + checksum."""

import numpy as np
import pytest
from conftest import make_valid_store

from dartrift.io_hdf5 import (
    LAYERS,
    Hdf5Writer,
    content_sha256,
    file_sha256,
    list_snapshots,
    read_events,
    read_scalar_budget,
    read_snapshot,
)


def _budget_row(step: int) -> dict:
    return {
        "step": step,
        "time": 0.1 * step,
        "mass_total": 1000.0,
        "px": 0.0,
        "py": 1.0e-9,
        "pz": -1.0e-9,
        "e_kin": 5.0e3,
        "e_int": 2.0e3,
    }


def _write_reference(path, compression="gzip", n=32) -> None:
    store = make_valid_store(n)
    with Hdf5Writer(path, compression=compression) as w:
        for s in range(5):
            w.append_scalar_budget(_budget_row(s))
        w.write_snapshot(0, store, step=0, time=0.0)
        w.write_snapshot(1, store, step=4, time=0.4)
        w.append_event(0, 0.0, "run_start", {"note": "faz0"})
        w.append_event(4, 0.4, "run_end", {"ok": True})


def test_three_layers_exist(tmp_path):
    p = tmp_path / "out.h5"
    _write_reference(p)
    import h5py

    with h5py.File(p, "r") as f:
        for layer in LAYERS:
            assert layer in f, f"katman eksik: {layer}"


def test_scalar_budget_roundtrip_exact(tmp_path):
    p = tmp_path / "out.h5"
    _write_reference(p)
    budget = read_scalar_budget(p)
    assert np.array_equal(budget["step"], np.arange(5))
    assert np.array_equal(budget["time"], 0.1 * np.arange(5))
    assert np.all(budget["mass_total"] == 1000.0)
    assert budget["py"][0] == 1.0e-9  # bit-tam float64


def test_snapshot_roundtrip_bitwise(tmp_path):
    p = tmp_path / "out.h5"
    store = make_valid_store(64)
    store.u[7] = np.nan  # NaN dahi korunmali
    with Hdf5Writer(p) as w:
        w.write_snapshot(0, store, step=12, time=1.2)
    back, attrs = read_snapshot(p, 0)
    assert store.equal_bitwise(back)
    assert attrs == {"step": 12, "time": 1.2, "n": 64, "precision": "science"}


def test_snapshot_listing(tmp_path):
    p = tmp_path / "out.h5"
    _write_reference(p)
    assert list_snapshots(p) == ["snap_000000", "snap_000001"]


def test_events_roundtrip(tmp_path):
    p = tmp_path / "out.h5"
    _write_reference(p)
    events = read_events(p)
    assert len(events) == 2
    assert events[0]["kind"] == "run_start"
    assert events[0]["payload"] == {"note": "faz0"}
    assert events[1]["payload"] == {"ok": True}
    assert events[1]["step"] == 4


def test_budget_wrong_columns_raise(tmp_path):
    p = tmp_path / "out.h5"
    with Hdf5Writer(p) as w:
        row = _budget_row(0)
        row.pop("e_kin")
        with pytest.raises(KeyError, match="eksik"):
            w.append_scalar_budget(row)
        row2 = _budget_row(0)
        row2["surpriz"] = 1.0
        with pytest.raises(KeyError, match="fazla"):
            w.append_scalar_budget(row2)


def test_writer_requires_context(tmp_path):
    w = Hdf5Writer(tmp_path / "out.h5")
    with pytest.raises(RuntimeError, match="with"):
        w.append_event(0, 0.0, "x")


@pytest.mark.parametrize("compression", ["gzip", "lzf", "none"])
def test_compression_modes_roundtrip(tmp_path, compression):
    p = tmp_path / f"out_{compression}.h5"
    _write_reference(p, compression=compression)
    back, _ = read_snapshot(p, 0)
    assert back.equal_bitwise(make_valid_store(32))


def test_bad_compression_raises(tmp_path):
    with pytest.raises(ValueError, match="sikistirma"):
        Hdf5Writer(tmp_path / "x.h5", compression="zip")


class TestChecksum:
    def test_content_hash_deterministic_across_writes(self, tmp_path):
        # DR-RIFT-P0 §8: "yazilip okununca ozdes; checksum eslesir"
        p1, p2 = tmp_path / "a.h5", tmp_path / "b.h5"
        _write_reference(p1)
        _write_reference(p2)
        assert content_sha256(p1) == content_sha256(p2)

    def test_content_hash_detects_data_change(self, tmp_path):
        p1, p2 = tmp_path / "a.h5", tmp_path / "b.h5"
        _write_reference(p1)
        store = make_valid_store(32)
        store.rho[0] += 1.0e-12  # tek ULP bile farki yakalanmali
        with Hdf5Writer(p2) as w:
            for s in range(5):
                w.append_scalar_budget(_budget_row(s))
            w.write_snapshot(0, store, step=0, time=0.0)
            w.write_snapshot(1, store, step=4, time=0.4)
            w.append_event(0, 0.0, "run_start", {"note": "faz0"})
            w.append_event(4, 0.4, "run_end", {"ok": True})
        assert content_sha256(p1) != content_sha256(p2)

    def test_file_sha256_stable_for_same_file(self, tmp_path):
        p = tmp_path / "a.h5"
        _write_reference(p)
        assert file_sha256(p) == file_sha256(p)
        assert len(file_sha256(p)) == 64
