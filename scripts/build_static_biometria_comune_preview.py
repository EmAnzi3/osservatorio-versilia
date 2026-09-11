#!/usr/bin/env python3
"""Build di revisione v1.35.0 sulla stessa pipeline e shell del main."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "build_static_brand.py"
REQUIRED_HOOK = '_ORIGINAL_RUN_PATH(str(BIOMETRIA_MATERIALIZER), run_name="__main__")'


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    if REQUIRED_HOOK not in source:
        raise RuntimeError("La pipeline di produzione non materializza Biometria v1.35.0.")
    runpy.run_path(str(TARGET), run_name="__main__")
    print("Artifact Biometria costruito dalla pipeline canonica di produzione.")


if __name__ == "__main__":
    main()
