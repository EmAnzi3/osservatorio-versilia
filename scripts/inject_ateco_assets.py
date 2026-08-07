#!/usr/bin/env python3
"""Inietta gli asset del modulo ATECO nelle pagine HTML già costruite."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def main() -> int:
    if not DIST.exists():
        raise SystemExit("dist/ non esiste: eseguire prima build_static_safe.py")
    changed = 0
    for path in DIST.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        prefix = os.path.relpath(DIST, path.parent).replace(os.sep, "/")
        assets = "" if prefix == "." else f"{prefix}/"
        css = f'{assets}assets/ateco-addon.css'
        js = f'{assets}assets/ateco-addon.js'
        if "ateco-addon.css" not in text:
            text = text.replace("</head>", f'  <link rel="stylesheet" href="{css}">\n</head>')
        if "ateco-addon.js" not in text:
            text = text.replace("</body>", f'  <script src="{js}" defer></script>\n</body>')
        path.write_text(text, encoding="utf-8")
        changed += 1
    print(f"Modulo ATECO iniettato in {changed} pagine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
