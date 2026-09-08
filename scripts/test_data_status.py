#!/usr/bin/env python3
"""Verifica Stato dati contro il catalogo effettivamente materializzato in dist/."""
from __future__ import annotations

from pathlib import Path

import test_data_status_impl as _impl

_SOURCE_DATA = _impl.ROOT / "data"
_BUILD_DATA = _impl.ROOT / "dist" / "data"
_ORIGINAL_LOAD = _impl.load
_BUILD_SNAPSHOT_FILES = {"site-data.json", "source-registry.json"}


def _build_aware_load(path: Path):
    try:
        relative = path.relative_to(_SOURCE_DATA)
    except ValueError:
        return _ORIGINAL_LOAD(path)
    if relative.as_posix() in _BUILD_SNAPSHOT_FILES:
        candidate = _BUILD_DATA / relative
        if candidate.is_file():
            return _ORIGINAL_LOAD(candidate)
    return _ORIGINAL_LOAD(path)


def main() -> None:
    dist = _impl.ROOT / "dist"
    if dist.exists():
        missing = sorted(
            name for name in _BUILD_SNAPSHOT_FILES
            if not (_BUILD_DATA / name).is_file()
        )
        if missing:
            raise AssertionError(
                "Snapshot dati della build incompleto per il test Stato dati: " + ", ".join(missing)
            )
    _impl.load = _build_aware_load
    try:
        _impl.main()
    finally:
        _impl.load = _ORIGINAL_LOAD


if __name__ == "__main__":
    main()
