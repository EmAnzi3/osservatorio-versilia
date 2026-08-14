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
APP_BUNDLE_ASSET_VERSION = "20260814-v111"
PWA_ASSET_VERSION = "20260813-pwa8"
PWA_JS_REVISION = "install-ui-off"
MOBILE_ACCORDION_ASSET_VERSION = "20260809-3"
CHART_SURFACE_ASSET_VERSION = "20260808-1"
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
        href = f"{relative_root}{token}?v={BRAND_ASSET_VERSION}"
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{href}">\n</head>',
        )
    return document


def inject_mobile_accordion_styles(document: str, relative_root: str) -> str:
    token = "assets/mobile-accordion-fix.css"
    if token not in document:
        href = f"{relative_root}{token}?v={MOBILE_ACCORDION_ASSET_VERSION}"
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{href}">\n</head>',
        )
    return document


def inject_chart_surface_styles(document: str, relative_root: str) -> str:
    token = "assets/chart-surfaces.css"
    if token not in document:
        href = f"{relative_root}{token}?v={CHART_SURFACE_ASSET_VERSION}"
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


def cache_bust_app_bundle(document: str) -> str:
    return re.sub(
        r'src="([^"?]*assets/app-bundle\.js)(?:\?[^\"]*)?"',
        rf'src="\1?v={APP_BUNDLE_ASSET_VERSION}"',
        document,
    )


def ensure_pwa_files() -> None:
    """Copia esplicitamente gli asset PWA nella build, indipendentemente dal builder base."""
    DIST.mkdir(parents=True, exist_ok=True)
    for name in PWA_FILES:
        source = ROOT / name
        if not source.exists():
            raise RuntimeError(f"File PWA sorgente mancante: {source}")
        shutil.copy2(source, DIST / name)

    target_dir = DIST / "pwa"
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in PWA_ICONS:
        source = ROOT / "pwa" / name
        if not source.exists():
            raise RuntimeError(f"Icona PWA sorgente mancante: {source}")
        shutil.copy2(source, target_dir / name)


def inject_pwa(document: str, relative_root: str) -> str:
    """Aggiunge metadata Apple/Android, CSS e bootstrap PWA a una pagina del sito."""
    document = re.sub(
        r'<meta\s+name="theme-color"\s+content="[^"]*"\s*/?>',
        '<meta name="theme-color" content="#0F3654">',
        document,
        flags=re.IGNORECASE,
    )

    metadata = []
    if 'name="theme-color"' not in document:
        metadata.append('<meta name="theme-color" content="#0F3654">')
    if 'name="mobile-web-app-capable"' not in document:
        metadata.append('<meta name="mobile-web-app-capable" content="yes">')
    if 'name="apple-mobile-web-app-capable"' not in document:
        metadata.append('<meta name="apple-mobile-web-app-capable" content="yes">')
    if 'name="apple-mobile-web-app-status-bar-style"' not in document:
        metadata.append('<meta name="apple-mobile-web-app-status-bar-style" content="default">')
    if 'name="apple-mobile-web-app-title"' not in document:
        metadata.append('<meta name="apple-mobile-web-app-title" content="Osservatorio Versilia">')
    if 'rel="apple-touch-icon"' not in document:
        metadata.append(
            f'<link rel="apple-touch-icon" sizes="180x180" '
            f'href="{relative_root}pwa/icon-180.png?v={PWA_ASSET_VERSION}">'
        )
    if metadata:
        document = document.replace("</head>", "  " + "\n  ".join(metadata) + "\n</head>")

    document = re.sub(
        r'href="([^"?]*site\.webmanifest)(?:\?[^\"]*)?"',
        rf'href="\1?v={PWA_ASSET_VERSION}"',
        document,
    )

    if "assets/pwa.css" not in document:
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{relative_root}assets/pwa.css?v={PWA_ASSET_VERSION}">\n</head>',
        )

    if "assets/pwa.js" not in document:
        document = document.replace(
            "</body>",
            f'  <script src="{relative_root}assets/pwa.js?v={PWA_ASSET_VERSION}&rev={PWA_JS_REVISION}" defer></script>\n</body>',
        )
    return document


def apply_brand_and_pwa() -> None:
    ensure_pwa_files()
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
    site_pages = [path for path in html_files if path.name != "offline.html"]

    for path in site_pages:
        text = path.read_text(encoding="utf-8")
        if OLD_MARK in text:
            text = text.replace(OLD_MARK, mark)
        prefix = os.path.relpath(DIST, path.parent).replace(os.sep, "/")
        relative_root = "" if prefix == "." else f"{prefix}/"
        text = inject_brand_styles(text, relative_root)
        text = inject_mobile_accordion_styles(text, relative_root)
        text = inject_chart_surface_styles(text, relative_root)
        text = cache_bust_favicon(text)
        text = cache_bust_app_bundle(text)
        text = inject_pwa(text, relative_root)
        path.write_text(text, encoding="utf-8")

    missing_mark = [
        path for path in site_pages
        if 'class="ov-mark-svg"' not in path.read_text(encoding="utf-8")
    ]
    if missing_mark:
        raise RuntimeError(f"Nuovo marchio assente in {len(missing_mark)} pagine")

    if OLD_MARK in bundle_path.read_text(encoding="utf-8"):
        raise RuntimeError("Il vecchio marchio O è ancora presente nell'app bundle")

    for relative in (*PWA_FILES, *(f"pwa/{name}" for name in PWA_ICONS)):
        path = DIST / relative
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Asset PWA non incluso nella build: {relative}")


if __name__ == "__main__":
    runpy.run_path(str(ROOT / "scripts" / "build_static_safe.py"), run_name="__main__")
    apply_brand_and_pwa()
    print("Build statica completata con identità OV e PWA installabile.")
