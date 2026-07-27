"""P0-QR-03: ayni girdi + tohum 'altin hash' uretir; sapma CI'yi kirar."""

import json
from pathlib import Path

from golden_scenario import (
    SCENARIO_N,
    SCENARIO_NAME,
    SCENARIO_SEED,
    build_canonical_state,
    state_hash,
)

GOLDEN_FILE = Path(__file__).resolve().parent / "golden" / "p0_canonical_v1.json"


def test_state_build_is_reproducible_in_process():
    h1 = state_hash(build_canonical_state())
    h2 = state_hash(build_canonical_state())
    assert h1 == h2


def test_hash_sensitive_to_seed():
    assert state_hash(build_canonical_state(seed=SCENARIO_SEED + 1)) != state_hash(
        build_canonical_state()
    )


def test_golden_hash_matches():
    """Altin dosyadaki hash ile birebir eslesme — kirilirsa determinizm bozulmustur.

    Guncelleme (BILINCLI degisiklik + ADR sonrasi): python scripts/update_golden.py
    """
    golden = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))
    assert golden["scenario"] == SCENARIO_NAME
    assert golden["seed"] == SCENARIO_SEED
    assert golden["n"] == SCENARIO_N
    current = state_hash(build_canonical_state())
    assert current == golden["sha256"], (
        "ALTIN HASH SAPMASI: determinizm kaybi veya bilincli-ama-belgesiz degisiklik. "
        f"beklenen={golden['sha256']} bulunan={current}"
    )
