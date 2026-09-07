#!/usr/bin/env python3
"""Transactional entry point for the production static build."""
from __future__ import annotations

import runpy
from pathlib import Path

from build_static_brand_impl import *  # noqa: F401,F403
from ephemeral_build_workspace import public_build_workspace

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "scripts" / "build_static_brand_impl.py"


if __name__ == "__main__":
    with public_build_workspace():
        runpy.run_path(str(IMPLEMENTATION), run_name="__main__")
