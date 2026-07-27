"""ADR-0006: FAZ 1 config alanlari (kernel/cfl/alpha_av/beta_av) TUKETILIYOR."""

import numpy as np
import pytest

from dartrift.config import ConfigError, RunConfig, load_config
from dartrift.cpu_reference import sph_ref as R
from dartrift.validation.conservation import build_cloud_ic


def _cfg(**numerics) -> RunConfig:
    base = {"precision": "deterministic_fp64"}
    base.update(numerics)
    return RunConfig.model_validate(
        {"schema_version": 1, "run_id": "P1_wire", "random_seed": 3, "numerics": base}
    )


class TestSchemaP1Fields:
    def test_kernel_only_wendland_c2(self):
        assert _cfg(kernel="wendland_c2").numerics.kernel == "wendland_c2"

    def test_invalid_kernel_rejected(self, tmp_path):
        p = tmp_path / "bad_kernel.yaml"
        p.write_text(
            "schema_version: 1\nrun_id: X\nrandom_seed: 1\n"
            "numerics: {precision: deterministic_fp64, kernel: cubic_spline}\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="kernel"):
            load_config(p)

    def test_av_defaults_are_spec_values(self):
        n = _cfg().numerics
        assert n.alpha_av == 1.0 and n.beta_av == 2.0  # P1 §2.5 tipik degerler

    def test_av_out_of_range_rejected(self, tmp_path):
        p = tmp_path / "bad_av.yaml"
        p.write_text(
            "schema_version: 1\nrun_id: X\nrandom_seed: 1\n"
            "numerics: {precision: deterministic_fp64, alpha_av: -1.0}\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="alpha_av"):
            load_config(p)

    def test_scenario_fields(self):
        cfg = RunConfig.model_validate(
            {"schema_version": 1, "run_id": "P1_sod_R2", "random_seed": 1,
             "numerics": {"precision": "deterministic_fp64", "kernel": "wendland_c2",
                          "cfl": 0.3, "alpha_av": 1.0, "beta_av": 2.0},
             "test": "sod_shock_tube", "resolution": [64, 128, 256]}
        )
        assert cfg.test == "sod_shock_tube"
        assert cfg.resolution == [64, 128, 256]

    def test_unknown_scenario_rejected(self, tmp_path):
        p = tmp_path / "bad_test.yaml"
        p.write_text(
            "schema_version: 1\nrun_id: X\nrandom_seed: 1\n"
            "numerics: {precision: deterministic_fp64}\ntest: warp_hizi_testi\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="test"):
            load_config(p)


class TestParamsConsumption:
    """Alanlar RefParams uzerinden cozucuye GERCEKTEN akiyor."""

    def test_from_config_reads_values(self):
        cfg = _cfg(kernel="wendland_c2", cfl=0.17, alpha_av=0.5, beta_av=1.1)
        p = R.RefParams.from_config(cfg)
        assert (p.cfl, p.alpha_av, p.beta_av) == (0.17, 0.5, 1.1)

    def test_alpha_av_changes_shock_heating(self):
        # davranis testi: alpha_av'nin YALNIZCA AV katkisi izole edilir
        # (toplam du/dt basinc isini de icerir; fark alinarak ayristirilir)
        ic = build_cloud_ic(150)
        n = len(ic["m"])
        v = ic["x"] * -0.5  # ice cokme: yaklasan ciftler -> AV aktif

        def total_heating(alpha: float) -> float:
            st = R.RefState(x=ic["x"].copy(), v=v.copy(), m=ic["m"], u=ic["u"].copy(),
                            h=ic["h"], active=np.ones(n, bool))
            R.evaluate(st, R.RefParams.from_config(_cfg(alpha_av=alpha, beta_av=0.0)))
            return float(np.sum(ic["m"] * st.dudt))

        base = total_heating(0.0)
        av_small = total_heating(0.2) - base
        av_big = total_heating(2.0) - base
        assert av_small > 0.0, "AV isinmasi pozitif olmali"
        # dogrusal olcek: 10x katsayi ~10x AV isinmasi vermeli
        assert av_big == pytest.approx(10.0 * av_small, rel=1e-9), (
            f"alpha_av dogrusal olceklemiyor: {av_small} vs {av_big}"
        )

    def test_cfl_changes_timestep(self):
        ic = build_cloud_ic(100)
        st = R.RefState(x=ic["x"], v=ic["v"], m=ic["m"], u=ic["u"], h=ic["h"],
                        active=np.ones(len(ic["m"]), bool))
        R.evaluate(st, R.RefParams())
        dt1, _ = R.compute_timestep(st, R.RefParams.from_config(_cfg(cfl=0.1)))
        dt2, _ = R.compute_timestep(st, R.RefParams.from_config(_cfg(cfl=0.3)))
        assert dt2 == pytest.approx(3.0 * dt1, rel=1e-12)

    def test_timestep_stats_structure(self):
        # P1-FR-07: kisit yuzdesi kaydi
        ic = build_cloud_ic(100)
        st = R.RefState(x=ic["x"], v=ic["v"], m=ic["m"], u=ic["u"], h=ic["h"],
                        active=np.ones(len(ic["m"]), bool))
        R.evaluate(st, R.RefParams())
        _, stats = R.compute_timestep(st, R.RefParams())
        assert stats["binding_criterion"] in ("cfl_viscous", "acceleration")
        assert stats["pct_cfl_viscous"] + stats["pct_acceleration"] == pytest.approx(100.0)
