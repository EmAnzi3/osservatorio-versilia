#!/usr/bin/env python3
"""Materializza Stato dati usando lo snapshot realmente pubblicato in dist/."""
from __future__ import annotations

from pathlib import Path

import build_data_status_impl as _impl
from public_build_snapshot import build_aware_load, validate_public_snapshot

_ORIGINAL_LOAD = _impl.load


def _public_load(path: Path):
    return build_aware_load(_ORIGINAL_LOAD, path)


def main() -> None:
    validate_public_snapshot()
    _impl.load = _public_load
    try:
        _impl.main()
    finally:
        _impl.load = _ORIGINAL_LOAD


if __name__ == "__main__":
    main()
