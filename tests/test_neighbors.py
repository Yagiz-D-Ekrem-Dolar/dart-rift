"""P1-FR-01: hash-grid komsu listesi brute-force ile birebir + simetrik."""

import numpy as np
import pytest

from dartrift.particles import warp_available

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")


def _gather(kernel_name: str, x: np.ndarray, support: float, device: str):
    import warp as wp

    from dartrift.warp_core import neighbors as NB
    from dartrift.warp_core.hash_grid import GridManager

    n = x.shape[0]
    max_nb = 128
    x64 = wp.array(x, dtype=wp.vec3d, device=device)
    counts = wp.zeros(n, dtype=wp.int32, device=device)
    lists = wp.zeros((n, max_nb), dtype=wp.int32, device=device)
    if kernel_name == "grid":
        gm = GridManager(n, device)
        radius32 = gm.build(x64, support)
        wp.launch(
            NB.gather_neighbors_grid, dim=n,
            inputs=[gm.id, gm.x32, x64, wp.float64(support), wp.float32(radius32),
                    max_nb],
            outputs=[counts, lists], device=device,
        )
    else:
        wp.launch(
            NB.gather_neighbors_brute, dim=n,
            inputs=[x64, n, wp.float64(support), max_nb],
            outputs=[counts, lists], device=device,
        )
    c = counts.numpy()
    ls = lists.numpy()
    assert int(c.max()) <= max_nb, "max_nb tasti; test kurulumu hatali"
    return [set(ls[i, : c[i]].tolist()) for i in range(n)]


@needs_warp
class TestNeighborParity:
    @pytest.fixture(scope="class")
    def cloud(self):
        rng = np.random.default_rng(42)
        return rng.uniform(-0.5, 0.5, (300, 3))

    def test_grid_matches_brute_force(self, cloud):
        # kucuk-N birebir eslesme (P1 §6.1)
        support = 0.18
        grid_sets = _gather("grid", cloud, support, "cpu")
        brute_sets = _gather("brute", cloud, support, "cpu")
        for i, (g, b) in enumerate(zip(grid_sets, brute_sets, strict=True)):
            assert g == b, f"parcacik {i}: grid={sorted(g)} brute={sorted(b)}"

    def test_grid_matches_numpy_reference(self, cloud):
        from dartrift.warp_core.hash_grid import brute_force_neighbors

        support = 0.18
        grid_sets = _gather("grid", cloud, support, "cpu")
        ref_sets = brute_force_neighbors(cloud, support)
        assert grid_sets == ref_sets

    def test_neighbor_list_is_symmetric(self, cloud):
        support = 0.18
        sets = _gather("grid", cloud, support, "cpu")
        for i, s in enumerate(sets):
            for j in s:
                assert i in sets[j], f"simetri ihlali: {i} -> {j} ama {j} -/-> {i}"

    def test_self_is_included(self, cloud):
        sets = _gather("grid", cloud, 0.18, "cpu")
        assert all(i in s for i, s in enumerate(sets))

    @pytest.mark.gpu
    def test_gpu_grid_matches_brute_force(self, cloud):
        from dartrift.particles import warp_devices

        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")
        support = 0.18
        grid_sets = _gather("grid", cloud, support, "cuda:0")
        brute_sets = _gather("brute", cloud, support, "cuda:0")
        assert grid_sets == brute_sets
