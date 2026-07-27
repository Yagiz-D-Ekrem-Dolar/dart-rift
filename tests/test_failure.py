"""DR-RIFT-P0 §6.2: "ihlal -> 'numerical_failure' etiketiyle durdur, config dondur".

Ilk uygulamada invariant ihlali yalnizca istisna firlatiyordu; sartnamenin
istedigi dondurma adimi yoktu ve MANIFEST_STATUSES icindeki
'numerical_failure' degeri hicbir yerde uretilmiyordu.
"""

from __future__ import annotations

import numpy as np
import pytest
import yaml
from conftest import make_valid_store

from dartrift.config import RunConfig, config_hash
from dartrift.failure import freeze_failed_run
from dartrift.invariants import check_invariants
from dartrift.logging_cfg import config_from_manifest, read_manifest, validate_manifest


@pytest.fixture()
def cfg() -> RunConfig:
    return RunConfig.model_validate(
        {
            "schema_version": 1,
            "run_id": "F_0001",
            "random_seed": 424242,
            "numerics": {"precision": "deterministic_fp64"},
        }
    )


@pytest.fixture()
def bad_report():
    store = make_valid_store(16)
    store.rho[4] = np.nan
    store.mass[9] = -1.0
    return check_invariants(store, step=137, raise_on_violation=False)


class TestFreeze:
    def test_status_is_numerical_failure(self, cfg, bad_report, tmp_path):
        frozen = freeze_failed_run(cfg, bad_report, tmp_path / "run")
        manifest = read_manifest(frozen.manifest)
        assert manifest["status"] == "numerical_failure"

    def test_failure_manifest_is_still_complete(self, cfg, bad_report, tmp_path):
        """Basarisiz kosu da Ek A'yi tam doldurur; eksik manifest kabul edilmez."""
        frozen = freeze_failed_run(cfg, bad_report, tmp_path / "run")
        assert validate_manifest(read_manifest(frozen.manifest)) == []

    def test_config_is_frozen_to_disk(self, cfg, bad_report, tmp_path):
        frozen = freeze_failed_run(cfg, bad_report, tmp_path / "run")
        assert frozen.config.is_file()
        saved = yaml.safe_load(frozen.config.read_text(encoding="utf-8"))
        assert RunConfig.model_validate(saved) == cfg

    def test_frozen_run_is_reproducible(self, cfg, bad_report, tmp_path):
        """Basarisizlik da yeniden uretilebilir olmali (hata ayiklamanin sarti)."""
        frozen = freeze_failed_run(cfg, bad_report, tmp_path / "run")
        recovered = config_from_manifest(read_manifest(frozen.manifest))
        assert config_hash(recovered) == config_hash(cfg)
        assert recovered.random_seed == 424242

    def test_violation_report_names_fields_and_indices(self, cfg, bad_report, tmp_path):
        frozen = freeze_failed_run(cfg, bad_report, tmp_path / "run")
        text = frozen.report.read_text(encoding="utf-8")
        assert "step: 137" in text
        assert "numerical_failure" in text
        assert "alan=rho" in text and "alan=mass" in text
        assert "[4]" in text and "[9]" in text  # ihlal eden parcacik indeksleri

    def test_clean_report_cannot_be_frozen_as_failure(self, cfg, tmp_path):
        clean = check_invariants(make_valid_store(4), raise_on_violation=False)
        with pytest.raises(ValueError, match="temiz rapor"):
            freeze_failed_run(cfg, clean, tmp_path / "run")

    def test_physical_reject_status_supported(self, cfg, bad_report, tmp_path):
        frozen = freeze_failed_run(cfg, bad_report, tmp_path / "run", status="physical_reject")
        assert read_manifest(frozen.manifest)["status"] == "physical_reject"

    def test_invalid_status_rejected(self, cfg, bad_report, tmp_path):
        with pytest.raises(ValueError, match="status"):
            freeze_failed_run(cfg, bad_report, tmp_path / "run", status="olmadi_gitti")

    def test_creates_missing_directory(self, cfg, bad_report, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        frozen = freeze_failed_run(cfg, bad_report, deep)
        assert frozen.manifest.is_file() and frozen.config.is_file()
