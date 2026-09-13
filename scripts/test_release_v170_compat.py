#!/usr/bin/env python3
"""Retrocompatibilità release verificata sul catalogo pubblico materializzato."""
from __future__ import annotations

import test_release_v170_compat_impl as _impl
from public_build_snapshot import public_catalog_path, validate_public_snapshot


# INVALSI v1.38: coperture parziali strutturali approvate e documentate.
# Il wrapper estende soltanto l'elenco delle eccezioni del test legacy: l'impl
# continua a verificare copertura dichiarata, Comuni mancanti e formato n.d.
INVALSI_APPROVED_PARTIAL = {
    "invalsiResults": (
        "4/7 · 5/7 · 6/7 secondo grado/prova; n.d. mantenuti senza stime.",
        {"Stazzema"},
    ),
    "invalsiCompetence": (
        "4/7 · 6/7 secondo grado/prova; n.d. mantenuti senza stime.",
        {"Stazzema"},
    ),
    "invalsiImplicitDispersion": (
        "4/7 secondo grado/prova; n.d. mantenuti senza stime.",
        {"Forte dei Marmi", "Seravezza", "Stazzema"},
    ),
    "invalsiAcademicExcellence": (
        "4/7 secondo grado/prova; n.d. mantenuti senza stime.",
        {"Forte dei Marmi", "Seravezza", "Stazzema"},
    ),
}


def main() -> None:
    validate_public_snapshot()
    public = public_catalog_path()
    _impl.DATA = public
    _impl.DIST_DATA = public
    _impl.APPROVED_PARTIAL = {**_impl.APPROVED_PARTIAL, **INVALSI_APPROVED_PARTIAL}
    _impl.main()


if __name__ == "__main__":
    main()
