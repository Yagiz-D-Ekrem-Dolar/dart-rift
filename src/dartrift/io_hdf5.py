"""3 katmanli HDF5 cikti/checkpoint iskeleti (P0-FR-07).

Katmanlar ayri gruplarda saklanir:
- /scalar_budget   : adim-bazli skaler korunum butceleri (genisleyebilir diziler)
- /sparse_snapshot : seyrek tam-alan anlik goruntuleri (snap_XXXXXX alt gruplari)
- /event_catalog   : olay kayitlari (adim, zaman, tur, JSON yuk)

Checksum politikasi (ADR-0003): kanonik saglama `content_sha256` ICERIK uzerinden
hesaplanir (grup/veri kumesi adlari + dtype + shape + veri baytlari + attr'lar,
sirali gezinme). Ham dosya baytlari HDF5 ust-veri zaman damgalarina bagimli
olabileceginden butun veri kumeleri `track_times=False` ile yazilir.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

from .particles import ParticleStore

__all__ = [
    "LAYERS",
    "Hdf5Writer",
    "read_scalar_budget",
    "read_snapshot",
    "list_snapshots",
    "read_events",
    "content_sha256",
    "file_sha256",
]

LAYERS = ("scalar_budget", "sparse_snapshot", "event_catalog")

SCALAR_BUDGET_COLUMNS = (
    "step",
    "time",
    "mass_total",
    "px",
    "py",
    "pz",
    "e_kin",
    "e_int",
)

_EVENT_DTYPE = np.dtype(
    [
        ("step", np.int64),
        ("time", np.float64),
        ("kind", h5py.string_dtype(encoding="utf-8")),
        ("payload", h5py.string_dtype(encoding="utf-8")),
    ]
)


def _compression_kwargs(compression: str) -> dict:
    if compression == "gzip":
        return {"compression": "gzip", "compression_opts": 4}
    if compression == "lzf":
        return {"compression": "lzf"}
    if compression == "none":
        return {}
    raise ValueError(f"bilinmeyen sikistirma: {compression!r} (gecerli: gzip, lzf, none)")


class Hdf5Writer:
    """Uc katmanli HDF5 yazici. Baglam yoneticisi olarak kullanilir."""

    def __init__(self, path: str | Path, compression: str = "gzip"):
        self.path = Path(path)
        self._ckw = _compression_kwargs(compression)
        self._file: h5py.File | None = None

    def __enter__(self) -> Hdf5Writer:
        self._file = h5py.File(self.path, "w", track_order=True)
        for layer in LAYERS:
            self._file.create_group(layer, track_order=True)
        g = self._file["scalar_budget"]
        for col in SCALAR_BUDGET_COLUMNS:
            dt = np.int64 if col == "step" else np.float64
            g.create_dataset(
                col,
                shape=(0,),
                maxshape=(None,),
                dtype=dt,
                chunks=(1024,),
                track_times=False,
                **self._ckw,
            )
        self._file["event_catalog"].create_dataset(
            "events",
            shape=(0,),
            maxshape=(None,),
            dtype=_EVENT_DTYPE,
            chunks=(256,),
            track_times=False,
        )
        return self

    def __exit__(self, *exc) -> None:
        assert self._file is not None
        self._file.close()
        self._file = None

    def _require_open(self) -> h5py.File:
        if self._file is None:
            raise RuntimeError("Hdf5Writer kapali; 'with' blogu icinde kullanin")
        return self._file

    # -- katman 1: skaler butce -------------------------------------------
    def append_scalar_budget(self, row: dict) -> None:
        """Bir adimin korunum butcesini ekle. Eksik/fazla kolon acik hata."""
        f = self._require_open()
        missing = set(SCALAR_BUDGET_COLUMNS) - set(row)
        extra = set(row) - set(SCALAR_BUDGET_COLUMNS)
        if missing or extra:
            raise KeyError(
                f"scalar_budget kolonlari uyusmuyor: eksik={sorted(missing)} fazla={sorted(extra)}"
            )
        g = f["scalar_budget"]
        for col in SCALAR_BUDGET_COLUMNS:
            ds = g[col]
            ds.resize((ds.shape[0] + 1,))
            ds[-1] = row[col]

    # -- katman 2: seyrek snapshot ----------------------------------------
    def write_snapshot(self, index: int, store: ParticleStore, step: int, time: float) -> None:
        """Tam parcacik durumunu snap_XXXXXX alt grubuna yaz."""
        f = self._require_open()
        name = f"snap_{index:06d}"
        grp = f["sparse_snapshot"].create_group(name, track_order=True)
        grp.attrs["step"] = np.int64(step)
        grp.attrs["time"] = np.float64(time)
        grp.attrs["n"] = np.int64(store.n)
        grp.attrs["precision"] = store.precision
        for fname, arr in store.as_dict().items():
            ckw = self._ckw if arr.size else {}
            grp.create_dataset(fname, data=arr, track_times=False, **ckw)

    # -- katman 3: olay katalogu ------------------------------------------
    def append_event(self, step: int, time: float, kind: str, payload: dict | None = None) -> None:
        """Olay kaydi ekle; yuk JSON olarak saklanir."""
        f = self._require_open()
        ds = f["event_catalog"]["events"]
        ds.resize((ds.shape[0] + 1,))
        ds[-1] = (
            np.int64(step),
            np.float64(time),
            kind,
            json.dumps(payload or {}, sort_keys=True),
        )


# ---------------------------------------------------------------------------
# Okuyucular
# ---------------------------------------------------------------------------


def read_scalar_budget(path: str | Path) -> dict[str, np.ndarray]:
    with h5py.File(path, "r") as f:
        g = f["scalar_budget"]
        return {col: g[col][...] for col in SCALAR_BUDGET_COLUMNS}


def list_snapshots(path: str | Path) -> list[str]:
    with h5py.File(path, "r") as f:
        return sorted(f["sparse_snapshot"].keys())


def read_snapshot(path: str | Path, index: int) -> tuple[ParticleStore, dict]:
    """Snapshot'i ParticleStore olarak geri yukle; (store, attrs) dondur."""
    name = f"snap_{index:06d}"
    with h5py.File(path, "r") as f:
        grp = f["sparse_snapshot"][name]
        attrs = {
            "step": int(grp.attrs["step"]),
            "time": float(grp.attrs["time"]),
            "n": int(grp.attrs["n"]),
            "precision": str(grp.attrs["precision"]),
        }
        store = ParticleStore(attrs["n"], attrs["precision"])
        for fname in store.field_names:
            data = grp[fname][...]
            if data.dtype != store.dtype_of(fname):
                raise TypeError(f"snapshot dtype uyusmazligi: {fname} {data.dtype}")
            store.as_dict()[fname][...] = data
    return store, attrs


