"""P0-FR-04: tek kok tohum; shard bolunmesi sonucu DEGISTIRMEZ."""

import numpy as np
import pytest

from dartrift.rng import (
    STREAMS,
    element_generator,
    element_seed,
    root_sequence,
    sample_uniform,
    sample_uniform_sharded,
    stream_generator,
)

SEED = 104729


class TestStreams:
    def test_stream_ids_are_locked(self):
        """ADR-0004: VAR OLAN akislarin kimlikleri kilitli.

        Kilitlenen sey mevcut esleme; listenin uzunlugu degil. Bir akisin
        kimligini ya da sirasini oynatmak butun altin hash'leri kirar —
        SONA yeni bir ad eklemek hicbirini etkilemez.

        Bu test once `STREAMS == {...}` diye tam esitlik ariyordu ve hasar
        modeli icin eklenen `damage_flaws` akisinda kirildi. Kirilma dogruydu
        (bekci calisti) ama iddia fazla genisti: eklemeyi de yasakliyordu.
        Simdi kilitlenen sey acikca "mevcut girdiler degismesin"dir.
        """
        kilitli = {"particles": 0, "material": 1, "realization": 2}
        for ad, kimlik in kilitli.items():
            assert STREAMS[ad] == kimlik, f"KILITLI AKIS DEGISTI: {ad}"
        # yeni akislar yalnizca SONA, cakismayan kimliklerle eklenebilir
        assert len(set(STREAMS.values())) == len(STREAMS), "kimlik cakismasi"
        assert min(STREAMS.values()) == 0
        assert set(STREAMS.values()) == set(range(len(STREAMS))), "kimlikler bosluksuz olmali"

    def test_new_streams_are_appended_not_inserted(self):
        """Yeni akislarin kimligi, kilitli olanlarin USTUNDE olmali."""
        for ad, kimlik in STREAMS.items():
            if ad not in ("particles", "material", "realization"):
                assert kimlik >= 3, f"{ad} kilitli araliga sokulmus: {kimlik}"

    def test_damage_flaws_stream_independent(self):
        """Hasar kusurlari, blok yerlestirmeyle AYNI diziyi kullanmamali.

        Ikisi de 'material' akisini kullansaydi ayni sayilari cekerler ve
        istatistiksel olarak korele olurlardi."""
        a = stream_generator(SEED, "material").random(64)
        b = stream_generator(SEED, "damage_flaws").random(64)
        assert not np.array_equal(a, b)

    def test_unknown_stream_raises(self):
        with pytest.raises(KeyError, match="bilinmeyen RNG akisi"):
            stream_generator(SEED, "kaos")

    def test_streams_are_independent(self):
        a = stream_generator(SEED, "particles").random(64)
        b = stream_generator(SEED, "material").random(64)
        assert not np.array_equal(a, b)

    def test_same_seed_same_stream_reproducible(self):
        a = stream_generator(SEED, "particles").random(64)
        b = stream_generator(SEED, "particles").random(64)
        assert np.array_equal(a, b)

    def test_different_root_seed_differs(self):
        a = stream_generator(SEED, "particles").random(16)
        b = stream_generator(SEED + 1, "particles").random(16)
        assert not np.array_equal(a, b)

    def test_root_sequence_entropy(self):
        assert root_sequence(SEED).entropy == SEED


class TestElementSeeding:
    def test_element_generator_reproducible(self):
        x1 = element_generator(SEED, "particles", 7).random()
        x2 = element_generator(SEED, "particles", 7).random()
        assert x1 == x2

    def test_elements_differ(self):
        xs = {element_generator(SEED, "particles", i).random() for i in range(32)}
        assert len(xs) == 32

    def test_negative_index_raises(self):
        with pytest.raises(ValueError, match="negatif"):
            element_seed(SEED, "particles", -1)

    def test_element_independent_of_call_order(self):
        forward = [element_generator(SEED, "material", i).random() for i in range(8)]
        backward = [element_generator(SEED, "material", i).random() for i in reversed(range(8))]
        assert forward == backward[::-1]


class TestShardInvariance:
    """DR-RIFT-P0 §8: 'farkli shard sayisi -> ayni sonuc'."""

    def test_reference_unsharded(self):
        ref = sample_uniform(SEED, "particles", 101)
        assert ref.shape == (101,)
        assert np.all((ref >= 0.0) & (ref < 1.0))

    @pytest.mark.parametrize("n_shards", [1, 2, 3, 5, 7, 101])
    def test_sharded_equals_unsharded_bitwise(self, n_shards):
        ref = sample_uniform(SEED, "particles", 101)
        sharded = sample_uniform_sharded(SEED, "particles", 101, n_shards)
        assert np.array_equal(ref, sharded), f"shard={n_shards} sonucu degistirdi"

    def test_shard_invariance_with_bounds(self):
        ref = sample_uniform(SEED, "material", 50, low=2000.0, high=3000.0)
        sharded = sample_uniform_sharded(SEED, "material", 50, 4, low=2000.0, high=3000.0)
        assert np.array_equal(ref, sharded)
        assert np.all((ref >= 2000.0) & (ref < 3000.0))

    def test_custom_shard_worker_matches(self):
        def worker(start: int, stop: int) -> np.ndarray:
            return np.array(
                [element_generator(SEED, "particles", i).random() for i in range(start, stop)]
            )

        ref = sample_uniform(SEED, "particles", 20)
        out = sample_uniform_sharded(SEED, "particles", 20, 3, shard_worker=worker)
        assert np.array_equal(ref, out)

    def test_zero_shards_raises(self):
        with pytest.raises(ValueError, match="n_shards"):
            sample_uniform_sharded(SEED, "particles", 10, 0)

    def test_empty_sample(self):
        assert sample_uniform(SEED, "particles", 0).size == 0
        assert sample_uniform_sharded(SEED, "particles", 0, 3).size == 0
