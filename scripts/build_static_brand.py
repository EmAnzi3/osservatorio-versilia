#!/usr/bin/env python3
"""Build di produzione con identità OV e PWA installabile."""
from __future__ import annotations

import os
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BRAND_ASSET_VERSION = "20260807-ov"
PWA_ASSET_VERSION = "20260807-pwa7"
OLD_MARK = '<span class="site-brand-mark">O</span>'
PWA_FILES = ("service-worker.js", "offline.html", "site.webmanifest")
PWA_ICONS = (
    "icon-180.png",
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-512.png",
)


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


def inject_brand_styles(document: str, relative_root: str) -> str:
    token = "assets/brand.css"
    if token not in document:
        link = f'<link rel="stylesheet" href="{relative_root}{token}?v={BRAND_ASSET_VERSION}">'
        document = document.replace("</head>", f"  {link}\n</head>", 1)
    return document


def inject_brand_markup(document: str) -> str:
    mark = decorative_mark()
    if OLD_MARK in document:
        document = document.replace(OLD_MARK, mark)
    return document


def inject_favicon(document: str, relative_root: str) -> str:
    href = f"{relative_root}favicon.svg?v={BRAND_ASSET_VERSION}"
    tag = f'<link rel="icon" type="image/svg+xml" href="{href}">'
    document = re.sub(r'<link rel="icon"[^>]*>', tag, document, count=1)
    return document


def inject_pwa(document: str, relative_root: str) -> str:
    if "offline.html" in relative_root:
        return document
    css = f'<link rel="stylesheet" href="{relative_root}assets/pwa.css?v={PWA_ASSET_VERSION}">'
    js = f'<script src="{relative_root}assets/pwa.js?v={PWA_ASSET_VERSION}" defer></script>'
    manifest = f'<link rel="manifest" href="{relative_root}site.webmanifest?v={PWA_ASSET_VERSION}">'
    apple_icon = f'<link rel="apple-touch-icon" sizes="180x180" href="{relative_root}pwa/icon-180.png?v={PWA_ASSET_VERSION}">'
    ios_meta = (
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '  <meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
        '  <meta name="apple-mobile-web-app-title" content="Osservatorio Versilia">'
    )
    theme = '<meta name="theme-color" content="#123d59">'
    additions = [css, manifest, apple_icon, ios_meta, theme]
    for item in additions:
        if item.split("?v=")[0] not in document:
            document = document.replace("</head>", f"  {item}\n</head>", 1)
    if "assets/pwa.js" not in document:
        document = document.replace("</body>", f"  {js}\n</body>", 1)
    return document


def patch_html() -> None:
    for html_path in DIST.rglob("*.html"):
        rel = os.path.relpath(ROOT, html_path.parent).replace(os.sep, "/")
        relative_root = "" if rel == "." else rel.rstrip("/") + "/"
        document = html_path.read_text(encoding="utf-8")
        document = inject_brand_styles(document, relative_root)
        document = inject_brand_markup(document)
        document = inject_favicon(document, relative_root)
        if html_path.name != "offline.html":
            document = inject_pwa(document, relative_root)
        html_path.write_text(document, encoding="utf-8")


def copy_assets() -> None:
    for name in ("brand.css", "brand-mark.svg", "pwa.css", "pwa.js"):
        source = ROOT / "assets" / name
        target = DIST / "assets" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    shutil.copy2(ROOT / "favicon.svg", DIST / "favicon.svg")
    for name in PWA_FILES:
        shutil.copy2(ROOT / name, DIST / name)
    pwa_dir = DIST / "pwa"
    pwa_dir.mkdir(parents=True, exist_ok=True)
    for name in PWA_ICONS:
        shutil.copy2(ROOT / "pwa" / name, pwa_dir / name)


def main() -> None:
    runpy.run_path(str(ROOT / "scripts" / "build_static_safe.py"), run_name="__main__")
    copy_assets()
    patch_html()
    print("Build statica completata con identità OV e PWA installabile.")


if __name__ == "__main__":
    main()