def read_events(path: str | Path) -> list[dict]:
    with h5py.File(path, "r") as f:
        raw = f["event_catalog"]["events"][...]
    out = []
    for rec in raw:
        kind = rec["kind"]
        payload = rec["payload"]
        out.append(
            {
                "step": int(rec["step"]),
                "time": float(rec["time"]),
                "kind": kind.decode("utf-8") if isinstance(kind, bytes) else str(kind),
                "payload": json.loads(
                    payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)
                ),
            }
        )
    return out


# ---------------------------------------------------------------------------
# Saglama (checksum)
# ---------------------------------------------------------------------------


def _hash_attrs(h: hashlib._Hash, obj) -> None:
    for key in sorted(obj.attrs):
        h.update(key.encode("utf-8"))
        val = obj.attrs[key]
        if isinstance(val, bytes):
            h.update(b"bytes" + val)
        elif isinstance(val, str):
            h.update(b"str" + val.encode("utf-8"))
        else:
            arr = np.asarray(val)
            h.update(str(arr.dtype).encode("utf-8"))
            h.update(np.ascontiguousarray(arr).tobytes())


def _hash_array(h: hashlib._Hash, data: np.ndarray) -> None:
    """Diziyi ICERIGE gore hashle.

    Nesne (vlen-string) ve bilesik dtype'lar alan alan gezilir: `tobytes()`
    nesne dizilerinde bellek ADRESLERINI serilestirir ve yazimdan yazima
    degisir — kanonik saglamada asla kullanilmaz.
    """
    dt = data.dtype
    if dt.kind == "O":
        for item in np.asarray(data, dtype=object).ravel():
            b = item if isinstance(item, bytes) else str(item).encode("utf-8")
            h.update(b)
            h.update(b"\x00")
    elif dt.names:  # bilesik (compound) dtype: alan alan
        for fname in dt.names:
            h.update(fname.encode("utf-8"))
            _hash_array(h, data[fname])
    else:
        h.update(np.ascontiguousarray(data).tobytes())


def content_sha256(path: str | Path) -> str:
    """Kanonik icerik saglamasi: yapi + dtype + shape + veri + attr, sirali gezinme."""
    h = hashlib.sha256()

    def visit(name: str, obj) -> None:
        h.update(name.encode("utf-8"))
        if isinstance(obj, h5py.Dataset):
            h.update(str(obj.dtype).encode("utf-8"))
            h.update(str(obj.shape).encode("utf-8"))
            _hash_array(h, obj[...])
        _hash_attrs(h, obj)

    with h5py.File(path, "r") as f:
        _hash_attrs(h, f)
        f.visititems(visit)
    return h.hexdigest()


def file_sha256(path: str | Path) -> str:
    """Ham dosya baytlarinin SHA-256'si (arsiv butunlugu icin; kanonik degil)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
