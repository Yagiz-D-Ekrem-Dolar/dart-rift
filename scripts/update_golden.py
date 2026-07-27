"""Altin hash dosyasini yeniden uret (YALNIZCA bilincli, ADR'li degisiklik sonrasi).

Kullanim: python scripts/update_golden.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from golden_scenario import (  # noqa: E402
    SCENARIO_N,
    SCENARIO_NAME,
    SCENARIO_SEED,
    build_canonical_state,
    state_hash,
)


def main() -> int:
    sha = state_hash(build_canonical_state())
    out = {
        "scenario": SCENARIO_NAME,
        "seed": SCENARIO_SEED,
        "n": SCENARIO_N,
        "sha256": sha,
    }
    path = REPO / "tests" / "golden" / "p0_canonical_v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"altin hash yazildi: {path}\n  sha256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
