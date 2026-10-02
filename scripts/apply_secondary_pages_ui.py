#!/usr/bin/env python3
"""Apply the approved secondary-page UI to exactly seven public routes.

This script intentionally runs at the end of build_public_site.py.  It only
injects the dedicated stylesheet into the explicitly approved pages and then
fails the build if the stylesheet is referenced by any other HTML document.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
STYLESHEET = DIST / "assets" / "secondary-pages-ui.css"

TARGETS = (
    DIST / "index.html",
    DIST / "opportunita" / "index.html",
    DIST / "progetto" / "index.html",
    DIST / "segnala" / "index.html",
    DIST / "confronta" / "economia" / "atlante-attivita-economiche" / "index.html",
    DIST / "pnrr" / "index.html",
    DIST / "stato-dati" / "index.html",
)
TOKEN = "secondary-pages-ui.css"


def href_for(path: Path) -> str:
    rel = os.path.relpath(STYLESHEET, path.parent).replace(os.sep, "/")
    return rel


def inject(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Pagina UI approvata non materializzata: {path.relative_to(DIST)}")
    text = path.read_text(encoding="utf-8")
    if TOKEN in text:
        if text.count(TOKEN) != 1:
            raise SystemExit(f"Riferimento UI duplicato: {path.relative_to(DIST)}")
        return
    marker = "</head>"
    if marker not in text:
        raise SystemExit(f"Head non trovato: {path.relative_to(DIST)}")
    link = f'  <link rel="stylesheet" href="{href_for(path)}">\n'
    path.write_text(text.replace(marker, link + marker, 1), encoding="utf-8")


def validate_scope() -> None:
    approved = {path.resolve() for path in TARGETS}
    found: set[Path] = set()
    for path in DIST.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if TOKEN in text:
            found.add(path.resolve())
            if path.resolve() not in approved:
                raise SystemExit(
                    "Secondary-page UI fuori scope: "
                    + str(path.relative_to(DIST))
                )
            if text.count(TOKEN) != 1:
                raise SystemExit(
                    "Secondary-page UI duplicata: "
                    + str(path.relative_to(DIST))
                )
    missing = approved - found
    if missing:
        names = ", ".join(str(path.relative_to(DIST)) for path in sorted(missing))
        raise SystemExit(f"Secondary-page UI mancante: {names}")


def main() -> int:
    if not STYLESHEET.exists():
        raise SystemExit("Foglio assets/secondary-pages-ui.css non trovato nel dist")
    for path in TARGETS:
        inject(path)
    validate_scope()
    print("Secondary-page UI applicata esclusivamente alle 7 route approvate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
