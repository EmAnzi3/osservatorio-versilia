#!/usr/bin/env python3
"""Retrocompatibilità release verificata sul catalogo pubblico materializzato."""
from __future__ import annotations

import test_release_v170_compat_impl as _impl
from public_build_snapshot import public_catalog_path, validate_public_snapshot


def main() -> None:
    validate_public_snapshot()
    public = public_catalog_path()
    _impl.DATA = public
    _impl.DIST_DATA = public
    _impl.main()


if __name__ == "__main__":
    main()
