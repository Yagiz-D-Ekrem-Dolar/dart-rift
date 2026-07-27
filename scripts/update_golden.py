"""Altin hash dosyasini yeniden uret (YALNIZCA bilincli, ADR'li degisiklik sonrasi).

Kullanim: python scripts/update_golden.py
"""

from __future__ import annotations

import json
import platform
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
    path = REPO / "tests" / "golden" / "p0_canonical_v1.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    this_platform = f"{platform.system()}/CPython {platform.python_version()}"
    if sha == old.get("sha256"):
        # Hash degismedi: bu platformu dogrulanmislar listesine ekle.
        verified = sorted(set(old.get("verified_on", [])) | {this_platform})
    else:
        # Hash degisti: eski platform dogrulamalari artik gecersizdir.
        verified = [this_platform]

    out = {
        "scenario": SCENARIO_NAME,
        "seed": SCENARIO_SEED,
        "n": SCENARIO_N,
        "sha256": sha,
        "verified_on": verified,
        "note": old.get("note", ""),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"altin hash yazildi: {path}\n  sha256={sha}\n  dogrulanan platformlar={verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
