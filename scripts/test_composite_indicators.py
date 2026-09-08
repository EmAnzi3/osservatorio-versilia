#!/usr/bin/env python3
"""Verifica i compositi sul catalogo realmente pubblicato, non sul sorgente ripristinato."""
from __future__ import annotations

import test_composite_indicators_impl as _impl
from public_build_snapshot import public_catalog_path, public_registry_path, validate_public_snapshot


def main() -> None:
    validate_public_snapshot()
    _impl.DATA_PATH = public_catalog_path()
    _impl.REGISTRY_PATH = public_registry_path()
    _impl.main()


if __name__ == "__main__":
    main()
