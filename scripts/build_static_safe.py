#!/usr/bin/env python3
"""Safe private build wrapper for the static pre-render migration."""

from __future__ import annotations

import json
import os
import re

import build_static as build

_original_copy_source_tree = build.copy_source_tree
_original_bundle_application = build.bundle_application
_original_prepare_shells = build.prepare_shells

SEARCH_ICON = (
    '<svg class="search-icon" xmlns="http://www.w3.org/2000/svg" '
    'width="16" height="16" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="11" cy="11" r="8"></circle>'
    '<path d="m21 21-4.3-4.3"></path>'
    '</svg>'
)

NUMBER_FORMAT_REPLACEMENTS = {
    "new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', maximumFractionDigits: 0 })",
    "new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 })",
    "new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', minimumFractionDigits: 2, maximumFractionDigits: 2 })",
    "new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })":
        "new Intl.NumberFormat('it-IT', { useGrouping: 'always', style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })",
}


def copy_source_tree_with_local_assets() -> None:
    _original_copy_source_tree()
    data_path = build.DIST / "data" / "site-data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    crest_files = {
        "Camaiore": "camaiore.svg",
        "Forte dei Marmi": "forte-dei-marmi.svg",
        "Massarosa": "massarosa.png",
        "Pietrasanta": "pietrasanta.svg",
        "Seravezza": "seravezza.png",
        "Stazzema": "stazzema.webp",
        "Viareggio": "viareggio.svg",
    }
    data["crests"] = {
        town: f"/crests/{filename}" for town, filename in crest_files.items()
    }
    data_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def bundle_application_with_private_fixes() -> None:
    _original_bundle_application()
    bundle_path = build.DIST / "assets" / "app-bundle.js"
    bundle = bundle_path.read_text(encoding="utf-8")

    old_icon = '<span aria-hidden="true">⌕</span>'
    if old_icon in bundle:
        bundle = bundle.replace(old_icon, SEARCH_ICON)
    elif '<svg class="search-icon"' not in bundle:
        raise RuntimeError("Né l'icona testuale né la lente SVG sono presenti nel bundle")

    for old, new in NUMBER_FORMAT_REPLACEMENTS.items():
        if old in bundle:
            bundle = bundle.replace(old, new)
        elif new not in bundle:
            raise RuntimeError(f"Formatter numerico non trovato: {old}")

    bundle_path.write_text(bundle, encoding="utf-8")


def prepare_shells_with_fonts() -> None:
    _original_prepare_shells()
    for path in build.DIST.rglob("*.html"):
        prefix = build.relative_asset_prefix(path)
        assets = "" if prefix == "." else f"{prefix}/"
        text = path.read_text(encoding="utf-8")
        if "assets/fonts.css" not in text:
            font_link = f'  <link rel="stylesheet" href="{assets}assets/fonts.css">\n'
            text = text.replace("</head>", font_link + "</head>")
            path.write_text(text, encoding="utf-8")


def normalize_prerendered_urls() -> None:
    """Remove the temporary localhost origin serialized by the headless build."""
    localhost = re.compile(r"https?://127\.0\.0\.1:\d+/")
    for path in build.DIST.rglob("*.html"):
        prefix = os.path.relpath(build.DIST, path.parent).replace(os.sep, "/")
        replacement = "" if prefix == "." else f"{prefix}/"
        text = path.read_text(encoding="utf-8")
        text = localhost.sub(replacement, text)
        text = text.replace(
            '<body data-prerendered="true" class=',
            '<body class=',
        )
        path.write_text(text, encoding="utf-8")


build.copy_source_tree = copy_source_tree_with_local_assets
build.bundle_application = bundle_application_with_private_fixes
build.prepare_shells = prepare_shells_with_fonts

if __name__ == "__main__":
    build.main()
    normalize_prerendered_urls()
