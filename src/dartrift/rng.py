"""Deterministik RNG ve tohum mimarisi (P0-FR-04).

Tum rastgelelik, kosu basina TEK bir kok tohumdan (config.random_seed) turetilir.
Adlandirilmis akislar (particles / material / realization) kok tohumdan bagimsiz
spawn edilir. Parca (shard) bolunmesi sonucu DEGISTIRMEZ: her eleman kendi
`spawn_key=(akis, indeks)` tohumunu kullanir; kac parcaya bolundugunden bagimsiz
ayni diziyi uretir.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

__all__ = [
    "STREAMS",
    "root_sequence",
    "stream_generator",
    "element_seed",
    "element_generator",
    "sample_uniform",
    "sample_uniform_sharded",
]

# Adlandirilmis akislarin sabit kimlikleri. SIRA VE DEGERLER KILITLIDIR:
# degistirmek tum altin hash'leri kirar (bkz. ADR-0004).
STREAMS: dict[str, int] = {
    "particles": 0,
    "material": 1,
    "realization": 2,
    # SONA EKLEME (2026-08-01, hasar modeli). Mevcut kimlikler 0/1/2
    # DEGISMEDIGI icin hicbir altin hash etkilenmez; ADR-0004'un yasakladigi
    # sey var olan bir akisin kimligini/sirasini oynatmaktir, listeye yeni bir
    # ad eklemek degil. Yeni akislar DAIMA sona eklenir.
    "damage_flaws": 3,
}


def _stream_id(stream: str) -> int:
    try:
        return STREAMS[stream]
    except KeyError:
        raise KeyError(f"bilinmeyen RNG akisi: {stream!r} (gecerli: {sorted(STREAMS)})") from None


def root_sequence(root_seed: int) -> np.random.SeedSequence:
    """Kosunun kok tohum dizisi."""
    return np.random.SeedSequence(root_seed)


def stream_generator(root_seed: int, stream: str) -> np.random.Generator:
    """Adlandirilmis akis icin toplu-cekim ureteci.

    NOT: Toplu cekimler cekim SIRASINA duyarlidir; shard-degismez ornekleme icin
    `sample_uniform` / `element_generator` kullanin (ADR-0004).
    """
    ss = np.random.SeedSequence(root_seed, spawn_key=(_stream_id(stream),))
    return np.random.default_rng(ss)


def element_seed(root_seed: int, stream: str, index: int) -> np.random.SeedSequence:
    """Tek bir eleman (parcacik/realizasyon) icin deterministik tohum."""
    if index < 0:
        raise ValueError(f"eleman indeksi negatif olamaz: {index}")
    return np.random.SeedSequence(root_seed, spawn_key=(_stream_id(stream), index))


def element_generator(root_seed: int, stream: str, index: int) -> np.random.Generator:
    """Tek elemanlik bagimsiz uretec — shard sayisindan bagimsiz ayni sonuc."""
    return np.random.default_rng(element_seed(root_seed, stream, index))


def sample_uniform(
    root_seed: int,
    stream: str,
    n: int,
    low: float = 0.0,
    high: float = 1.0,
) -> np.ndarray:
    """Eleman-tohumlu U[low, high) ornekleri (float64, shard-degismez).

    Her eleman kendi generatorunden TEK deger ceker; boylece sonuc yalnizca
    (root_seed, stream, index)'e baglidir.
    """
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        out[i] = element_generator(root_seed, stream, i).random()
    return low + (high - low) * out


def sample_uniform_sharded(
    root_seed: int,
    stream: str,
    n: int,
    n_shards: int,
    low: float = 0.0,
    high: float = 1.0,
    shard_worker: Callable[[int, int], np.ndarray] | None = None,
) -> np.ndarray:
    """Ayni ornekleri n_shards parcaya bolerek uret; sonuc `sample_uniform` ile ozdes.

    `shard_worker(start, stop)` verilirse parca hesabi ona devredilir (paralel
    yurutme simulasyonu); verilmezse ardisik hesaplanir.
    """
    if n_shards < 1:
        raise ValueError(f"n_shards >= 1 olmali: {n_shards}")
    bounds = np.linspace(0, n, n_shards + 1, dtype=np.int64)
    parts: list[np.ndarray] = []
    for k in range(n_shards):
        start, stop = int(bounds[k]), int(bounds[k + 1])
        if shard_worker is not None:
            part = shard_worker(start, stop)
        else:
            part = np.array(
                [element_generator(root_seed, stream, i).random() for i in range(start, stop)],
                dtype=np.float64,
            )
        parts.append(part)
    out = np.concatenate(parts) if parts else np.empty(0, dtype=np.float64)
    return low + (high - low) * out
