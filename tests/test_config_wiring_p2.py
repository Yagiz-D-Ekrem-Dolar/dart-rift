"""ADR-0006: FAZ 2 physics config alanlari dogrulanir VE tuketilir."""

import numpy as np
import pytest

from dartrift.config import ConfigError, RunConfig, load_config
from dartrift.cpu_reference.materials import MaterialParams
from dartrift.cpu_reference.solid_ref import SolidState, compute_eos_solid


def _cfg(physics: dict) -> RunConfig:
    return RunConfig.model_validate(
        {"schema_version": 1, "run_id": "P2_wire", "random_seed": 3,
         "numerics": {"precision": "deterministic_fp64"}, "physics": physics}
    )


class TestSchemaP2:
    def test_default_physics_is_phase1_compatible(self):
        cfg = RunConfig.model_validate(
            {"schema_version": 1, "run_id": "X", "random_seed": 1,
             "numerics": {"precision": "deterministic_fp64"}}
        )
        assert cfg.physics.eos == "ideal_gas"
        assert not cfg.physics.strength.enabled
        assert not cfg.physics.porosity.enabled
        assert not cfg.physics.gravity.enabled

    def test_ps_le_pe_rejected(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(
            "schema_version: 1\nrun_id: X\nrandom_seed: 1\n"
            "numerics: {precision: deterministic_fp64}\n"
            "physics: {porosity: {enabled: true, Pe: 1.0e8, Ps: 1.0e6}}\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="Ps"):
            load_config(p)

    def test_ucv_le_uiv_rejected(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(
            "schema_version: 1\nrun_id: X\nrandom_seed: 1\n"
            "numerics: {precision: deterministic_fp64}\n"
            "physics: {tillotson: {u_iv: 2.0e7, u_cv: 1.0e7}}\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="u_cv"):
            load_config(p)

    def test_bad_gravity_mode_rejected(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(
            "schema_version: 1\nrun_id: X\nrandom_seed: 1\n"
            "numerics: {precision: deterministic_fp64}\n"
            "physics: {gravity: {enabled: true, mode: fmm}}\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="mode"):
            load_config(p)


class TestConsumption:
    def test_from_config_reads_all_modules(self):
        cfg = _cfg({
            "eos": "tillotson",
            "strength": {"enabled": True, "Y0": 123.0, "shear_G": 1e10, "jaumann": False},
            "porosity": {"enabled": True, "alpha0": 1.7, "Pe": 2e6, "Ps": 3e8},
            "gravity": {"enabled": True, "mode": "barnes_hut", "theta": 0.7, "eps": 0.1},
        })
        mat = MaterialParams.from_config(cfg)
        assert mat.eos == "tillotson"
        assert mat.strength.Y0 == 123.0 and mat.strength.jaumann is False
        assert mat.porosity.alpha0 == 1.7
        assert mat.gravity.mode == "barnes_hut" and mat.gravity.theta == 0.7

    def test_eos_choice_changes_pressure(self):
        # davranis: ayni durum, farkli EOS -> farkli P (alan gercekten okunuyor)
        n = 8
        st = SolidState(x=np.random.default_rng(0).uniform(-1, 1, (n, 3)),
                        v=np.zeros((n, 3)), m=np.ones(n), u=np.full(n, 1e5),
                        h=0.5, active=np.ones(n, bool))
        st.rho = np.full(n, 2700.0)
        m1 = MaterialParams.from_config(_cfg({"eos": "tillotson"}))
        compute_eos_solid(st, m1)
        p_till = st.P.copy()
        m2 = MaterialParams.from_config(_cfg({"eos": "ideal_gas", "gamma": 1.4}))
        compute_eos_solid(st, m2)
        assert not np.allclose(p_till, st.P)

    def test_porosity_alpha0_drives_initial_distension(self):
        cfg = _cfg({"porosity": {"enabled": True, "alpha0": 2.1, "Pe": 1e6, "Ps": 1e8}})
        mat = MaterialParams.from_config(cfg)
        assert mat.porosity.crush_alpha(np.array([0.0]))[0] == 2.1

    def test_density_method_is_read_from_config(self):
        assert MaterialParams.from_config(_cfg({})).density_method == "summation"
        cfg = _cfg({"density_method": "continuity"})
        assert MaterialParams.from_config(cfg).density_method == "continuity"

    def test_density_method_changes_behavior(self):
        """ADR-0015: alan yalnizca tasinmiyor, ayriklastirmayi GERCEKTEN degistiriyor.

        Summation rho'yu komsu toplamindan yeniden hesaplar; continuity ona
        dokunmaz (integrator ilerletir). Ayni duruma iki yontem uygulaninca
        rho farkli olmali — yoksa alan sessizce tuketilmiyor demektir.
        """
        from dartrift.cpu_reference.solid_ref import evaluate_solid
        from dartrift.cpu_reference.sph_ref import RefParams

        n, rho_seed = 40, 2700.0
        x = np.random.default_rng(7).uniform(-1.0, 1.0, (n, 3))

        def _rho(method):
            st = SolidState(x=x.copy(), v=np.zeros((n, 3)), m=np.ones(n),
                            u=np.full(n, 1e5), h=0.6, active=np.ones(n, bool))
            st.rho = np.full(n, rho_seed)
            mat = MaterialParams.from_config(
                _cfg({"eos": "tillotson", "density_method": method})
            )
            evaluate_solid(st, mat, RefParams())
            return st.rho

        assert np.allclose(_rho("continuity"), rho_seed)
        assert not np.allclose(_rho("summation"), rho_seed)

    def test_unknown_density_method_rejected(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(
            "schema_version: 1\nrun_id: X\nrandom_seed: 1\n"
            "numerics: {precision: deterministic_fp64}\n"
            "physics: {density_method: summasyon}\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="density_method"):
            load_config(p)
