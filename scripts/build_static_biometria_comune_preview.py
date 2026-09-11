#!/usr/bin/env python3
"""Build di revisione v1.35.0 sulla stessa pipeline e shell del main."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "build_static_brand.py"
NEEDLE = '        _ORIGINAL_RUN_PATH(str(ECONOMIA_PRODOTTA_MATERIALIZER), run_name="__main__")'
INSERT = NEEDLE + '\n        _ORIGINAL_RUN_PATH(str(ROOT / "scripts" / "materialize_biometria_comune_release.py"), run_name="__main__")'


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    if original.count(NEEDLE) != 1:
        raise RuntimeError(f"Hook Economia prodotta non univoco: {original.count(NEEDLE)} occorrenze")
    TARGET.write_text(original.replace(NEEDLE, INSERT, 1), encoding="utf-8")
    try:
        runpy.run_path(str(TARGET), run_name="__main__")
    finally:
        TARGET.write_text(original, encoding="utf-8")
    print("Artifact Biometria costruito dalla pipeline canonica di main.")


if __name__ == "__main__":
    main()
