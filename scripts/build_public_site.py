#!/usr/bin/env python3
"""Build and validate the complete public Pages artifact."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
STEPS = (
    "build_static_brand.py",
    "build_data_status.py",
    "inject_data_status_runtime.py",
    "build_pnrr_toscana_deep_dive.py",
    "inject_pnrr_town_experience.py",
    "copy_percorsi_dist.py",
)


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not args.validate_only:
        for step in STEPS:
            run([sys.executable, str(ROOT / "scripts" / step)])
        run(["node", "--check", str(DIST / "assets" / "app-bundle.js")])
    run([sys.executable, str(ROOT / "scripts" / "validate_public_site.py"), "--dist", str(DIST)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
