"""P0-FR-05: enjekte edilmis hatalar MUTLAKA yakalanir."""

import numpy as np
import pytest
from conftest import make_valid_store

from dartrift.invariants import InvariantViolation, check_invariants

DOMAIN = (np.array([-2.0, -2.0, -2.0]), np.array([2.0, 2.0, 2.0]))


def test_clean_store_passes():
    report = check_invariants(make_valid_store(32), step=0, level="science", domain=DOMAIN)
    assert report.ok
    assert "OK" in str(report)


@pytest.mark.parametrize(
    ("field", "value", "rule_part"),
    [
        ("rho", np.nan, "NaN"),
        ("rho", np.inf, "NaN/Inf"),
        ("rho", -1.0, "<= 0"),
        ("rho", 0.0, "<= 0"),
        ("u", np.nan, "NaN"),
        ("mass", 0.0, "<= 0"),
        ("mass", -1.0, "<= 0"),
        ("mass", np.inf, "NaN/Inf"),
        ("D", 1.5, "[0,1]"),
        ("D", -0.1, "[0,1]"),
        ("alpha_por", 0.5, "distansiyon"),
        ("x", np.nan, "NaN"),
        ("vz", np.inf, "NaN"),
    ],
)
def test_injected_error_is_caught(field, value, rule_part):
    store = make_valid_store(16)
    store.as_dict()[field][5] = value
    with pytest.raises(InvariantViolation) as exc:
        check_invariants(store, step=3, level="science", domain=DOMAIN)
    report = exc.value.report
    assert not report.ok
    assert any(
        v.field.startswith(field.split("/")[0]) or field in v.field for v in report.violations
    )
    assert any(rule_part in v.rule for v in report.violations)
    assert any(5 in v.first_indices for v in report.violations)


def test_out_of_domain_caught_in_science_mode():
    store = make_valid_store(8)
    store.x[2] = 100.0  # domain disina cikar
    with pytest.raises(InvariantViolation, match="alan disina"):
        check_invariants(store, level="science", domain=DOMAIN)


def test_domain_skipped_in_performance_mode():
    store = make_valid_store(8)
    store.x[2] = 100.0
    report = check_invariants(store, level="performance", domain=DOMAIN)
    assert report.ok  # performans modu sinir denetimi yapmaz


def test_domain_skipped_when_not_given():
    store = make_valid_store(8)
    store.x[2] = 1.0e9
    assert check_invariants(store, level="science", domain=None).ok


def test_report_mode_without_raise():
    store = make_valid_store(8)
    store.rho[0] = -1.0
    report = check_invariants(store, raise_on_violation=False)
    assert not report.ok
    assert report.violations[0].count == 1


def test_inactive_particles_are_ignored():
    store = make_valid_store(8)
    store.rho[4] = np.nan
    store.active[4] = 0  # pasif parcacik denetlenmez
    assert check_invariants(store, level="science", domain=DOMAIN).ok


def test_multiple_violations_all_reported():
    store = make_valid_store(8)
    store.rho[0] = -5.0
    store.mass[1] = 0.0
    store.D[2] = 2.0
    report = check_invariants(store, raise_on_violation=False)
    fields = {v.field for v in report.violations}
    assert {"rho", "mass", "D"} <= fields


def test_violation_message_is_informative():
    store = make_valid_store(8)
    store.mass[3] = -1.0
    with pytest.raises(InvariantViolation) as exc:
        check_invariants(store, step=42)
    msg = str(exc.value)
    assert "step=42" in msg and "mass" in msg


def test_unknown_level_raises():
    with pytest.raises(ValueError, match="denetim seviyesi"):
        check_invariants(make_valid_store(2), level="hizli")
