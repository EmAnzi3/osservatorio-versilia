#!/usr/bin/env python3
"""Verifica pagine e sitemap contro il catalogo pubblico materializzato."""
from __future__ import annotations

import test_indicator_pages_impl as _impl
from public_build_snapshot import public_catalog_path, validate_public_snapshot


def main() -> None:
    validate_public_snapshot()
    # Questo test deve trattare dist/ come radice del rilascio: catalogo,
    # registry e storage esterni sono quelli effettivamente pubblicati.
    public_root = public_catalog_path().parents[1]
    _impl.ROOT = public_root
    _impl.DIST = public_root
    _impl.main()


if __name__ == "__main__":
    main()
