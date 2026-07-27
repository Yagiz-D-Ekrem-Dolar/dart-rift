"""P0-FR-06 + P0-DR-02: manifest tamligi ve loglama."""

import json
from pathlib import Path

import pytest

from dartrift import logging_cfg as L
from dartrift.config import load_config

SMOKE = Path(__file__).resolve().parents[1] / "configs" / "p0_smoke.yaml"


@pytest.fixture(scope="module")
def cfg():
    return load_config(SMOKE)


@pytest.fixture()
def manifest(cfg):
    return L.build_manifest(cfg, status="accepted", wall_time=1.5,
                            checkpoint_sha256="a" * 64, observables_sha256="b" * 64)


class TestManifestCompleteness:
    def test_manifest_is_complete(self, manifest):
        assert L.validate_manifest(manifest) == []

    @pytest.mark.parametrize("dotted", L.REQUIRED_MANIFEST_FIELDS)
    def test_each_required_field_detected_when_missing(self, manifest, dotted):
        # Ek A'daki HER alan icin: alani sil -> dogrulama yakalamali
        broken = json.loads(json.dumps(manifest))
        parts = dotted.split(".")
        cur = broken
        for p in parts[:-1]:
            cur = cur[p]
        del cur[parts[-1]]
        assert dotted in L.validate_manifest(broken)

    def test_config_identity_fields(self, manifest, cfg):
        assert manifest["run_id"] == cfg.run_id
        assert manifest["random_seed"] == cfg.random_seed
        assert manifest["numerics"]["precision"] == "deterministic_fp64"
        assert len(manifest["config_hash"]) == 64

    def test_invalid_status_rejected_at_build(self, cfg):
        with pytest.raises(ValueError, match="status"):
            L.build_manifest(cfg, status="belki_oldu")

    def test_invalid_status_flagged_at_validate(self, manifest):
        manifest["status"] = "harika"
        assert any("status" in m for m in L.validate_manifest(manifest))

    def test_timestamp_is_utc_iso(self, manifest):
        assert "T" in manifest["timestamp_utc"]
        assert manifest["timestamp_utc"].endswith("+00:00")


class TestManifestIo:
    def test_write_and_read_roundtrip(self, manifest, tmp_path):
        path = L.write_manifest(manifest, tmp_path / "run" / "manifest.yaml")
        assert path.is_file()
        back = L.read_manifest(path)
        assert back == manifest

    def test_write_refuses_incomplete_manifest(self, manifest, tmp_path):
        del manifest["outputs"]["checkpoint_sha256"]
        with pytest.raises(ValueError, match="eksik"):
            L.write_manifest(manifest, tmp_path / "manifest.yaml")


class TestReproducibility:
    """Kirmizi-takim §12: "Manifest, kosuyu sifirdan yeniden uretmeye yetiyor mu?"

    Yalnizca config_hash tasimak yetmez: hash "ayni mi?" sorusunu yanitlar,
    "neydi?" sorusunu yanitlamaz. Bu testler config'in manifestten tek basina
    geri kurulabildigini kanitlar.
    """

    def test_config_recovered_from_manifest_alone(self, manifest, cfg, tmp_path):
        path = L.write_manifest(manifest, tmp_path / "manifest.yaml")
        # Orijinal YAML'a hic dokunmadan, sadece manifestten:
        recovered = L.config_from_manifest(L.read_manifest(path))
        assert recovered == cfg

    def test_recovered_config_has_same_hash(self, manifest, cfg):
        from dartrift.config import config_hash

        assert config_hash(L.config_from_manifest(manifest)) == config_hash(cfg)

    def test_recovered_config_drives_same_precision(self, manifest, cfg):
        assert L.config_from_manifest(manifest).store_precision == cfg.store_precision

    def test_manifest_without_config_rejected(self, manifest):
        del manifest["config"]
        with pytest.raises(ValueError, match="yeniden uretilemez"):
            L.config_from_manifest(manifest)

    def test_tampered_manifest_detected(self, manifest):
        # Gomulu config degistirilip hash eski birakilirsa yakalanmali
        manifest["config"]["random_seed"] = 999_999
        with pytest.raises(ValueError, match="tutarsiz"):
            L.config_from_manifest(manifest)


class TestGitSha:
    def test_returns_string(self):
        assert isinstance(L.get_git_sha(strict=False), str)

    def test_env_fallback(self, monkeypatch):
        def boom(*a, **k):
            raise OSError("git yok")

        monkeypatch.setattr(L.subprocess, "run", boom)
        monkeypatch.setenv("DARTRIFT_GIT_SHA", "deadbeef")
        assert L.get_git_sha() == "deadbeef"

    def test_strict_raises_without_source(self, monkeypatch):
        def boom(*a, **k):
            raise OSError("git yok")

        monkeypatch.setattr(L.subprocess, "run", boom)
        monkeypatch.delenv("DARTRIFT_GIT_SHA", raising=False)
        with pytest.raises(RuntimeError, match="bilim modunda"):
            L.get_git_sha(strict=True)


class TestHardwareAndLogging:
    def test_detect_hardware_shape(self):
        hw = L.detect_hardware()
        assert set(hw) >= {"gpu", "driver"}
        assert isinstance(hw["gpu"], str) and hw["gpu"]

    def test_jsonl_logging(self, tmp_path):
        logger = L.setup_logging(tmp_path, console=False)
        logger.info("merhaba %s", "faz0")
        logger.handlers[0].flush()
        lines = (tmp_path / "run.log.jsonl").read_text(encoding="utf-8").strip().splitlines()
        rec = json.loads(lines[-1])
        assert rec["msg"] == "merhaba faz0"
        assert rec["level"] == "INFO"

    def test_stopwatch(self):
        with L.Stopwatch() as sw:
            pass
        assert sw.elapsed >= 0.0
