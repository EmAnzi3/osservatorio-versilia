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
ATLAS_SCRIPT = DIST / "assets" / "secondary-pages-atlas.js"

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
ATLAS_TOKEN = "secondary-pages-atlas.js"
ATLAS_PAGE = DIST / "confronta" / "economia" / "atlante-attivita-economiche" / "index.html"


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


def inject_atlas_script(path: Path) -> None:
    if not ATLAS_SCRIPT.exists():
        raise SystemExit("Adapter assets/secondary-pages-atlas.js non trovato nel dist")
    text = path.read_text(encoding="utf-8")
    if ATLAS_TOKEN in text:
        if text.count(ATLAS_TOKEN) != 1:
            raise SystemExit("Adapter Atlante duplicato")
        return
    marker = "</body>"
    if marker not in text:
        raise SystemExit("Body Atlante non trovato")
    rel = os.path.relpath(ATLAS_SCRIPT, path.parent).replace(os.sep, "/")
    script = f'  <script src="{rel}" defer></script>\n'
    path.write_text(text.replace(marker, script + marker, 1), encoding="utf-8")


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
    atlas_found: set[Path] = set()
    for path in DIST.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if ATLAS_TOKEN in text:
            atlas_found.add(path.resolve())
            if path.resolve() != ATLAS_PAGE.resolve():
                raise SystemExit(
                    "Adapter Atlante fuori scope: "
                    + str(path.relative_to(DIST))
                )
            if text.count(ATLAS_TOKEN) != 1:
                raise SystemExit("Adapter Atlante duplicato")
    if atlas_found != {ATLAS_PAGE.resolve()}:
        raise SystemExit("Adapter Atlante non presente esclusivamente sulla route approvata")

    missing = approved - found
    if missing:
        names = ", ".join(str(path.relative_to(DIST)) for path in sorted(missing))
        raise SystemExit(f"Secondary-page UI mancante: {names}")


def main() -> int:
    if not STYLESHEET.exists():
        raise SystemExit("Foglio assets/secondary-pages-ui.css non trovato nel dist")
    for path in TARGETS:
        inject(path)
    inject_atlas_script(ATLAS_PAGE)
    validate_scope()
    print("Secondary-page UI applicata esclusivamente alle 7 route approvate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
