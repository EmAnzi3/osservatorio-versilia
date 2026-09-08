#!/usr/bin/env python3
"""Regression del build statico contro lo snapshot pubblico materializzato."""
from __future__ import annotations

import test_static_impl as _impl
from public_build_snapshot import public_catalog_path, validate_public_snapshot


def main() -> None:
    validate_public_snapshot()
    # L'implementazione storica usa ROOT solo per leggere data/site-data.json;
    # DIST resta il dist canonico inizializzato nel modulo.
    _impl.ROOT = public_catalog_path().parents[1]
    _impl.main()


if __name__ == "__main__":
    main()
