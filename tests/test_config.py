"""P0-FR-02 + P0-DR-01: config semasi; gecersiz vakalar ACIK hatayla reddedilir."""

from pathlib import Path

import pytest

from dartrift.config import (
    ConfigError,
    RunConfig,
    _main,
    config_hash,
    load_config,
)

INVALID_DIR = Path(__file__).resolve().parents[1] / "configs" / "invalid"
SMOKE = Path(__file__).resolve().parents[1] / "configs" / "p0_smoke.yaml"

_invalid_files = sorted(INVALID_DIR.glob("*.yaml"))


def test_invalid_catalog_has_at_least_10_cases():
    # DR-RIFT-P0 §8: "10+ gecersiz config vakasi"
    assert len(_invalid_files) >= 10


def test_smoke_config_loads():
    cfg = load_config(SMOKE)
    assert cfg.run_id == "P0_smoke_0001"
    assert cfg.random_seed == 104729
    assert cfg.schema_version == 1
    assert cfg.numerics.precision == "deterministic_fp64"
    assert cfg.numerics.kernel is None
    assert cfg.io.hdf5_compression == "gzip"
    assert cfg.domain is not None and cfg.domain.min[0] == -1000.0


@pytest.mark.parametrize("path", _invalid_files, ids=[p.stem for p in _invalid_files])
def test_invalid_config_rejected_with_clear_error(path):
    with pytest.raises(ConfigError) as exc:
        load_config(path)
    # hata mesaji dosya kaynagi veya sorunlu alani soylemeli — sessiz yutma yok
    assert str(exc.value).strip(), "hata mesaji bos olamaz"


def test_error_message_names_offending_field():
    with pytest.raises(ConfigError, match="random_seed"):
        load_config(INVALID_DIR / "06_negative_seed.yaml")


def test_unsupported_schema_version_message():
    with pytest.raises(ConfigError, match="schema_version"):
        load_config(INVALID_DIR / "02_unsupported_schema_version.yaml")


def test_missing_file_raises():
    with pytest.raises(ConfigError, match="bulunamadi"):
        load_config("boyle_bir_dosya_yok.yaml")


def test_non_mapping_yaml_raises(tmp_path):
    p = tmp_path / "liste.yaml"
    p.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="anahtar-deger"):
        load_config(p)


def test_broken_yaml_raises(tmp_path):
    p = tmp_path / "bozuk.yaml"
    p.write_text("a: [1, 2\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML"):
        load_config(p)


class TestConfigHash:
    def test_hash_is_stable_across_loads(self):
        h1 = config_hash(load_config(SMOKE))
        h2 = config_hash(load_config(SMOKE))
        assert h1 == h2
        assert len(h1) == 64  # sha256 hex

    def test_hash_changes_with_seed(self):
        cfg = load_config(SMOKE)
        other = RunConfig.model_validate(
            {**cfg.model_dump(mode="json"), "random_seed": cfg.random_seed + 1}
        )
        assert config_hash(cfg) != config_hash(other)

    def test_hash_covers_defaults(self):
        # varsayilanlar cozulmus halde hash'e girer (kanonik form)
        minimal = RunConfig.model_validate(
            {
                "schema_version": 1,
                "run_id": "X_0001",
                "random_seed": 1,
                "numerics": {"precision": "deterministic_fp64"},
            }
        )
        explicit = RunConfig.model_validate(
            {
                "schema_version": 1,
                "run_id": "X_0001",
                "random_seed": 1,
                "numerics": {"precision": "deterministic_fp64", "kernel": None, "cfl": None},
                "io": {
                    "output_layers": ["scalar_budget", "sparse_snapshot", "event_catalog"],
                    "hdf5_compression": "gzip",
                },
                "domain": None,
            }
        )
        assert config_hash(minimal) == config_hash(explicit)


class TestCli:
    def test_cli_valid(self, capsys):
        assert _main([str(SMOKE)]) == 0
        out = capsys.readouterr().out
        assert "GECERLI" in out and "config_hash=" in out

    def test_cli_invalid(self, capsys):
        assert _main([str(INVALID_DIR / "06_negative_seed.yaml")]) == 1
        assert "GECERSIZ" in capsys.readouterr().out

    def test_cli_usage(self, capsys):
        assert _main([]) == 2
