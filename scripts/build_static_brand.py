#!/usr/bin/env python3
"""Build di produzione con applicazione dell'identità visiva OV."""
from __future__ import annotations

import os
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BRAND_ASSET_VERSION = "20260807-ov"
OLD_MARK = '<span class="site-brand-mark">O</span>'


def decorative_mark() -> str:
    svg = (ROOT / "assets" / "brand-mark.svg").read_text(encoding="utf-8").strip()
    svg = re.sub(r"\s+role=\"img\"\s+aria-labelledby=\"[^\"]+\"", "", svg, count=1)
    svg = re.sub(r"\s*<title[^>]*>.*?</title>\s*", "", svg, flags=re.DOTALL)
    svg = re.sub(r"\s*<desc[^>]*>.*?</desc>\s*", "", svg, flags=re.DOTALL)
    svg = svg.replace(
        "<svg ",
        '<svg class="ov-mark-svg" aria-hidden="true" focusable="false" ',
        1,
    )
    return f'<span class="site-brand-mark" aria-hidden="true">{svg}</span>'


def inject_brand_styles(document: str, relative_assets: str) -> str:
    token = "assets/brand.css"
    if token not in document:
        href = f"{relative_assets}{token}?v={BRAND_ASSET_VERSION}"
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{href}">\n</head>',
        )
    return document


def cache_bust_favicon(document: str) -> str:
    return re.sub(
        r'href="([^"?]*favicon\.svg)(?:\?[^\"]*)?"',
        rf'href="\1?v={BRAND_ASSET_VERSION}"',
        document,
    )


def apply_brand() -> None:
    mark = decorative_mark()

    bundle_path = DIST / "assets" / "app-bundle.js"
    bundle = bundle_path.read_text(encoding="utf-8")
    if OLD_MARK in bundle:
        bundle = bundle.replace(OLD_MARK, mark)
    elif 'class="ov-mark-svg"' not in bundle:
        raise RuntimeError("Marchio precedente non trovato nell'app bundle")
    bundle_path.write_text(bundle, encoding="utf-8")

    html_files = list(DIST.rglob("*.html"))
    if not html_files:
        raise RuntimeError("Nessuna pagina HTML trovata nella build")

    for path in html_files:
        text = path.read_text(encoding="utf-8")
        if OLD_MARK in text:
            text = text.replace(OLD_MARK, mark)
        prefix = os.path.relpath(DIST, path.parent).replace(os.sep, "/")
        relative_assets = "" if prefix == "." else f"{prefix}/"
        text = inject_brand_styles(text, relative_assets)
        text = cache_bust_favicon(text)
        path.write_text(text, encoding="utf-8")

    missing_mark = [
        path for path in html_files
        if 'class="ov-mark-svg"' not in path.read_text(encoding="utf-8")
    ]
    if missing_mark:
        raise RuntimeError(f"Nuovo marchio assente in {len(missing_mark)} pagine")

    if OLD_MARK in bundle_path.read_text(encoding="utf-8"):
        raise RuntimeError("Il vecchio marchio O è ancora presente nell'app bundle")


if __name__ == "__main__":
    runpy.run_path(str(ROOT / "scripts" / "build_static_safe.py"), run_name="__main__")
    apply_brand()
    print("Build statica completata con identità OV.")
