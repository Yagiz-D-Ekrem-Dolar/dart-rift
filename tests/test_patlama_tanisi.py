"""A80 — patlama tanısı: ilk bozulan parçacıklar ve önceki zaman serisi."""
from __future__ import annotations

import inspect
import json

import numpy as np
import pytest

from dartrift.inference import forward
from dartrift.inference.patlama_tanisi import PatlamaGozlemcisi, PatlamaYakalandi


class _SahteCozucu:
    """`state_numpy()` sunan, 7. parçacığı adım 60'ta `nan`'a götüren çözücü."""

    def __init__(self, n=20):
        self.n = n
        self.adim = 0

    def state_numpy(self):
        k = self.adim
        rho = np.full(self.n, 1500.0)
        rho[7] = 1500.0 / (1.0 + 0.1 * k)          # giderek seyrelen parcacik
        v = np.zeros((self.n, 3))
        v[7, 0] = 10.0 * k
        if k >= 60:
            rho[7] = np.nan
        return {"x": np.zeros((self.n, 3)), "v": v, "u": np.ones(self.n),
                "rho": rho, "P": np.zeros(self.n), "cs": np.full(self.n, 300.0),
                "alpha": np.ones(self.n), "S": np.zeros((self.n, 6)),
                "h": np.full(self.n, 0.7)}


def test_ilk_bozulan_parcacik_ve_ONCEKI_seri_yaziliyor(tmp_path):
    sol = _SahteCozucu()
    g = PatlamaGozlemcisi(tmp_path / "t", her=10, halka=4)
    with pytest.raises(PatlamaYakalandi, match="adim 60"):
        for adim in range(1, 200):
            sol.adim = adim
            g(adim, adim * 1e-6, 1e-6, sol)
    tani = json.loads((tmp_path / "t" / "patlama_tani.json").read_text(encoding="utf-8"))
    assert tani["adim"] == 60 and tani["n_sonlu_degil"] == 1
    assert tani["alan_basina"]["rho"] == 1 and tani["alan_basina"]["v"] == 0
    seri = tani["ilk_bozulanlar"]["7"]
    assert [s["adim"] for s in seri] == [20, 30, 40, 50]      # halka = 4
    assert seri[-1]["rho"] < seri[0]["rho"]
    assert len(tani["kuresel_seri"]) == 5
    son = np.load(tmp_path / "t" / "patlama_son_iyi.npz")
    assert int(son["adim"]) == 50
    ilk = np.load(tmp_path / "t" / "patlama_ilk_bozuk.npz")
    assert ilk["kotu"].sum() == 1 and ilk["kotu"][7]


def test_sonlu_kosuda_HICBIR_sey_yazilmiyor(tmp_path):
    sol = _SahteCozucu()
    g = PatlamaGozlemcisi(tmp_path / "t", her=10)
    for adim in range(1, 50):
        sol.adim = adim
        g(adim, 0.0, 1e-6, sol)
    assert not (tmp_path / "t").exists()


def test_ileri_kosu_merdiven_gozlemciyi_HER_adimda_cagiriyor():
    kaynak = inspect.getsource(forward.ileri_kosu_merdiven)
    assert "adim_gozlemcisi=None" in kaynak
    # Belge metninde de geciyor; siralama DONGU icinde aranir.
    i_step = kaynak.index("sol.step(dt)")
    i_cagri = kaynak.index("adim_gozlemcisi(adim, t, dt, sol)", i_step)
    i_sonluluk = kaynak.index("kosu PATLADI adim", i_step)
    assert i_step < i_cagri < i_sonluluk
    assert "if adim_gozlemcisi is not None:" in kaynak[i_step:i_cagri]
