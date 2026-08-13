#!/usr/bin/env python3
"""Controlli della nuova identità visiva OV nella build di produzione."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OLD_MARK = '<span class="site-brand-mark">O</span>'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    brand_svg = ROOT / "assets" / "brand-mark.svg"
    favicon = ROOT / "favicon.svg"
    brand_css = ROOT / "assets" / "brand.css"
    for path in (brand_svg, favicon, brand_css):
        require(path.exists() and path.stat().st_size > 100, f"Asset brand mancante o vuoto: {path}")

    favicon_text = favicon.read_text(encoding="utf-8")
    require("#0F3654" in favicon_text and "#58A28F" in favicon_text,
            "Favicon OV: palette inattesa")
    require("<circle" in favicon_text and "<path" in favicon_text,
            "Favicon OV: monogramma incompleto")

    bundle = (DIST / "assets" / "app-bundle.js").read_text(encoding="utf-8")
    require('class="ov-mark-svg"' in bundle,
            "Nuovo monogramma OV non incluso nell'app bundle")
    require(OLD_MARK not in bundle,
            "Vecchia O ancora presente nell'app bundle")

    pages = (
        DIST / "index.html",
        DIST / "confronta" / "demografia" / "index.html",
        DIST / "comuni" / "massarosa" / "index.html",
        DIST / "progetto" / "index.html",
    )
    for page in pages:
        text = page.read_text(encoding="utf-8")
        require('class="ov-mark-svg"' in text, f"Logo OV assente in {page}")
        require("assets/brand.css?v=20260807-ov" in text, f"CSS brand assente in {page}")
        require("assets/app-bundle.js?v=20260813-1" in text,
                f"Bundle applicativo non cache-bustato in {page}")
        require("assets/visual-grammar.js?v=20260809-2" in text,
                f"Grammatica visiva non cache-bustata in {page}")
        require("favicon.svg?v=20260807-ov" in text, f"Favicon non cache-bustata in {page}")
        require(OLD_MARK not in text, f"Vecchia O ancora presente in {page}")

    print("Identità OV verificata: logo header, favicon e asset di brand coerenti.")


if __name__ == "__main__":
    main()
